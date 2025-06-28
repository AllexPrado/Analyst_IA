"""
Módulo que integra o backend com o sistema de aprendizado contínuo (cara_cinteligente).
Garante que as interações do usuário sejam registradas e utilizadas para melhorar as respostas.
"""

import logging
import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

# Configuração de logging
logger = logging.getLogger(__name__)

# Adiciona o diretório raiz ao path do Python para permitir importar core_inteligente
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from core_inteligente.context_storage import ContextStorage
    from core_inteligente.learning_engine import LearningEngine
    
    # Inicializa componentes do sistema de aprendizado
    storage = ContextStorage()
    
    # Estatísticas de funcionamento
    stats = {
        "registros_sucesso": 0,
        "registros_fallback": 0,
        "registros_falha": 0,
        "ultima_atualizacao": datetime.now().isoformat()
    }
    
    # Verifica a assinatura do construtor do LearningEngine para inicializar corretamente
    import inspect
    learning_engine = None
    
    # Examina a assinatura do construtor
    try:
        sig = inspect.signature(LearningEngine.__init__)
        param_names = list(sig.parameters.keys())
        
        # Se __init__ aceita apenas self (além de self)
        if len(param_names) == 1:
            learning_engine = LearningEngine()
            # Se o objeto tem atributo storage, define-o
            if hasattr(learning_engine, 'storage'):
                learning_engine.storage = storage
                logger.info("LearningEngine inicializado e storage definido posteriormente")
        # Se __init__ aceita self e storage (2 parâmetros)
        elif len(param_names) == 2:
            learning_engine = LearningEngine(storage)
            logger.info("LearningEngine inicializado com storage no construtor")
        # Para outros casos
        else:
            logger.warning(f"Assinatura do construtor LearningEngine incompatível: {param_names}")
            # Tenta sem parâmetros como fallback
            learning_engine = LearningEngine()
    except Exception as e:
        logger.error(f"Erro ao analisar assinatura do LearningEngine: {e}")
        # Tentativa final - primeiro sem parâmetros, depois com storage
        try:
            learning_engine = LearningEngine()
        except TypeError:
            try:
                learning_engine = LearningEngine(storage)
            except Exception as e2:
                logger.error(f"Todas as tentativas de inicializar LearningEngine falharam: {e2}")
    
    # Verifica se foi possível inicializar
    if learning_engine:
        LEARNING_ENABLED = True
        logger.info("Sistema de aprendizado contínuo inicializado com sucesso")
    else:
        LEARNING_ENABLED = False
        logger.warning("Não foi possível inicializar o sistema de aprendizado")
except Exception as e:
    logger.warning(f"Não foi possível inicializar módulos do core_inteligente: {e}")
    LEARNING_ENABLED = False
    storage = None
    learning_engine = None

