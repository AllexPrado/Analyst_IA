"""
Script para testar diretamente a comunicação com o Agno
"""
import os
import sys
import json
import logging
from datetime import datetime
import asyncio

# Configurar logging
log_file = os.path.join("logs", f"agno_direct_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.DEBUG,  # Usar DEBUG para mostrar mais detalhes
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("agno_direct_test")

async def testar_agno_interface():
    """Testa diretamente a interface do Agno"""
    logger.info("Testando comunicação direta com o Agno...")
    
    # Adicionar diretório atual ao PATH para encontrar os módulos
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from core_inteligente.mpc_agent_communication import MPCAgentCommunication
        
        # Criar cliente MPC
        logger.info("Criando cliente MPC...")
        mpc = MPCAgentCommunication()
        
        # Exibir configuração carregada
        logger.info(f"Configuração carregada: {mpc.config}")
        
        # Verificar status dos agentes
        logger.info("Verificando status dos agentes...")
        status = await mpc.verificar_status_agentes()
        logger.info(f"Status retornado: {status}")
        
        # Enviar comando direto para o Agno
        logger.info("Enviando comando direto para o Agno...")
        resultado = await mpc.enviar_comando_agente(
            "agno", 
            "processar_mensagem", 
            {
                "mensagem": "Olá, esta é uma mensagem de teste direto para o Agno!",
                "session_id": f"test_session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
        )
        logger.info(f"Resultado do comando: {resultado}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao testar Agno Interface: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def testar_agno_endpoint_direto():
    """Testa diretamente o endpoint do Agno via API HTTP"""
    logger.info("Testando endpoint do Agno via API HTTP direta...")
    
    import httpx
    
    # Ler configuração
    try:
        config_path = os.path.join("config", "mpc_agents.json")
        with open(config_path, "r") as f:
            config = json.load(f)
        
        base_url = config.get("base_url", "http://localhost:10876/agent")
        logger.info(f"URL base configurada: {base_url}")
        
        # Obter endpoint do Agno
        agno_endpoint = "/agno"
        for agent in config.get("agents", []):
            if agent.get("id") == "agno":
                agno_endpoint = agent.get("endpoint", "/agno")
                break
        
        url = f"{base_url}{agno_endpoint}"
        logger.info(f"URL do endpoint Agno: {url}")
        
        # Preparar payload
        payload = {
            "action": "processar_mensagem",
            "parameters": {
                "mensagem": "Esta é uma mensagem de teste para o endpoint do Agno",
                "session_id": f"test_http_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
        }
        
        # Enviar requisição
        async with httpx.AsyncClient() as client:
            logger.info(f"Enviando requisição POST para {url}...")
            logger.debug(f"Payload: {payload}")
            
            response = await client.post(
                url, 
                json=payload,
                timeout=30.0
            )
            
            logger.info(f"Status da resposta: {response.status_code}")
            logger.info(f"Conteúdo da resposta: {response.text}")
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Erro na requisição: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Erro ao testar endpoint HTTP: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Função principal"""
    logger.info("=== Iniciando teste direto do Agno ===")
    
    # Testar via interface MPC
    logger.info("--- Teste via interface MPC ---")
    resultado_interface = await testar_agno_interface()
    
    # Testar via endpoint HTTP
    logger.info("\n--- Teste via endpoint HTTP ---")
    resultado_http = await testar_agno_endpoint_direto()
    
    # Resultado final
    logger.info("\n=== Resultados dos testes ===")
    logger.info(f"Teste via interface MPC: {'✅ SUCESSO' if resultado_interface else '❌ FALHA'}")
    logger.info(f"Teste via endpoint HTTP: {'✅ SUCESSO' if resultado_http else '❌ FALHA'}")
    
    logger.info(f"\nLog completo salvo em: {log_file}")

if __name__ == "__main__":
    asyncio.run(main())
