from fastapi import APIRouter, HTTPException
from datetime import datetime
from models.incidentes import EntidadeResponseModel, EntidadesListResponseModel
from utils.newrelic_advanced_collector import get_all_entities, get_entity_advanced_data
import aiohttp
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/entidades",
    response_model=EntidadesListResponseModel,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Lista todas as entidades do New Relic com dados avançados reais",
    description="Lista todas as entidades do New Relic com dados avançados válidos (com pelo menos uma métrica, log, trace ou query preenchida). Sempre retorna dados reais, nunca simulados."
)
async def listar_entidades():
    try:
        async with aiohttp.ClientSession() as session:
            entidades = await get_all_entities(session)
            entidades_avancadas = []
            for entidade in entidades:
                dados_avancados = await get_entity_advanced_data(entidade, "7d", session=session)
                if any([
                    dados_avancados.get("logs"),
                    dados_avancados.get("errors"),
                    dados_avancados.get("traces"),
                    dados_avancados.get("queries"),
                    dados_avancados.get("distributed_trace"),
                    dados_avancados.get("metricas"),
                ]):
                    entidades_avancadas.append(EntidadeResponseModel(guid=entidade.get("guid"), entidade=entidade, dados_avancados=dados_avancados))
            return EntidadesListResponseModel(
                entidades=entidades_avancadas,
                timestamp=datetime.now().isoformat(),
                total=len(entidades_avancadas)
            )
    except Exception as e:
        logger.error(f"Erro ao coletar entidades avançadas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao coletar entidades avançadas: {e}")
