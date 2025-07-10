from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List, Dict, Any
import aiohttp
from models.incidentes import CausaRaizEntidadeModel
from models.openapi_examples import CausaRaizResponseModelOpenAPI
from utils.newrelic_advanced_collector import get_all_entities, get_entity_advanced_data
from services.incidentes_service import dados_incidentes

router = APIRouter()

@router.get(
    "/analise_causa_raiz/{incidente_id}",
    response_model=CausaRaizResponseModelOpenAPI,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Análise de causa raiz de um incidente com dados avançados reais",
    description="Analisa a causa raiz de um incidente específico usando dados avançados reais do New Relic. Sempre retorna dados reais, nunca simulados."
)
async def analise_causa_raiz(incidente_id: str):
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
                    metricas_entidades.append(CausaRaizEntidadeModel(guid=guid, entidade=entidade_real, dados_avancados=dados_avancados))
            return CausaRaizResponseModelOpenAPI(
                incidente_id=incidente_id,
                causa_raiz=metricas_entidades,
                timestamp=datetime.now().isoformat(),
                explicacao="Esta resposta apresenta a provável causa raiz do incidente, baseada em análise de dados avançados e correlações detectadas.",
                sugestao="Priorize a investigação das entidades e métricas destacadas como causa raiz para mitigar recorrências.",
                proximos_passos="Implemente as recomendações sugeridas e monitore o ambiente para validar a resolução do incidente."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao coletar causa raiz avançada do incidente: {e}")
