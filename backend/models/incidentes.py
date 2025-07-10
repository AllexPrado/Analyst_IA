from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Evita erro de ordem de definição de classe
    from .incidentes import EntidadesListResponseModel, AnaliseIncidenteResponseModel, StatusCacheResponseModel, CorrelacionarResponseModel, ChatResponseModel, CausaRaizResponseModel


from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DadosAvancadosModel(BaseModel):
    logs: Optional[Any] = None
    errors: Optional[Any] = None
    traces: Optional[Any] = None
    queries: Optional[Any] = None
    distributed_trace: Optional[Any] = None
    metricas: Optional[Any] = None

class EntidadeModel(BaseModel):
    guid: str
    entidade: Dict[str, Any]
    dados_avancados: DadosAvancadosModel

class IncidenteModel(BaseModel):
    id: str
    title: Optional[str]
    description: Optional[str]
    severity: Optional[str]
    opened_at: Optional[str]
    state: Optional[str]
    impacted_service: Optional[str]
    entidades_dados_avancados: List[EntidadeModel] = []

class IncidentesResponseModel(BaseModel):
    incidentes: List[IncidenteModel]
    alertas: List[Any]
    timestamp: str
    resumo: Dict[str, Any]
    explicacao: str = ""
    sugestao: str = ""
    proximos_passos: str = ""

class EntidadeResponseModel(BaseModel):
    guid: str
    entidade: Dict[str, Any]
    dados_avancados: DadosAvancadosModel

class EntidadesListResponseModel(BaseModel):
    entidades: List[EntidadeResponseModel]
    timestamp: str
    total: int
    explicacao: str = ""
    sugestao: str = ""
    proximos_passos: str = ""

class AnaliseEntidadeModel(BaseModel):
    guid: str
    entidade: Dict[str, Any]
    dados_avancados: DadosAvancadosModel

class AnaliseIncidenteResponseModel(BaseModel):
    incidente_id: str
    analise: List[AnaliseEntidadeModel]
    timestamp: str

class StatusCacheResponseModel(BaseModel):
    status: str
    timestamp: str
    total_entidades_consolidadas: int
    total_alertas: int
    total_incidentes: int
    entidades_por_dominio: Dict[str, int]
    chaves_disponiveis: List[str]
    ultima_atualizacao_cache: str

class CorrelacionarResponseModel(BaseModel):
    mensagem: str
    total_incidentes: int
    total_entidades_associadas: int
    timestamp: str
    explicacao: str = ""
    sugestao: str = ""
    proximos_passos: str = ""

class ChatRequestModel(BaseModel):
    mensagem: str = Field(..., description="Mensagem enviada pelo usuário")

class ChatResponseModel(BaseModel):
    resposta: str
    mensagem_recebida: str
    timestamp: str
    explicacao: str = ""
    sugestao: str = ""
    proximos_passos: str = ""

class CausaRaizEntidadeModel(BaseModel):
    guid: str
    entidade: Dict[str, Any]
    dados_avancados: DadosAvancadosModel

class CausaRaizResponseModel(BaseModel):
    incidente_id: str
    causa_raiz: List[CausaRaizEntidadeModel]
    timestamp: str
