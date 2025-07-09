from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime
from models.incidentes import *
from services.incidentes_service import dados_incidentes, atualizar_resumo, carregar_dados_do_disco, contar_entidades_por_dominio
from utils.newrelic_advanced_collector import get_all_entities, get_entity_advanced_data
import aiohttp
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/incidentes",
    response_model=IncidentesResponseModel,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Lista todos os incidentes com dados avançados reais",
    description="Lista todos os incidentes com dados avançados reais de cada entidade relacionada. Sempre retorna dados reais, nunca simulados.",
    status_code=status.HTTP_200_OK
)
async def listar_incidentes():
    await carregar_dados_do_disco()
    atualizar_resumo()
    try:
        async with aiohttp.ClientSession() as session:
            entidades = await get_all_entities(session)
            entidades_map = {e.get("guid"): e for e in entidades}
            incidentes_avancados = []
            for incidente in dados_incidentes["incidentes"]:
                entidades_rel = []
                for ent_assoc in dados_incidentes.get("entidades_associadas", {}).get(incidente["id"], []):
                    guid = ent_assoc.get("guid")
                    entidade = entidades_map.get(guid)
                    if entidade:
                        dados_avancados = await get_entity_advanced_data(entidade, "7d", session=session)
                        entidades_rel.append(EntidadeModel(guid=guid, entidade=entidade, dados_avancados=dados_avancados))
                incidente_c = IncidenteModel(**{**incidente, "entidades_dados_avancados": entidades_rel})
                incidentes_avancados.append(incidente_c)
            return IncidentesResponseModel(
                incidentes=incidentes_avancados,
                alertas=dados_incidentes["alertas"],
                timestamp=datetime.now().isoformat(),
                resumo=dados_incidentes["resumo"]
            )
    except Exception as e:
        logger.error(f"Erro ao coletar dados avançados para incidentes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao coletar dados avançados para incidentes: {e}")
