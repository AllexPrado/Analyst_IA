"""
Simple HTTP request test for the /agno endpoints
"""
import requests

def test_endpoint(url, payload=None):
    """Test an endpoint with an optional payload"""
    print(f"Testing URL: {url}")
    try:
        if payload:
            response = requests.post(url, json=payload)
        else:
            response = requests.get(url)
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.text[:200]}...")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

# Test Agno endpoints
print("=== Testing Agno Endpoints ===")
test_endpoint("http://localhost:8000/agno/corrigir", {"entidade": "sistema_backend", "acao": "verificar"})
test_endpoint("http://localhost:8000/agno/playbook", {"nome": "diagnostico", "contexto": {}})
test_endpoint("http://localhost:8000/agno/feedback", {"feedback": {"tipo": "verificacao", "valor": "ok"}})
test_endpoint("http://localhost:8000/agno/coletar_newrelic", {"tipo": "entidades"})

# Test API endpoints for comparison
print("\n=== Testing API Endpoints ===")
test_endpoint("http://localhost:8000/api/healthcheck")
test_endpoint("http://localhost:8000/docs")  # OpenAPI documentation

print("=== Tests Completed ===")
