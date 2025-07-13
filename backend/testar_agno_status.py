"""
Teste específico para o método verificar_status do AgnoInterface

Este script testa de forma isolada o método verificar_status da classe AgnoInterface
e compara com uma requisição HTTP direta para verificar a diferença.
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
import requests

# Adicionar diretório pai ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/agno_status_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("agno_status_test")

async def testar_metodo_verificar_status():
    """Testa o método verificar_status da classe AgnoInterface"""
    try:
        from core_inteligente.agno_interface import AgnoInterface
        
        logger.info("Criando instância do AgnoInterface...")
        agno = AgnoInterface()
        
        logger.info("Executando método verificar_status()...")
        resultado = await agno.verificar_status()
        
        logger.info(f"Resultado obtido: {json.dumps(resultado, indent=2)}")
        
        return resultado
    except Exception as e:
        logger.error(f"Erro ao executar verificar_status: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"erro": str(e)}

def testar_requisicao_direta():
    """Testa uma requisição direta ao endpoint de status do Agno"""
    portas = [10876, 9876, 8000]
    
    for porta in portas:
        try:
            logger.info(f"Tentando porta {porta}...")
            url = f"http://localhost:{porta}/agent/agno"
            
            payload = {
                "action": "status",
                "parameters": {},
                "context": {
                    "session_id": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "timestamp": datetime.now().isoformat(),
                    "diagnostic_test": True
                }
            }
            
            logger.info(f"Enviando requisição para {url}")
            response = requests.post(url, json=payload, timeout=5)
            
            logger.info(f"Status da resposta: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    resultado = response.json()
                    logger.info(f"Resposta: {json.dumps(resultado, indent=2)}")
                    return {"porta": porta, "status": response.status_code, "resposta": resultado}
                except Exception as e:
                    logger.error(f"Erro ao processar JSON: {e}")
            else:
                logger.warning(f"Requisição falhou com status {response.status_code}")
                
        except Exception as e:
            logger.info(f"Porta {porta} não está disponível: {e}")
    
    logger.error("Nenhuma porta disponível encontrada")
    return {"erro": "Nenhuma porta disponível"}

def analisar_mpc_agent_communication():
    """Analisa o código do módulo mpc_agent_communication"""
    try:
        import inspect
        from core_inteligente.mpc_agent_communication import send_agent_command
        
        logger.info("Analisando implementação de send_agent_command...")
        
        # Obter o código fonte da função
        source = inspect.getsource(send_agent_command)
        logger.info(f"Código da função send_agent_command:\n{source}")
        
        # Verificar a configuração carregada
        from core_inteligente.mpc_agent_communication import MPCAgentCommunication
        comm = MPCAgentCommunication()
        logger.info(f"URL base configurada: {comm.base_url}")
        logger.info(f"Timeout configurado: {comm.timeout}")
        logger.info(f"Agentes configurados: {[a.get('id') for a in comm.agents]}")
        
        return {
            "base_url": comm.base_url,
            "timeout": comm.timeout,
            "agents": [a.get("id") for a in comm.agents if a.get("enabled", True)]
        }
        
    except Exception as e:
        logger.error(f"Erro ao analisar módulo: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"erro": str(e)}

async def main():
    """Função principal"""
    logger.info("=== Iniciando testes de comunicação com Agno ===")
    
    # Executar os testes
    logger.info("\n=== Testando método verificar_status ===")
    resultado_metodo = await testar_metodo_verificar_status()
    
    logger.info("\n=== Testando requisição HTTP direta ===")
    resultado_http = testar_requisicao_direta()
    
    logger.info("\n=== Analisando módulo de comunicação ===")
    resultado_analise = analisar_mpc_agent_communication()
    
    # Comparar resultados
    logger.info("\n=== Comparando resultados ===")
    
    metodo_ok = not resultado_metodo.get("erro", False)
    http_ok = not resultado_http.get("erro", False)
    
    logger.info(f"Método verificar_status: {'✅ OK' if metodo_ok else '❌ Falhou'}")
    logger.info(f"Requisição HTTP direta: {'✅ OK' if http_ok else '❌ Falhou'}")
    
    if metodo_ok != http_ok:
        if metodo_ok and not http_ok:
            logger.warning("⚠️ O método verificar_status funciona, mas a requisição HTTP direta falha.")
            logger.warning("Isso é incomum, pois o método utiliza internamente uma requisição HTTP.")
        elif http_ok and not metodo_ok:
            logger.warning("⚠️ A requisição HTTP direta funciona, mas o método verificar_status falha.")
            logger.warning("Isso sugere um problema na implementação do método verificar_status ou nas camadas intermediárias.")
    
    # Conclusão e recomendações
    logger.info("\n=== Conclusão ===")
    
    if metodo_ok and http_ok:
        logger.info("✅ Ambos os métodos de comunicação estão funcionando corretamente.")
        logger.info("Se você ainda está enfrentando problemas, verifique os parâmetros específicos sendo passados nas chamadas reais.")
    elif not metodo_ok and not http_ok:
        logger.error("❌ Ambos os métodos de comunicação estão falhando.")
        logger.error("Verifique se o servidor MPC está rodando e se o agente Agno está ativo.")
    else:
        logger.warning("⚠️ Há uma discrepância entre os métodos de comunicação.")
        logger.warning("Verifique as configurações e as mensagens de erro detalhadas acima.")
    
    # Sugestão de conserto
    if not metodo_ok or not http_ok:
        logger.info("\n=== Sugestões de conserto ===")
        logger.info("1. Verifique se o servidor MPC está rodando na porta esperada (10876)")
        logger.info("2. Confira se a configuração em config/mpc_agents.json está apontando para a URL correta")
        logger.info("3. Verifique se o agente Agno está devidamente configurado e respondendo")
        logger.info("4. Reinicie o servidor MPC se necessário")

if __name__ == "__main__":
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Executar o teste assíncrono
    asyncio.run(main())
