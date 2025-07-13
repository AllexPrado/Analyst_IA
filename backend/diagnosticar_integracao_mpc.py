"""
Script para testar uma integração completa do MPC com o backend principal

Verifica se:
1. O backend principal está rodando na porta 8000
2. O servidor MPC está rodando na porta 9876 ou 10876
3. A comunicação entre os dois está funcionando
"""

import requests
import sys
import os
import json
import time
import logging
from datetime import datetime

# Configurar logging
log_file = os.path.join("logs", f"mpc_diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("mpc_diagnosis")

def check_port_status(host, port):
    """Verifica se uma porta está aberta e respondendo"""
    url = f"http://{host}:{port}/"
    try:
        response = requests.get(url, timeout=3)
        logger.info(f"✓ Porta {port} está respondendo. Status: {response.status_code}")
        return True, response.status_code
    except requests.exceptions.ConnectionError:
        logger.warning(f"✗ Porta {port} não está respondendo")
        return False, None
    except Exception as e:
        logger.error(f"Erro ao conectar na porta {port}: {e}")
        return False, None

def check_agno_endpoints(port=8000):
    """Verifica se os endpoints do Agno estão disponíveis"""
    endpoints = [
        "/agno/status",
        "/api/agno/status",
    ]
    
    results = {}
    for endpoint in endpoints:
        url = f"http://localhost:{port}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            logger.info(f"Endpoint {endpoint}: Status {response.status_code}")
            results[endpoint] = {
                "status": response.status_code,
                "working": 200 <= response.status_code < 300
            }
            try:
                results[endpoint]["data"] = response.json()
            except:
                results[endpoint]["data"] = "Não é JSON válido"
        except Exception as e:
            logger.error(f"Erro ao acessar {endpoint}: {e}")
            results[endpoint] = {"status": "erro", "error": str(e)}
    
    return results

def check_mpc_server(ports=[9876, 10876, 8765]):
    """Verifica se o servidor MPC está rodando em alguma das portas possíveis"""
    for port in ports:
        success, status = check_port_status("localhost", port)
        if success:
            logger.info(f"Servidor MPC encontrado na porta {port}")
            
            # Testar endpoint de agentes
            try:
                url = f"http://localhost:{port}/agent/status"
                response = requests.get(url, timeout=3)
                logger.info(f"Endpoint de status do MPC: {response.status_code}")
                if response.status_code == 200:
                    logger.info(f"Resposta: {response.json()}")
                    return port, True
            except Exception as e:
                logger.error(f"Erro ao verificar endpoint do MPC: {e}")
    
    logger.error("Servidor MPC não encontrado em nenhuma porta")
    return None, False

def test_mpc_integration():
    """Testa a integração entre o backend principal e o servidor MPC"""
    logger.info("=== Iniciando diagnóstico do sistema MPC ===")
    
    # Verificar backend principal
    logger.info("Verificando backend principal (porta 8000)...")
    success, status = check_port_status("localhost", 8000)
    if not success:
        logger.error("✗ Backend principal não está rodando na porta 8000")
        return False
    
    # Verificar endpoints do Agno no backend principal
    logger.info("Verificando endpoints do Agno...")
    agno_results = check_agno_endpoints()
    
    # Verificar servidor MPC
    logger.info("Procurando servidor MPC...")
    mpc_port, mpc_running = check_mpc_server()
    
    if not mpc_running:
        logger.error("✗ Servidor MPC não está rodando")
        logger.info("Tentando iniciar o servidor MPC na porta 10876...")
        
        try:
            # Criar diretório config se não existir
            os.makedirs("config", exist_ok=True)
            
            # Atualizar arquivo de configuração com a porta correta
            with open("config/mpc_port.txt", "w") as f:
                f.write("porta=10876")
                
            # Iniciar servidor MPC
            import subprocess
            subprocess.Popen(["python", "mpc_server.py", "--port", "10876"], 
                            stdout=open(os.path.join("logs", "mpc_server_auto.log"), "w"),
                            stderr=subprocess.STDOUT)
                
            logger.info("Aguardando inicialização do servidor MPC (10s)...")
            time.sleep(10)
            
            # Verificar novamente
            mpc_port, mpc_running = check_mpc_server([10876])
        except Exception as e:
            logger.error(f"Erro ao iniciar servidor MPC: {e}")
    
    # Atualizar o arquivo de configuração do MPC se necessário
    if mpc_port and mpc_port != 9876:
        logger.info(f"Atualizando configuração para usar a porta {mpc_port}...")
        config_dir = "config"
        os.makedirs(config_dir, exist_ok=True)
        
        # Atualizar ou criar o arquivo de configuração
        config_path = os.path.join(config_dir, "mpc_agents.json")
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
            else:
                config = {
                    "agents": [],
                    "base_url": f"http://localhost:{mpc_port}/agent",
                    "timeout": 30,
                    "retry_attempts": 3,
                    "retry_delay": 5
                }
                
            config["base_url"] = f"http://localhost:{mpc_port}/agent"
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Configuração atualizada para usar a porta {mpc_port}")
        except Exception as e:
            logger.error(f"Erro ao atualizar configuração: {e}")
    
    # Relatório final
    logger.info("=== Diagnóstico concluído ===")
    logger.info(f"Backend principal: {'✓ Rodando' if success else '✗ Não rodando'}")
    logger.info(f"Servidor MPC: {'✓ Rodando na porta '+str(mpc_port) if mpc_running else '✗ Não rodando'}")
    
    return success and mpc_running

if __name__ == "__main__":
    test_mpc_integration()
