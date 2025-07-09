from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List, Dict, Any
import aiohttp
from models.incidentes import AnaliseEntidadeModel
from models.openapi_examples import AnaliseIncidenteResponseModelOpenAPI
from utils.newrelic_advanced_collector import get_all_entities, get_entity_advanced_data
from services.incidentes_service import dados_incidentes

router = APIRouter()

@router.get(
    "/analise/{incidente_id}",
    response_model=AnaliseIncidenteResponseModelOpenAPI,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Análise profunda de um incidente com dados avançados reais",
    description="Fornece uma análise profunda de um incidente específico com dados avançados reais de cada entidade relacionada. Sempre retorna dados reais, nunca simulados."
)
async def obter_analise_incidente(incidente_id: str):
    try:
        async with aiohttp.ClientSession() as session:
            entidades = await get_all_entities(session)
            entidades_map = {e.get("guid"): e for e in entidades}
            entidades_associadas = dados_incidentes.get("entidades_associadas", {}).get(incidente_id, [])
            metricas_entidades = []
            for entidade in entidades_associadas:
                guid = entidade.get("guid")
                entidade_real = entidades_map.get(guid)
                if entidade_real:
                    dados_avancados = await get_entity_advanced_data(entidade_real, "7d", session=session)
                    metricas_entidades.append(AnaliseEntidadeModel(guid=guid, entidade=entidade_real, dados_avancados=dados_avancados))
            return AnaliseIncidenteResponseModelOpenAPI(
                incidente_id=incidente_id,
                analise=metricas_entidades,
                timestamp=datetime.now().isoformat()
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao coletar análise avançada do incidente: {e}")
