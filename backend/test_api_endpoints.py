"""
Script para verificar se o backend do Analyst IA está funcionando corretamente.
Testa endpoints específicos e mostra resultados.
"""
import requests
import time
import logging
import sys
import json
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Configurações
BASE_URL = "http://127.0.0.1:8000"
ENDPOINTS = [
    "/api/status",
    "/api/agno/status",
    "/api/entidades",
    "/api/kpis",
    "/api/insights"
]
MAX_RETRIES = 3
RETRY_DELAY = 2

def test_endpoint(url, endpoint, retries=MAX_RETRIES):
    """Testa um endpoint específico e retorna o resultado."""
    full_url = f"{url}{endpoint}"
    
    for attempt in range(1, retries + 1):
        logger.info(f"Testando endpoint: {full_url} (tentativa {attempt}/{retries})")
        
        try:
            response = requests.get(full_url, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"✅ Endpoint {endpoint} está acessível (status: {response.status_code})")
                # Mostrar apenas parte da resposta para evitar saída muito grande
                resp_text = response.text[:100] + "..." if len(response.text) > 100 else response.text
                logger.info(f"Resposta: {resp_text}")
                return True
            else:
                logger.warning(f"❌ Endpoint {endpoint} retornou status {response.status_code}")
                logger.warning(f"Resposta: {response.text[:100]}...")
                
                if attempt < retries:
                    logger.info(f"Aguardando {RETRY_DELAY} segundos antes de tentar novamente...")
                    time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.error(f"❌ Erro ao acessar {endpoint}: {e}")
            
            if attempt < retries:
                logger.info(f"Aguardando {RETRY_DELAY} segundos antes de tentar novamente...")
                time.sleep(RETRY_DELAY)
    
    return False

def main():
    """Função principal para testar endpoints do backend."""
    logger.info("=" * 80)
    logger.info("INICIANDO TESTES DOS ENDPOINTS DO BACKEND")
    logger.info("=" * 80)
    
    results = {}
    
    for endpoint in ENDPOINTS:
        results[endpoint] = test_endpoint(BASE_URL, endpoint)
    
    # Resumo dos testes
    logger.info("\nRESUMO DOS TESTES:")
    logger.info("-" * 40)
    
    successful = 0
    for endpoint, success in results.items():
        status = "✅ SUCESSO" if success else "❌ FALHA"
        logger.info(f"{endpoint}: {status}")
        if success:
            successful += 1
    
    logger.info("-" * 40)
    logger.info(f"Total de endpoints testados: {len(ENDPOINTS)}")
    logger.info(f"Endpoints acessíveis: {successful}")
    logger.info(f"Endpoints com falha: {len(ENDPOINTS) - successful}")
    
    # Status final
    if successful == len(ENDPOINTS):
        logger.info("\n✅ TODOS OS ENDPOINTS ESTÃO FUNCIONANDO CORRETAMENTE")
    else:
        logger.warning(f"\n⚠️ {len(ENDPOINTS) - successful} ENDPOINT(S) COM PROBLEMAS")
    
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
