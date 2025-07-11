from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel
from core_inteligente.agno_agent import agno_agent
class GerarRelatorioRequest(BaseModel):
    tipo: str = "tecnico"
    filtro: Optional[Dict[str, Any]] = None

class CorrigirEntidadeRequest(BaseModel):
    entidade: str
    acao: str = "corrigir"

class DispararAlertaRequest(BaseModel):
    mensagem: str
    destino: str = "equipe"

class AnalisarIntencaoRequest(BaseModel):
    texto: str

class ExecutarPlaybookRequest(BaseModel):
    nome: str
    contexto: Optional[Dict[str, Any]] = None

class ExecutarAcaoRequest(BaseModel):
    acao: Dict[str, Any]

class CorrelacionarEventosRequest(BaseModel):
    eventos: list

class RegistrarFeedbackRequest(BaseModel):
    feedback: Dict[str, Any]

class ColetarNewRelicRequest(BaseModel):
    entidade: Optional[str] = None
    periodo: str = "7d"
    tipo: str = "metricas"

router = APIRouter()

def get_tool(name: str):
    for tool in agno_agent.tools:
        if tool.name == name:
            return tool
    raise HTTPException(status_code=404, detail=f"Ferramenta '{name}' não encontrada no agente IA.")

@router.post("/relatorio", summary="Gera relatório técnico ou executivo via IA")
async def gerar_relatorio(request: GerarRelatorioRequest):
    try:
        tool = get_tool("gerar_relatorio")
        resultado = tool.run(tipo=request.tipo, filtro=request.filtro)
        return {"relatorio": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/corrigir", summary="Executa automação de correção para uma entidade")
async def corrigir_entidade(request: CorrigirEntidadeRequest):
    try:
        tool = get_tool("corrigir_entidade")
        resultado = tool.run(entidade=request.entidade, acao=request.acao)
        return {"resultado": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerta", summary="Dispara alerta customizado para equipe ou sistema externo")
async def disparar_alerta(request: DispararAlertaRequest):
    try:
        tool = get_tool("disparar_alerta")
        resultado = tool.run(mensagem=request.mensagem, destino=request.destino)
        return {"resultado": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historico", summary="Consulta histórico de interações ou decisões da IA")
async def consultar_historico(session_id: Optional[str] = None, limite: int = 10):
    try:
        tool = get_tool("consultar_historico")
        resultado = tool.run(session_id=session_id, limite=limite)
        return {"historico": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intencao", summary="Analisa a intenção da mensagem do usuário")
async def analisar_intencao(request: AnalisarIntencaoRequest):
    try:
        tool = get_tool("analisar_intencao")
        resultado = tool.run(texto=request.texto)
        return {"intencao": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/playbook", summary="Executa um playbook dinâmico por nome")
async def executar_playbook(request: ExecutarPlaybookRequest):
    try:
        tool = get_tool("executar_playbook")
        resultado = tool.run(nome=request.nome, contexto=request.contexto or {})
        return {"resultado": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/acao", summary="Executa uma ação plugável (notificação, webhook, CI/CD)")
async def executar_acao(request: ExecutarAcaoRequest):
    try:
        tool = get_tool("executar_acao")
        resultado = tool.run(acao=request.acao)
        return {"resultado": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/correlacionar", summary="Detecta padrões e picos em eventos")
async def correlacionar_eventos(request: CorrelacionarEventosRequest):
    try:
        tool = get_tool("correlacionar_eventos")
        resultado = tool.run(eventos=request.eventos)
        return {"correlacao": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contexto", summary="Consulta o contexto/memória de uma sessão")
async def consultar_contexto(session_id: str):
    try:
        tool = get_tool("consultar_contexto")
        resultado = tool.run(session_id=session_id)
        return {"contexto": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback", summary="Registra feedback do usuário para aprendizado contínuo")
async def registrar_feedback(request: RegistrarFeedbackRequest):
    try:
        tool = get_tool("registrar_feedback")
        resultado = tool.run(feedback=request.feedback)
        return {"resultado": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/coletar_newrelic", summary="Coleta dados do New Relic via Agno, usando cache para evitar custos")
async def coletar_newrelic(request: ColetarNewRelicRequest):
    tool = get_tool("coletar_dados_newrelic")
    # Suporte tanto para métodos async quanto sync
    run_method = getattr(tool, "run", None)
    if run_method is None:
        raise HTTPException(status_code=500, detail="Ferramenta não possui método run.")
    if hasattr(run_method, "__code__") and run_method.__code__.co_flags & 0x80:
        resultado = await tool.run(entidade=request.entidade, periodo=request.periodo, tipo=request.tipo)
    else:
        resultado = tool.run(entidade=request.entidade, periodo=request.periodo, tipo=request.tipo)
    return resultado
