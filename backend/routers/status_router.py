from fastapi import APIRouter, HTTPException
from datetime import datetime
from models.openapi_examples import StatusCacheResponseModelOpenAPI
from services.incidentes_service import dados_incidentes, carregar_entidades_newrelic, contar_entidades_por_dominio

router = APIRouter()

@router.get(
    "/status-cache",
    response_model=StatusCacheResponseModelOpenAPI,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Status do cache de incidentes e entidades",
    description="Retorna informações sobre o status do cache de incidentes e entidades, incluindo totais, domínios e chaves disponíveis."
)
async def status_cache():
    try:
        entidades = await carregar_entidades_newrelic()
        entidades_por_dominio = contar_entidades_por_dominio(entidades)
        return StatusCacheResponseModelOpenAPI(
            status="Completo" if entidades and dados_incidentes["incidentes"] else "Incompleto",
            timestamp=datetime.now().isoformat(),
            total_entidades_consolidadas=len(entidades),
            total_alertas=len(dados_incidentes["alertas"]),
            total_incidentes=len(dados_incidentes["incidentes"]),
            entidades_por_dominio=entidades_por_dominio,
            chaves_disponiveis=list(dados_incidentes.keys()),
            ultima_atualizacao_cache=dados_incidentes.get("timestamp", "Nunca"),
            explicacao="Este endpoint retorna o status atual do cache, incluindo totais e chaves disponíveis para análise.",
            sugestao="Utilize essas informações para monitorar a saúde do backend e identificar possíveis necessidades de atualização de dados.",
            proximos_passos="Se notar dados desatualizados, acione a atualização manual do cache ou verifique logs para possíveis falhas."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter status do cache: {e}")