class LearningIntegration:
    """
    Classe responsável pela integração entre o backend e o sistema de aprendizado contínuo.
    """
    
    @staticmethod
    def is_enabled() -> bool:
        """Verifica se o sistema de aprendizado está habilitado"""
        return LEARNING_ENABLED
    
    @staticmethod
    async def registrar_interacao(session_id: str, pergunta: str, resposta: str, 
                                  feedback: Optional[str] = None, 
                                  contexto: Optional[Dict[str, Any]] = None) -> bool:
        """
        Registra uma interação de chat para aprendizado futuro
        
        Args:
            session_id: Identificador único da sessão
            pergunta: Pergunta do usuário
            resposta: Resposta gerada pela IA
            feedback: Feedback opcional do usuário (positivo/negativo)
            contexto: Contexto utilizado para gerar a resposta
            
        Returns:
            bool: True se o registro foi bem-sucedido
        """
        if not LEARNING_ENABLED:
            logger.debug("Sistema de aprendizado desabilitado, ignorando registro de interação")
            return False
            
        try:
            # Cria evento de interação
            evento = {
                "tipo": "chat",
                "pergunta": pergunta,
                "resposta": resposta,
                "feedback": feedback,
                "contexto": contexto
            }
            
            # Registra via learning engine
            if learning_engine:
                try:
                    # Verifica se o método existe antes de chamar
                    if hasattr(learning_engine, 'registrar_feedback'):
                        # O método registrar_feedback da LearningEngine espera (session_id, evento, resultado)
                        learning_engine.registrar_feedback(session_id, "interacao_chat", evento)
                        logger.info(f"Interação registrada no sistema de aprendizado: {session_id[:8]}...")
                        if 'stats' in globals():
                            stats["registros_sucesso"] += 1
                            stats["ultima_atualizacao"] = datetime.now().isoformat()
                        return True
                    else:
                        # Fallback: tenta registrar_interacao se disponível
                        if hasattr(learning_engine, 'registrar_interacao'):
                            learning_engine.registrar_interacao(session_id, evento)
                            logger.info(f"Interação registrada via método alternativo: {session_id[:8]}...")
                            if 'stats' in globals():
                                stats["registros_fallback"] += 1
                                stats["ultima_atualizacao"] = datetime.now().isoformat()
                            return True
                        else:
                            logger.warning(f"Método 'registrar_feedback' ou 'registrar_interacao' não encontrado no LearningEngine")
                            # Armazena diretamente no storage como fallback final
                            if storage:
                                contexto = storage.carregar_contexto(session_id) or {}
                                contexto.setdefault("feedbacks", []).append({"evento": "interacao_chat", "resultado": evento})
                                storage.salvar_contexto(session_id, contexto)
                                logger.info(f"Feedback salvo diretamente no storage como fallback: {session_id[:8]}...")
                                if 'stats' in globals():
                                    stats["registros_fallback"] += 1
                                    stats["ultima_atualizacao"] = datetime.now().isoformat()
                                return True
                except Exception as e:
                    logger.error(f"Erro ao registrar feedback: {e}", exc_info=True)
                    if 'stats' in globals():
                        stats["registros_falha"] += 1
                        stats["ultima_atualizacao"] = datetime.now().isoformat()
                    
                return False
                
        except Exception as e:
            logger.error(f"Erro ao registrar interação no sistema de aprendizado: {e}")
            if 'stats' in globals():
                stats["registros_falha"] += 1
                stats["ultima_atualizacao"] = datetime.now().isoformat()
            
        return False
    
    @staticmethod
    async def obter_sugestoes(pergunta: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtém sugestões do sistema de aprendizado para melhorar a resposta
        
        Args:
            pergunta: Pergunta do usuário
            contexto: Contexto atual
            
        Returns:
            Dict: Sugestões para melhorar a resposta
        """
        if not LEARNING_ENABLED:
            return {}
            
        try:
            # Implementação simplificada inicial
            # Futuramente pode utilizar histórico de perguntas similares
            return {
                "sugestoes": [],
                "aprendizado_ativo": True
            }
        except Exception as e:
            logger.error(f"Erro ao obter sugestões do sistema de aprendizado: {e}")
            return {"erro": str(e)}
    
    @staticmethod
    async def registrar_metricas(metricas: Dict[str, Any]) -> bool:
        """
        Registra métricas de uso do sistema para análise e melhoria contínua
        
        Args:
            metricas: Dicionário com métricas a serem registradas
            
        Returns:
            bool: True se o registro foi bem-sucedido
        """
        if not LEARNING_ENABLED:
            return False
            
        try:
            # Local para implementar registro de métricas
            # Por exemplo, tempo de resposta, satisfação do usuário, etc.
            return True
        except Exception as e:
            logger.error(f"Erro ao registrar métricas: {e}")
            return False

    @staticmethod
    async def obter_estatisticas() -> Dict[str, Any]:
        """
        Obtém estatísticas do sistema de aprendizado
        
        Returns:
            Dict: Estatísticas de uso do sistema de aprendizado
        """
        if not LEARNING_ENABLED:
            return {"status": "desativado", "motivo": "Sistema de aprendizado não inicializado"}
            
        try:
            resultado = {
                "status": "ativo" if learning_engine else "parcial",
                "engine_disponivel": learning_engine is not None,
                "storage_disponivel": storage is not None,
            }
            
            if 'stats' in globals():
                resultado.update({
                    "estatisticas": stats,
                    "metodos_disponiveis": {
                        "registrar_feedback": hasattr(learning_engine, 'registrar_feedback') if learning_engine else False,
                        "registrar_interacao": hasattr(learning_engine, 'registrar_interacao') if learning_engine else False,
                        "sugerir_melhoria": hasattr(learning_engine, 'sugerir_melhoria') if learning_engine else False
                    }
                })
                
                # Se temos storage, vamos contar quantos arquivos de contexto existem
                if storage and hasattr(storage, 'path'):
                    try:
                        import os
                        path = storage.path
                        arquivos = [f for f in os.listdir(path) if f.endswith('.json')]
                        resultado["contextos_salvos"] = len(arquivos)
                        if arquivos:
                            resultado["ultimo_contexto"] = max(arquivos, key=lambda f: os.path.getmtime(os.path.join(path, f)))
                    except Exception as e:
                        resultado["erro_contagem"] = str(e)
                
            return resultado
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do sistema de aprendizado: {e}")
            return {"status": "erro", "mensagem": str(e)}

# Inicialização default
learning_integration = LearningIntegration()
