
# Classe base Tool (stub local para evitar erro de importação)
class Tool:
    name: str = "tool"
    description: str = "Base Tool"
    def run(self, *args, **kwargs):
        raise NotImplementedError("Tool.run precisa ser implementado na subclasse.")

import asyncio
from utils.newrelic_advanced_collector import get_all_entities, execute_nrql_query

class ColetarDadosNewRelicTool(Tool):
    name = "coletar_dados_newrelic"
    description = "Coleta dados do New Relic (usando cache quando possível para evitar custos)."
    def run(self, entidade: str = None, periodo: str = "7d", tipo: str = "metricas"):
        # Tenta buscar no cache/contexto
        cache_key = f"newrelic_{entidade}_{periodo}_{tipo}"
        dados_cache = context_storage.carregar_contexto(cache_key)
        if dados_cache:
            return {"fonte": "cache", "dados": dados_cache}
        # Se não houver no cache, busca no New Relic
        async def fetch():
            async with __import__('aiohttp').ClientSession() as session:
                if tipo == "entidades":
                    entidades = await get_all_entities(session)
                    return entidades
                elif tipo == "metricas" and entidade:
                    nrql = f"SELECT * FROM Metric WHERE appName = '{entidade}' {periodo.upper()} LIMIT 100"
                    result = await execute_nrql_query(nrql, session=session)
                    return result
                else:
                    return {"erro": "Tipo ou entidade não suportados"}
        dados = asyncio.run(fetch())
        # Salva no cache/contexto
        context_storage.salvar_contexto(cache_key, dados)
        return {"fonte": "newrelic", "dados": dados}
"""
AgnoAgent: Integração do framework Agno com módulos core_inteligente.
Permite raciocínio, memória, ferramentas e automação IA no Analyst_IA.
"""

# Stub seguro para Agent (evita erro de importação e permite endpoints subirem)
class Agent:
    def __init__(self, tools=None):
        self.tools = tools or []

from core_inteligente.learning_engine import LearningEngine
from core_inteligente.context_storage import ContextStorage
from core_inteligente.intent_analyzer import IntentAnalyzer
from core_inteligente.playbook_engine import PlaybookEngine
from core_inteligente.action_dispatcher import ActionDispatcher
from core_inteligente.correlator import Correlator

# Inicialização dos módulos core_inteligente
learning_engine = LearningEngine()
context_storage = ContextStorage()
intent_analyzer = IntentAnalyzer()
playbook_engine = PlaybookEngine()
action_dispatcher = ActionDispatcher()
correlator = Correlator()

# Ferramentas customizadas para o Agno
class ConsultarContextoTool(Tool):
    name = "consultar_contexto"
    description = "Consulta o contexto/memória de uma sessão."
    def run(self, session_id: str):
        return context_storage.carregar_contexto(session_id) or {}

class RegistrarFeedbackTool(Tool):
    name = "registrar_feedback"
    description = "Registra feedback do usuário para aprendizado contínuo."
    def run(self, feedback: dict):
        # Tenta registrar feedback, se não existir método, salva no contexto
        if hasattr(learning_engine, "register_feedback"):
            learning_engine.register_feedback(feedback)
            return "Feedback registrado."
        else:
            context_storage.salvar_feedback(feedback)
            return "Feedback registrado no contexto."

class AnalisarIntencaoTool(Tool):
    name = "analisar_intencao"
    description = "Analisa a intenção da mensagem do usuário."
    def run(self, texto: str):
        return intent_analyzer.analyze(texto)

class ExecutarPlaybookTool(Tool):
    name = "executar_playbook"
    description = "Executa um playbook dinâmico por nome."
    def run(self, nome: str, contexto: dict):
        return playbook_engine.run_playbook(nome, contexto)

class ExecutarAcaoTool(Tool):
    name = "executar_acao"
    description = "Executa uma ação plugável (notificação, webhook, CI/CD)."
    def run(self, acao: dict):
        return action_dispatcher.dispatch(acao)

class CorrelacionarEventosTool(Tool):
    name = "correlacionar_eventos"
    description = "Detecta padrões e picos em eventos."
    def run(self, eventos: list):
        return {
            "padroes": correlator.detect_patterns(eventos),
            "picos": correlator.detect_peaks(eventos)
        }

# NOVAS FERRAMENTAS INTELIGENTES
class GerarRelatorioTool(Tool):
    name = "gerar_relatorio"
    description = "Gera relatório técnico ou executivo sobre entidades, incidentes ou métricas."
    def run(self, tipo: str = "tecnico", filtro: dict = None):
        # Exemplo: integrar com playbook ou gerar relatório customizado
        if tipo == "executivo":
            return playbook_engine.run_playbook("relatorio_executivo", filtro or {})
        return playbook_engine.run_playbook("relatorio_tecnico", filtro or {})

class CorrigirEntidadeTool(Tool):
    name = "corrigir_entidade"
    description = "Executa automação de correção para uma entidade específica."
    def run(self, entidade: str, acao: str = "corrigir"):
        # Exemplo: acionar automação de correção
        return action_dispatcher.dispatch({"entidade": entidade, "acao": acao})

class DispararAlertaTool(Tool):
    name = "disparar_alerta"
    description = "Dispara alerta customizado para equipe ou sistema externo."
    def run(self, mensagem: str, destino: str = "equipe"):
        # Exemplo: integração com webhook, Slack, etc.
        return action_dispatcher.dispatch({"tipo": "alerta", "mensagem": mensagem, "destino": destino})

class ConsultarHistoricoTool(Tool):
    name = "consultar_historico"
    description = "Consulta histórico de interações ou decisões da IA."
    def run(self, session_id: str = None, limite: int = 10):
        return context_storage.consultar_historico(session_id, limite)


# Inicialização do agente Agno (stub seguro, sem dependência de Memory)
agno_agent = Agent(
    tools=[
        ConsultarContextoTool(),
        RegistrarFeedbackTool(),
        AnalisarIntencaoTool(),
        ExecutarPlaybookTool(),
        ExecutarAcaoTool(),
        CorrelacionarEventosTool(),
        GerarRelatorioTool(),
        CorrigirEntidadeTool(),
        DispararAlertaTool(),
        ConsultarHistoricoTool(),
        ColetarDadosNewRelicTool()
    ]
)

def responder_chat(mensagem: str, session_id: str = None, contexto: dict = None):
    """
    Encaminha a mensagem para o agente Agno e retorna a resposta humanizada.
    """
    contexto = contexto or {}
    resposta = agno_agent.chat(
        mensagem,
        session_id=session_id,
        context=contexto
    )
    return resposta
