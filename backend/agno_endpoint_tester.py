"""
Focused test script for the /agno endpoints with detailed logging
"""
import requests
import json
import logging
import sys
import os
from pathlib import Path

# Configure logging to both file and console
log_path = Path("agno_test_log.txt")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_endpoint(url, payload=None, method="POST"):
    """Test an endpoint with detailed logging"""
    logger.info(f"Testing endpoint: {url}")
    logger.debug(f"Request method: {method}")
    if payload:
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=payload, timeout=10)
        else:  # GET
            response = requests.get(url, timeout=10)
        
        logger.info(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            logger.debug(f"Response JSON: {json.dumps(response_json, indent=2)}")
            return response.status_code, response_json
        except:
            logger.debug(f"Response text: {response.text[:500]}")
            return response.status_code, response.text
    
    except Exception as e:
        logger.error(f"Request failed with exception: {str(e)}", exc_info=True)
        return None, str(e)

def main():
    """Main test function"""
    logger.info("=" * 50)
    logger.info("AGNO ENDPOINTS TEST")
    logger.info("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Ensure server is running by checking docs endpoint
    logger.info("Checking if server is running...")
    status, response = test_endpoint(f"{base_url}/docs", method="GET")
    if status != 200:
        logger.error("Server does not appear to be running. Please start it first.")
        return
    
    logger.info("Server is running. Testing Agno endpoints...")
    
    # Test each Agno endpoint
    endpoints = {
        "/agno/corrigir": {"entidade": "sistema_backend", "acao": "verificar"},
        "/agno/playbook": {"nome": "diagnostico", "contexto": {}},
        "/agno/feedback": {"feedback": {"tipo": "verificacao", "valor": "ok"}},
        "/agno/coletar_newrelic": {"tipo": "entidades"}
    }
    
    results = {}
    for endpoint, payload in endpoints.items():
        logger.info("-" * 50)
        status, response = test_endpoint(f"{base_url}{endpoint}", payload)
        results[endpoint] = {"status": status, "response": response}
    
    # Summary
    logger.info("=" * 50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 50)
    
    success = 0
    failure = 0
    
    for endpoint, result in results.items():
        status = result["status"]
        if status == 200:
            logger.info(f"{endpoint}: SUCCESS")
            success += 1
        else:
            logger.info(f"{endpoint}: FAILURE - Status: {status}")
            failure += 1
    
    logger.info(f"Success: {success}, Failure: {failure}, Total: {len(endpoints)}")
    logger.info(f"Log file saved to: {log_path.absolute()}")

if __name__ == "__main__":
    main()
