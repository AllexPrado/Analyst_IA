#!/usr/bin/env python
"""
Teste de múltiplos endpoints do /agno
"""
import requests
import json
import sys
import time

def test_endpoint(url, payload, description):
    print(f"\n=== Testando {description} ===")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCESSO!")
            try:
                resp_json = response.json()
                print(json.dumps(resp_json, indent=2))
            except:
                print(response.text[:500])
            return True
        else:
            print(f"ERRO: {response.text}")
            return False
            
    except Exception as e:
        print(f"EXCEÇÃO: {str(e)}")
        return False
        
def main():
    base_url = "http://localhost:8000"
    endpoints = [
        {
            "url": f"{base_url}/agno/corrigir",
            "payload": {"entidade": "teste", "acao": "corrigir"},
            "description": "Endpoint /agno/corrigir"
        },
        {
            "url": f"{base_url}/api/agno/corrigir",
            "payload": {"entidade": "teste", "acao": "corrigir"},
            "description": "Endpoint /api/agno/corrigir"
        },
        {
            "url": f"{base_url}/agno/feedback",
            "payload": {"feedback": {"tipo": "teste", "mensagem": "teste"}},
            "description": "Endpoint /agno/feedback"
        },
        {
            "url": f"{base_url}/api/agno/feedback",
            "payload": {"feedback": {"tipo": "teste", "mensagem": "teste"}},
            "description": "Endpoint /api/agno/feedback"
        }
    ]
    
    results = []
    
    for endpoint in endpoints:
        result = test_endpoint(endpoint["url"], endpoint["payload"], endpoint["description"])
        results.append({
            "endpoint": endpoint["url"],
            "success": result
        })
        time.sleep(1)  # Pausa breve entre requisições
    
    print("\n=== RESUMO DOS RESULTADOS ===")
    all_success = True
    for result in results:
        status = "✅ SUCESSO" if result["success"] else "❌ FALHA"
        print(f"{status}: {result['endpoint']}")
        if not result["success"]:
            all_success = False
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())
