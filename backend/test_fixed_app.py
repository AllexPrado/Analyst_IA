"""
Test script specifically for the fixed application structure.
"""
import requests
import json
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_endpoint(url, payload=None, method="POST"):
    """Test an endpoint with detailed logging"""
    logger.info(f"Testing: {url}")
    if payload:
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=payload, timeout=10)
        else:  # GET
            response = requests.get(url, timeout=10)
        
        logger.info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                response_json = response.json()
                logger.info(f"Response (truncated): {json.dumps(response_json, indent=2)[:100]}...")
            except:
                logger.info(f"Response (truncated): {response.text[:100]}...")
        else:
            logger.warning(f"Failed with status {response.status_code}")
            logger.debug(f"Response: {response.text[:200]}")
        
        return response.status_code
    
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        return None

def main():
    """Main test function"""
    logger.info("=" * 50)
    logger.info("TESTING FIXED APP ENDPOINTS")
    logger.info("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Verify server is running
    docs_status = test_endpoint(f"{base_url}/docs", method="GET")
    if docs_status != 200:
        logger.error("Server does not appear to be running!")
        return
    
    logger.info("\nTesting API endpoints...")
    test_endpoint(f"{base_url}/api/agno/corrigir", {"entidade": "sistema_backend", "acao": "verificar"})
    test_endpoint(f"{base_url}/api/agno/playbook", {"nome": "diagnostico", "contexto": {}})
    test_endpoint(f"{base_url}/api/agno/feedback", {"feedback": {"tipo": "verificacao", "valor": "ok"}})
    test_endpoint(f"{base_url}/api/agno/coletar_newrelic", {"tipo": "entidades"})
    
    logger.info("\nTesting direct agno endpoints (these may fail depending on app setup)...")
    test_endpoint(f"{base_url}/agno/corrigir", {"entidade": "sistema_backend", "acao": "verificar"})
    test_endpoint(f"{base_url}/agno/playbook", {"nome": "diagnostico", "contexto": {}})
    
    logger.info("\nTest complete!")

if __name__ == "__main__":
    main()
