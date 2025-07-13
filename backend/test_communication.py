"""
Script para testar a comunicação com o servidor MPC
"""
import requests
import json
import logging
import sys
import os

# Configurar logging para arquivo
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "test_communication.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_mpc_communication")

def test_basic_urls():
    # Definir URLs para testar
    urls = [
        "http://localhost:8000/",          # Backend principal
        "http://localhost:10876/",         # Servidor MPC na porta atual
        "http://localhost:9876/",          # Servidor MPC na porta anterior
        "http://localhost:8765/",          # Servidor MPC na porta antiga
    ]
    
    logger.info("Testando comunicação básica com servidores...")
    
    results = {}
    for url in urls:
        try:
            logger.info(f"Tentando conectar a {url}...")
            response = requests.get(url, timeout=5)
            logger.info(f"Resposta de {url}: {response.status_code}")
            logger.info(f"Conteúdo: {response.text[:100]}...")
            results[url] = True
        except requests.exceptions.ConnectionError:
            logger.error(f"Não foi possível conectar a {url}")
            results[url] = False
        except Exception as e:
            logger.error(f"Erro ao conectar a {url}: {e}")
            results[url] = False
    
    return results

def test_mpc_endpoints():
    """Testa os endpoints específicos do MPC"""
    logger.info("Testando endpoints específicos do MPC...")
    
    # Porta padrão do MPC
    mpc_port = 10876
    
    # Endpoints a serem testados
    endpoints = [
        "/agent/status",                # Status geral dos agentes
        "/agent/agno",                  # Endpoint do Agno
        "/agent/agent-s",               # Endpoint do Agent-S
        "/agent/diagnose",              # Endpoint de diagnóstico
    ]
    
    results = {}
    for endpoint in endpoints:
        url = f"http://localhost:{mpc_port}{endpoint}"
        try:
            logger.info(f"Tentando conectar a {url}...")
            response = requests.get(url, timeout=5)
            logger.info(f"Resposta de {url}: {response.status_code}")
            if response.status_code == 200:
                logger.info(f"Conteúdo: {response.text[:100]}...")
                results[endpoint] = True
            else:
                logger.warning(f"Endpoint {endpoint} retornou status {response.status_code}")
                results[endpoint] = False
        except requests.exceptions.ConnectionError:
            logger.error(f"Não foi possível conectar a {url}")
            results[endpoint] = False
        except Exception as e:
            logger.error(f"Erro ao conectar a {url}: {e}")
            results[endpoint] = False
    
    return results

def test_agno_message():
    """Testa o envio de uma mensagem para o Agno"""
    logger.info("Testando envio de mensagem para o Agno...")
    
    try:
        # Importar módulo de interface do Agno
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from core_inteligente.agno_interface import AgnoInterface, falar_com_agno
        
        # Enviar mensagem de teste
        logger.info("Enviando mensagem de teste para o Agno...")
        try:
            resposta = falar_com_agno("Olá, esta é uma mensagem de teste. Você está funcionando?")
            logger.info(f"Resposta do Agno: {resposta}")
            return True, resposta
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para o Agno: {e}")
            return False, str(e)
            
    except ImportError as e:
        logger.error(f"Erro ao importar módulo de interface do Agno: {e}")
        return False, str(e)

def main():
    logger.info("=== Iniciando teste de comunicação do MPC ===")
    
    # Testar URLs básicas
    basic_results = test_basic_urls()
    
    # Se o MPC estiver rodando, testar seus endpoints específicos
    if basic_results.get("http://localhost:10876/", False):
        mpc_results = test_mpc_endpoints()
        
        # Testar envio de mensagem para o Agno
        logger.info("Tentando enviar mensagem para o Agno...")
        success, response = test_agno_message()
        
        if success:
            logger.info("✅ Mensagem enviada com sucesso para o Agno")
        else:
            logger.error("❌ Falha ao enviar mensagem para o Agno")
    else:
        logger.error("Servidor MPC não está respondendo na porta 10876. Pulando testes de endpoints.")
    
    logger.info("=== Teste concluído! ===")

if __name__ == "__main__":
    main()
