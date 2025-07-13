"""
Script de diagnóstico para o problema de comunicação com o Agno

Este script verifica:
1. Se o servidor MPC está rodando
2. Se os endpoints do Agno estão respondendo
3. Se os arquivos de configuração estão corretos
4. Se há algum problema de comunicação entre os componentes
"""

import os
import sys
import json
import logging
from datetime import datetime
import requests
import time

# Configurar logging
log_file = os.path.join("logs", f"agno_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("agno_diagnostic")

def verificar_servidor_mpc():
    """Verifica se o servidor MPC está rodando"""
    portas_mpc = [10876, 9876, 8765]
    
    logger.info("Verificando servidor MPC nas portas conhecidas...")
    
    for porta in portas_mpc:
        url = f"http://localhost:{porta}/"
        try:
            response = requests.get(url, timeout=2)
            logger.info(f"✅ Servidor encontrado na porta {porta}. Status: {response.status_code}")
            return porta
        except:
            logger.info(f"❌ Nenhum servidor na porta {porta}")
    
    logger.error("❌ Nenhum servidor MPC encontrado")
    return None

def verificar_endpoints_mpc(porta):
    """Verifica os endpoints do servidor MPC"""
    endpoints = [
        "/agent/status",
        "/agent/agno",
        "/agent/agent-s"
    ]
    
    logger.info(f"Verificando endpoints MPC na porta {porta}...")
    
    resultados = {}
    for endpoint in endpoints:
        url = f"http://localhost:{porta}{endpoint}"
        try:
            response = requests.get(url, timeout=3)
            status = response.status_code
            resultados[endpoint] = {
                "status": status,
                "ok": 200 <= status < 300
            }
            
            if resultados[endpoint]["ok"]:
                logger.info(f"✅ Endpoint {endpoint} OK (status {status})")
                try:
                    resultados[endpoint]["data"] = response.json()
                except:
                    resultados[endpoint]["data"] = "Não é JSON"
            else:
                logger.warning(f"⚠️ Endpoint {endpoint} retornou status {status}")
        except Exception as e:
            logger.error(f"❌ Erro ao acessar endpoint {endpoint}: {e}")
            resultados[endpoint] = {"status": "erro", "ok": False, "error": str(e)}
    
    return resultados

def testar_comunicacao_agno(porta):
    """Testa comunicação direta com o Agno enviando uma mensagem teste"""
    logger.info("Testando comunicação direta com o Agno...")
    
    url = f"http://localhost:{porta}/agent/agno"
    
    try:
        # Preparar payload para o teste
        payload = {
            "action": "processar_mensagem",
            "parameters": {
                "mensagem": "Esta é uma mensagem de teste para o endpoint do Agno"
            },
            "context": {
                "session_id": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "diagnostic_test": True
            }
        }
        
        # Enviar requisição POST
        logger.info(f"Enviando requisição para {url}")
        response = requests.post(url, json=payload, timeout=10)
        
        # Verificar resposta
        logger.info(f"Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            try:
                dados = response.json()
                logger.info(f"Conteúdo da resposta: {json.dumps(dados, indent=2)[:500]}...")
                logger.info("✅ Comunicação direta com Agno funcionou corretamente")
                return True, dados
            except Exception as e:
                logger.error(f"❌ Erro ao processar resposta JSON: {e}")
                return False, {"error": str(e), "response": response.text[:500]}
        else:
            logger.error(f"❌ Erro na comunicação: Status {response.status_code}")
            return False, {"status": response.status_code, "response": response.text[:500]}
    
    except Exception as e:
        logger.error(f"❌ Erro ao comunicar com Agno: {e}")
        return False, {"error": str(e)}

def verificar_config():
    """Verifica a configuração do MPC"""
    config_path = os.path.join("config", "mpc_agents.json")
    
    logger.info("Verificando configuração MPC...")
    
    if not os.path.exists(config_path):
        logger.warning("⚠️ Arquivo de configuração não encontrado")
        return None
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Verificar agentes configurados
        agentes = config.get("agents", [])
        agentes_ids = [a.get("id") for a in agentes]
        
        logger.info(f"Agentes configurados: {agentes_ids}")
        
        # Verificar URL base
        base_url = config.get("base_url", "")
        logger.info(f"URL base: {base_url}")
        
        # Verificar se Agno está na lista
        if "agno" in agentes_ids:
            logger.info("✅ Agente 'agno' encontrado na configuração")
        else:
            logger.error("❌ Agente 'agno' NÃO está configurado!")
        
        return config
    except Exception as e:
        logger.error(f"❌ Erro ao ler configuração: {e}")
        return None

def tentar_criar_configuracao(porta):
    """Tenta criar uma nova configuração do MPC"""
    logger.info(f"Criando nova configuração na porta {porta}...")
    
    config_dir = os.path.join("config")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "mpc_agents.json")
    
    # Configuração padrão
    config = {
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
            }
        ],
        "base_url": f"http://localhost:{porta}/agent",
        "timeout": 30,
        "retry_attempts": 3,
        "retry_delay": 5
    }
    
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✅ Nova configuração criada: {config_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar configuração: {e}")
        return False

def testar_interface_agno():
    """Testa a interface AgnoInterface usando o módulo de forma isolada"""
    logger.info("Testando interface AgnoInterface...")
    
    try:
        # Importar o módulo da interface
        from core_inteligente.agno_interface import AgnoInterface
