"""
Utility script to test the availability and functionality of Agno endpoints
"""
import asyncio
import httpx
import sys
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def test_agno_endpoints():
    """Test all Agno endpoints to verify they are working correctly"""
    test_payloads = {
        "/agno/corrigir": {"entidade": "sistema_backend", "acao": "verificar"},
        "/agno/playbook": {"nome": "diagnostico", "contexto": {}},
        "/agno/feedback": {"feedback": {"tipo": "verificacao", "valor": "ok"}},
        "/agno/coletar_newrelic": {"tipo": "entidades"}
    }
    
    # Log test header
    logger.info("=" * 50)
    logger.info("TESTE DE ENDPOINTS AGNO")
    logger.info("=" * 50)
    
    base_url = "http://localhost:8000"
    result = {"success": 0, "error": 0, "total": len(test_payloads)}
    
    async with httpx.AsyncClient(timeout=30) as client:
        for endpoint, payload in test_payloads.items():
            try:
                full_url = f"{base_url}{endpoint}"
                logger.info(f"TESTANDO: {endpoint}")
                logger.info(f"URL: {full_url}")
                logger.info(f"PAYLOAD: {json.dumps(payload, ensure_ascii=False)}")
                
                response = await client.post(full_url, json=payload)
                logger.info(f"STATUS: {response.status_code}")
                
                if response.status_code == 404:
                    logger.error(f"FALHA: Erro 404 - Endpoint não encontrado")
                    result["error"] += 1
                elif response.status_code >= 400:
                    logger.error(f"FALHA: Erro {response.status_code} - {response.text}")
                    result["error"] += 1
                else:
                    logger.info(f"SUCESSO: {response.status_code}")
                    try:
                        logger.info(f"RESPOSTA: {json.dumps(response.json(), ensure_ascii=False, indent=2)[:300]}...")
                    except:
                        logger.info(f"RESPOSTA: {response.text[:300]}...")
                    result["success"] += 1
            except Exception as e:
                logger.error(f"EXCEÇÃO: {str(e)}")
                result["error"] += 1
            
            logger.info("-" * 50)
    
    # Log summary
    logger.info("=" * 50)
    logger.info(f"RESULTADO FINAL: {result['success']} sucesso, {result['error']} erro, {result['total']} total")
    logger.info("=" * 50)
    
    return result

if __name__ == "__main__":
    asyncio.run(test_agno_endpoints())
