"""
Interface de Comunicação com o Agno

Este módulo simplifica a comunicação com o Agno, o agente principal de orquestração
do sistema MPC. O Agno recebe comandos em linguagem natural, entende as intenções,
e coordena ações com o Agent-S e outros agentes especializados.
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Adicionar diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos necessários
from core_inteligente.mpc_agent_communication import send_agent_command, broadcast_to_agents
from core_inteligente.context_storage import ContextStorage

# Configurar logger
logger = logging.getLogger("agno_interface")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Carregar o sistema de contexto
context_storage = ContextStorage()

class AgnoInterface:
    """Interface principal para comunicação com o Agno"""
    
    def __init__(self):
        """Inicializa a interface do Agno"""
        self.session_id = None
        self.history = []
    
    def iniciar_sessao(self, session_id: Optional[str] = None) -> str:
        """
        Inicia uma nova sessão de conversação com o Agno.
        
        Args:
            session_id: ID de sessão personalizado. Se não fornecido, gera um automático.
            
        Returns:
            ID da sessão criada
        """
        if not session_id:
            # Gerar um ID de sessão baseado em timestamp
            session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.session_id = session_id
        self.history = []
        
        # Registrar início de sessão no contexto
        context_storage.salvar_contexto(
            session_id, 
            {
                "criado_em": datetime.now().isoformat(),
                "mensagens": [],
                "agentes_utilizados": []
            }
        )
        
        logger.info(f"Sessão iniciada: {session_id}")
        return session_id
    
    async def enviar_mensagem(self, mensagem: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Envia uma mensagem em linguagem natural para o Agno processar.
        
        Args:
            mensagem: Texto da mensagem em linguagem natural
            context: Contexto adicional para a mensagem (opcional)
            
        Returns:
            Resposta do Agno com ações realizadas e próximos passos
        """
        if not self.session_id:
            self.iniciar_sessao()
        
        # Preparar contexto completo
        contexto_completo = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Adicionar contexto personalizado se fornecido
        if context:
            contexto_completo.update(context)
        
        logger.info(f"Enviando mensagem para Agno: {mensagem[:50]}{'...' if len(mensagem) > 50 else ''}")
        
        try:
            # Comunicar com o agente Agno
            resposta = await send_agent_command(
                agent_id="agno",  # ID do agente Agno
                action="processar_mensagem",
                parameters={
                    "mensagem": mensagem
                },
                context=contexto_completo
            )
            
            # Registrar histórico
            entrada = {
                "tipo": "usuario",
                "mensagem": mensagem,
                "timestamp": datetime.now().isoformat()
            }
            
            saida = {
                "tipo": "agno",
                "resposta": resposta.data if resposta.status == "success" else {"erro": resposta.error_message},
                "timestamp": datetime.now().isoformat()
            }
            
            self.history.append(entrada)
            self.history.append(saida)
            
            # Atualizar o contexto da sessão
            sessao_atual = context_storage.carregar_contexto(self.session_id) or {}
            mensagens_anteriores = sessao_atual.get("mensagens", [])
            mensagens_anteriores.extend([entrada, saida])
            
            # Limitar histórico a 20 mensagens (10 pares) para evitar sobrecarga
            if len(mensagens_anteriores) > 20:
                mensagens_anteriores = mensagens_anteriores[-20:]
            
            sessao_atual["mensagens"] = mensagens_anteriores
            context_storage.salvar_contexto(self.session_id, sessao_atual)
            
            # Retornar dados formatados
            if resposta.status == "success":
                return resposta.data
            else:
                return {
                    "erro": True,
                    "mensagem": resposta.error_message,
                    "sugestao": "Verifique se o agente Agno está ativo e funcionando corretamente."
                }
                
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para Agno: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "erro": True,
                "mensagem": f"Erro de comunicação: {str(e)}",
                "sugestao": "Verifique a conexão com o serviço MPC e se os agentes estão em execução."
            }
    
    async def executar_comando(self, comando: str, parametros: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executa um comando específico através do Agno, sem processamento de linguagem natural.
        
        Args:
            comando: Nome do comando a ser executado
            parametros: Parâmetros para o comando (opcional)
            
        Returns:
            Resultado da execução do comando
        """
        if not self.session_id:
            self.iniciar_sessao()
        
        logger.info(f"Executando comando via Agno: {comando}")
        
        try:
            # Comunicar diretamente com o Agent-S através do Agno
            resposta = await send_agent_command(
                agent_id="agno",
                action="executar_comando",
                parameters={
                    "comando": comando,
                    "parametros": parametros or {}
                },
                context={
                    "session_id": self.session_id,
                    "timestamp": datetime.now().isoformat(),
                    "tipo": "comando_direto"
                }
            )
            
            # Registrar comando no histórico
            entrada = {
                "tipo": "comando",
                "comando": comando,
                "parametros": parametros or {},
                "timestamp": datetime.now().isoformat()
            }
            
            saida = {
                "tipo": "resultado",
                "dados": resposta.data if resposta.status == "success" else {"erro": resposta.error_message},
                "timestamp": datetime.now().isoformat()
            }
            
            self.history.append(entrada)
            self.history.append(saida)
            
            # Retornar dados formatados
            if resposta.status == "success":
                return resposta.data
            else:
                return {
                    "erro": True,
                    "mensagem": resposta.error_message
                }
                
        except Exception as e:
            logger.error(f"Erro ao executar comando via Agno: {str(e)}")
            return {
                "erro": True,
                "mensagem": f"Erro de execução: {str(e)}"
            }
    
    def obter_historico(self, ultimas_n: int = 10) -> List[Dict[str, Any]]:
        """
        Obtém o histórico de comunicações com o Agno.
        
        Args:
            ultimas_n: Número de mensagens a retornar (padrão: 10)
            
        Returns:
            Lista com as últimas mensagens trocadas
        """
        return self.history[-ultimas_n:] if self.history else []
    
    async def verificar_status(self) -> Dict[str, Any]:
        """
        Verifica o status atual do Agno e do Agent-S.
        
        Returns:
            Status dos agentes principais
        """
        try:
            # Verificar status do Agno
            status_agno = await send_agent_command(
                agent_id="agno",
                action="status",
                parameters={}
            )
            
            # Verificar status do Agent-S
            status_agents = await send_agent_command(
                agent_id="agent-s",
                action="status",
                parameters={}
            )
            
            return {
                "agno": {
                    "ativo": status_agno.status == "success",
                    "detalhes": status_agno.data if status_agno.status == "success" else {"erro": status_agno.error_message}
                },
                "agent-s": {
                    "ativo": status_agents.status == "success",
                    "detalhes": status_agents.data if status_agents.status == "success" else {"erro": status_agents.error_message}
                }
            }
        except Exception as e:
            logger.error(f"Erro ao verificar status dos agentes: {str(e)}")
            return {
                "erro": True,
                "mensagem": f"Erro ao verificar status: {str(e)}"
            }

# Interface de comunicação rápida com o Agno (para uso simplificado)
async def falar_com_agno(mensagem: str, context: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Função simplificada para comunicação rápida com o Agno.
    
    Args:
        mensagem: Texto da mensagem em linguagem natural
        context: Contexto adicional para a mensagem (opcional)
        session_id: ID de sessão personalizado (opcional)
        
    Returns:
        Resposta do Agno
    """
    interface = AgnoInterface()
    
    if session_id:
        interface.iniciar_sessao(session_id)
    else:
        interface.iniciar_sessao()
    
    return await interface.enviar_mensagem(mensagem, context)

# Exemplo de uso
if __name__ == "__main__":
    async def teste_comunicacao():
        # Exemplo 1: Comunicação simplificada
        print("=== Exemplo 1: Comunicação Simplificada ===")
        resposta = await falar_com_agno("Preciso de um diagnóstico do sistema")
        print(f"Resposta: {json.dumps(resposta, indent=2)}")
        
        # Exemplo 2: Comunicação com sessão contínua
        print("\n=== Exemplo 2: Comunicação com Sessão ===")
        agno = AgnoInterface()
        session_id = agno.iniciar_sessao()
        print(f"Nova sessão: {session_id}")
        
        # Primeira mensagem
        resposta1 = await agno.enviar_mensagem(
            "Quais métricas de CPU tivemos na última semana?"
        )
        print(f"Resposta 1: {json.dumps(resposta1, indent=2)}")
        
        # Segunda mensagem (com contexto da primeira)
        resposta2 = await agno.enviar_mensagem(
            "E como está o uso de memória?"
        )
        print(f"Resposta 2: {json.dumps(resposta2, indent=2)}")
        
        # Verificar histórico
        historico = agno.obter_historico()
        print(f"\nHistórico ({len(historico)} mensagens):")
        for item in historico:
            tipo = item.get("tipo", "desconhecido")
            if tipo == "usuario":
                print(f"Usuário: {item.get('mensagem')}")
            elif tipo == "agno":
                if "erro" in item.get("resposta", {}):
                    print(f"Agno: Erro - {item['resposta']['erro']}")
                else:
                    print(f"Agno: {item['resposta'].get('mensagem', 'Sem mensagem')}")
        
        # Verificar status
        status = await agno.verificar_status()
        print(f"\nStatus dos agentes: {json.dumps(status, indent=2)}")
    
    # Executar teste
    asyncio.run(teste_comunicacao())
