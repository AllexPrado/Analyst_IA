"""
MPC Agent Communication Module

Este módulo fornece uma interface simplificada para comunicação com agentes MPC
(Model Context Protocol). Permite enviar comandos, receber respostas e monitorar
o status dos agentes de forma centralizada.
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any, Union
import httpx
from datetime import datetime
import traceback
from pydantic import BaseModel

# Configuração do logger
logger = logging.getLogger("mpc_agent_communication")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Arquivo de configuração dos agentes
AGENT_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "config", "mpc_agents.json")

# Caminho para armazenar o histórico de comunicações
COMMUNICATION_HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                       "logs", "mpc_communication_history.json")

# Diretório para os logs
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# Diretório para a configuração
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR, exist_ok=True)

# Classes de requisição/resposta para comunicação com agentes
class AgentRequest(BaseModel):
    action: str
    parameters: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    agent_id: Optional[str] = None
    priority: Optional[int] = 1  # 1 (baixa) a 5 (alta)
    timeout: Optional[int] = 60  # segundos

class AgentResponse(BaseModel):
    status: str  # "success", "error", "pending"
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    agent_id: Optional[str] = None

# Configuração padrão para os agentes
DEFAULT_AGENT_CONFIG = {
    "agents": [
        {
            "id": "agno",
            "name": "Agno - Agente Principal",
            "description": "Agente principal de orquestração que processa comandos em linguagem natural",
            "endpoint": "/agno",
            "enabled": True
        },
        {
            "id": "agent-s",
            "name": "Agent-S - Agente de Serviço",
            "description": "Agente de serviço que executa tarefas sob orientação do Agno",
            "endpoint": "/agent-s",
            "enabled": True
        },
        {
            "id": "diagnostico",
            "name": "Agente de Diagnóstico",
            "description": "Realiza diagnósticos do sistema e identifica problemas",
            "endpoint": "/diagnose",
            "enabled": True
        },
        {
            "id": "correcao",
            "name": "Agente de Correção Automática",
            "description": "Corrige problemas identificados no sistema",
            "endpoint": "/autofix",
            "enabled": True
        },
        {
            "id": "otimizacao",
            "name": "Agente de Otimização",
            "description": "Otimiza o desempenho do sistema",
            "endpoint": "/optimize",
            "enabled": True
        },
        {
            "id": "seguranca",
            "name": "Agente de Segurança",
            "description": "Realiza verificações de segurança no sistema",
            "endpoint": "/security_check",
            "enabled": True
        },
        {
            "id": "coleta",
            "name": "Agente de Coleta de Dados",
            "description": "Coleta dados de métricas e eventos do sistema",
            "endpoint": "/coletar_newrelic",
            "enabled": True
        }
    ],
    "base_url": "http://localhost:10876/agent",
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 5
}

class MPCAgentCommunication:
    def __init__(self):
        self.config = self._load_config()
        self.base_url = self.config.get("base_url", "http://localhost:8000/agent")
        self.timeout = self.config.get("timeout", 30)
        self.retry_attempts = self.config.get("retry_attempts", 3)
        self.retry_delay = self.config.get("retry_delay", 5)
        self.agents = self.config.get("agents", [])
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.history = self._load_history()
    
    def _load_config(self) -> Dict:
        """Carrega a configuração dos agentes"""
        try:
            if os.path.exists(AGENT_CONFIG_FILE):
                with open(AGENT_CONFIG_FILE, "r") as f:
                    return json.load(f)
            else:
                # Criar arquivo de configuração padrão se não existir
                os.makedirs(os.path.dirname(AGENT_CONFIG_FILE), exist_ok=True)
                with open(AGENT_CONFIG_FILE, "w") as f:
                    json.dump(DEFAULT_AGENT_CONFIG, f, indent=4)
                logger.info(f"Arquivo de configuração criado em {AGENT_CONFIG_FILE}")
                return DEFAULT_AGENT_CONFIG
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return DEFAULT_AGENT_CONFIG
    
    def _load_history(self) -> List[Dict]:
        """Carrega o histórico de comunicações"""
        try:
            if os.path.exists(COMMUNICATION_HISTORY_FILE):
                with open(COMMUNICATION_HISTORY_FILE, "r") as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Erro ao carregar histórico: {e}")
            return []
    
    def _save_history(self):
        """Salva o histórico de comunicações"""
        try:
            with open(COMMUNICATION_HISTORY_FILE, "w") as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")
    
    def _add_to_history(self, request: Dict, response: Dict, duration: float):
        """Adiciona uma comunicação ao histórico"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "request": request,
            "response": response,
            "duration": duration
        }
        self.history.append(entry)
        # Manter apenas os últimos 1000 registros
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        self._save_history()
    
    def get_agent_by_id(self, agent_id: str) -> Optional[Dict]:
        """Obtém um agente pelo ID"""
        for agent in self.agents:
            if agent.get("id") == agent_id:
                return agent
        return None
    
    async def send_command(self, request: Union[AgentRequest, Dict]) -> AgentResponse:
        """Envia um comando para um agente"""
        start_time = asyncio.get_event_loop().time()
        
        if isinstance(request, dict):
            request = AgentRequest(**request)
        
        agent_id = request.agent_id
        if not agent_id:
            return AgentResponse(
                status="error",
                error_message="ID do agente não especificado"
            )
        
        agent = self.get_agent_by_id(agent_id)
        if not agent:
            return AgentResponse(
                status="error",
                error_message=f"Agente com ID '{agent_id}' não encontrado"
            )
        
        if not agent.get("enabled", True):
            return AgentResponse(
                status="error",
                error_message=f"Agente '{agent_id}' está desativado"
            )
        
        endpoint = agent.get("endpoint")
        url = f"{self.base_url}{endpoint}"
        
        request_data = {
            "action": request.action,
            "parameters": request.parameters or {},
            "context": request.context or {},
            "agent_id": agent_id,
            "priority": request.priority or 1,
            "timestamp": datetime.now().isoformat()
        }
        
        response_data = {
            "status": "error",
            "error_message": "Falha ao comunicar com o agente"
        }
        
        attempts = 0
        while attempts < self.retry_attempts:
            try:
                async with self.client.stream("POST", url, json=request_data, timeout=request.timeout or self.timeout) as response:
                    if response.status_code == 200:
                        response_data = await response.json()
                        response_data["status"] = "success"
                        break
                    else:
                        response_data = {
                            "status": "error",
                            "error_message": f"Erro HTTP {response.status_code}: {await response.text()}"
                        }
            except Exception as e:
                response_data = {
                    "status": "error",
                    "error_message": f"Exceção: {str(e)}\n{traceback.format_exc()}"
                }
            
            attempts += 1
            if attempts < self.retry_attempts:
                await asyncio.sleep(self.retry_delay)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        response_data["execution_time"] = duration
        response_data["agent_id"] = agent_id
        
        self._add_to_history(request_data, response_data, duration)
        
        return AgentResponse(**response_data)
    
    async def broadcast_command(self, action: str, parameters: Dict = None, context: Dict = None) -> Dict[str, AgentResponse]:
        """Envia um comando para todos os agentes ativos"""
        results = {}
        tasks = []
        
        for agent in self.agents:
            if agent.get("enabled", True):
                request = AgentRequest(
                    action=action,
                    parameters=parameters,
                    context=context,
                    agent_id=agent.get("id")
                )
                task = self.send_command(request)
                tasks.append((agent.get("id"), task))
        
        for agent_id, task in tasks:
            try:
                results[agent_id] = await task
            except Exception as e:
                results[agent_id] = AgentResponse(
                    status="error",
                    error_message=f"Erro ao processar resposta: {str(e)}",
                    agent_id=agent_id
                )
        
        return results
    
    async def get_agent_status(self, agent_id: Optional[str] = None) -> Dict:
        """Obtém o status de um agente específico ou de todos os agentes"""
        if agent_id:
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                return {"status": "error", "message": f"Agente '{agent_id}' não encontrado"}
            
            try:
                url = f"{self.base_url}/status"
                params = {"agent_id": agent_id}
                async with self.client.get(url, params=params) as response:
                    if response.status_code == 200:
                        return await response.json()
                    else:
                        return {
                            "status": "error", 
                            "message": f"Erro HTTP {response.status_code}: {await response.text()}"
                        }
            except Exception as e:
                return {"status": "error", "message": f"Exceção: {str(e)}"}
        else:
            # Obter status de todos os agentes
            results = {}
            for agent in self.agents:
                agent_id = agent.get("id")
                result = await self.get_agent_status(agent_id)
                results[agent_id] = result
            return results
    
    def get_communication_history(self, agent_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Obtém o histórico de comunicações com os agentes"""
        if agent_id:
            filtered_history = [
                entry for entry in self.history 
                if entry.get("request", {}).get("agent_id") == agent_id
            ]
            return filtered_history[-limit:] if filtered_history else []
        else:
            return self.history[-limit:] if self.history else []

# Instância global para fácil importação
mpc_communication = MPCAgentCommunication()

# Funções auxiliares para facilitar o uso
async def send_agent_command(agent_id: str, action: str, parameters: Dict = None, context: Dict = None) -> AgentResponse:
    """Função auxiliar para enviar um comando para um agente"""
    request = AgentRequest(
        action=action,
        parameters=parameters or {},
        context=context or {},
        agent_id=agent_id
    )
    return await mpc_communication.send_command(request)

async def broadcast_to_agents(action: str, parameters: Dict = None, context: Dict = None) -> Dict[str, AgentResponse]:
    """Função auxiliar para enviar um comando para todos os agentes"""
    return await mpc_communication.broadcast_command(action, parameters, context)

async def get_agent_status(agent_id: Optional[str] = None) -> Dict:
    """Função auxiliar para obter o status de um agente ou de todos os agentes"""
    return await mpc_communication.get_agent_status(agent_id)

def get_agent_history(agent_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """Função auxiliar para obter o histórico de comunicações com um agente"""
    return mpc_communication.get_communication_history(agent_id, limit)

# Exemplos de uso:
if __name__ == "__main__":
    async def test():
        # Exemplo: Enviar um comando para o agente de diagnóstico
        response = await send_agent_command(
            agent_id="diagnostico",
            action="run_diagnostic",
            parameters={"scope": "full"},
            context={"urgency": "high"}
        )
        print(f"Resposta do agente de diagnóstico: {response}")
        
        # Exemplo: Enviar um comando para todos os agentes
        responses = await broadcast_to_agents(
            action="status_update",
            parameters={"check_health": True}
        )
        for agent_id, resp in responses.items():
            print(f"Agente {agent_id}: {resp}")
        
        # Exemplo: Obter status de todos os agentes
        status = await get_agent_status()
        print(f"Status dos agentes: {status}")
        
        # Exemplo: Obter histórico de comunicações
        history = get_agent_history(limit=10)
        print(f"Histórico de comunicações: {history}")
    
    # Executar o teste
    asyncio.run(test())
