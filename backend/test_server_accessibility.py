"""
Script para testar se o servidor backend está acessível.
Realiza uma solicitação HTTP para o endpoint /api/status.
"""
import requests
import sys
import time
import json
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def test_server(url="http://127.0.0.1:8000", max_retries=3, retry_delay=2):
    """Testa se o servidor está acessível fazendo uma solicitação HTTP"""
    endpoints = [
        "/api/status",
        "/logs",
        "/entidades"
    ]
    
    for endpoint in endpoints:
        full_url = f"{url}{endpoint}"
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Testando endpoint: {full_url} (tentativa {attempt}/{max_retries})")
                response = requests.get(full_url, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"✅ Endpoint {endpoint} está acessível (status: {response.status_code})")
                    try:
                        data = response.json()
                        logger.info(f"Resposta: {json.dumps(data, indent=2, ensure_ascii=False)[:100]}...")
                    except Exception:
                        logger.info(f"Resposta não é JSON válido: {response.text[:100]}...")
                    
                    # Se um endpoint funcionou, podemos considerar que o servidor está rodando
                    break
                else:
                    logger.warning(f"❌ Endpoint {endpoint} retornou status {response.status_code}")
                    logger.warning(f"Resposta: {response.text[:100]}...")
                    
                    if attempt < max_retries:
                        logger.info(f"Aguardando {retry_delay} segundos antes de tentar novamente...")
                        time.sleep(retry_delay)
            except requests.exceptions.ConnectionError:
                logger.warning(f"❌ Não foi possível conectar ao servidor em {full_url}")
                if attempt < max_retries:
                    logger.info(f"Aguardando {retry_delay} segundos antes de tentar novamente...")
                    time.sleep(retry_delay)
            except Exception as e:
                logger.error(f"❌ Erro ao testar servidor: {e}")
                if attempt < max_retries:
                    logger.info(f"Aguardando {retry_delay} segundos antes de tentar novamente...")
                    time.sleep(retry_delay)

def main():
    """Função principal"""
    logger.info("Testando acessibilidade do servidor backend...")
    test_server()
    logger.info("Teste concluído")

if __name__ == "__main__":
    main()
