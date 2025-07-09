from models.incidentes import (
    EntidadesListResponseModel, AnaliseIncidenteResponseModel, StatusCacheResponseModel, CorrelacionarResponseModel, ChatResponseModel, CausaRaizResponseModel
)

class EntidadesListResponseModelOpenAPI(EntidadesListResponseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "entidades": [
                        {
                            "guid": "MTYyODQwM3xBUE0=",
                            "entidade": {"name": "API de Pagamentos", "domain": "APM", "guid": "MTYyODQwM3xBUE0="},
                            "dados_avancados": {"logs": [], "errors": [], "traces": [], "queries": [], "distributed_trace": [], "metricas": {}}
                        }
                    ],
                    "timestamp": "2025-07-08T12:00:00.000Z",
                    "total": 1
                }
            ]
        }
    }

class AnaliseIncidenteResponseModelOpenAPI(AnaliseIncidenteResponseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "incidente_id": "inc-1",
                    "analise": [
                        {
                            "guid": "MTYyODQwM3xBUE0=",
                            "entidade": {"name": "API de Pagamentos", "domain": "APM", "guid": "MTYyODQwM3xBUE0="},
                            "dados_avancados": {"logs": [], "errors": [], "traces": [], "queries": [], "distributed_trace": [], "metricas": {}}
                        }
                    ],
                    "timestamp": "2025-07-08T12:00:00.000Z"
                }
            ]
        }
    }

class StatusCacheResponseModelOpenAPI(StatusCacheResponseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "Completo",
                    "timestamp": "2025-07-08T12:00:00.000Z",
                    "total_entidades_consolidadas": 3,
                    "total_alertas": 2,
                    "total_incidentes": 1,
                    "entidades_por_dominio": {"APM": 2, "BROWSER": 1},
                    "chaves_disponiveis": ["incidentes", "alertas", "timestamp", "resumo", "entidades_associadas"],
                    "ultima_atualizacao_cache": "2025-07-08T11:59:00.000Z"
                }
            ]
        }
    }

class CorrelacionarResponseModelOpenAPI(CorrelacionarResponseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "mensagem": "Correlação de incidentes concluída",
                    "total_incidentes": 3,
                    "total_entidades_associadas": 3,
                    "timestamp": "2025-07-08T12:00:00.000Z"
                }
            ]
        }
    }

class ChatResponseModelOpenAPI(ChatResponseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "resposta": "A entidade 'API de Pagamentos' apresentou o maior número de erros nas últimas 24h.",
                    "mensagem_recebida": "Quais entidades estão com maior número de erros?",
                    "timestamp": "2025-07-08T12:00:00.000Z"
                }
            ]
        }
    }

class CausaRaizResponseModelOpenAPI(CausaRaizResponseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "incidente_id": "inc-1",
                    "causa_raiz": [
                        {
                            "guid": "MTYyODQwM3xBUE0=",
                            "entidade": {"name": "API de Pagamentos", "domain": "APM", "guid": "MTYyODQwM3xBUE0="},
                            "dados_avancados": {"logs": [], "errors": [], "traces": [], "queries": [], "distributed_trace": [], "metricas": {}}
                        }
                    ],
                    "timestamp": "2025-07-08T12:00:00.000Z"
                }
            ]
        }
    }
