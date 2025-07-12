"""
Script para testar os endpoints do Agno de forma simples
"""
import requests
import json
import sys
from datetime import datetime

# Configuração
BASE_URL = "http://localhost:8000"
ENDPOINTS = {
    "/agno/corrigir": {"entidade": "sistema_teste", "acao": "verificar"},
    "/agno/playbook": {"nome": "diagnostico", "contexto": {}},
    "/agno/feedback": {"feedback": {"tipo": "teste", "valor": "ok"}},
    "/agno/coletar_newrelic": {"entidade": "sistema", "periodo": "3d", "tipo": "metricas"},
    "/api/agno/corrigir": {"entidade": "sistema_teste", "acao": "verificar"},
    "/api/agno/playbook": {"nome": "diagnostico", "contexto": {}},
    "/api/agno/feedback": {"feedback": {"tipo": "teste", "valor": "ok"}},
    "/api/agno/coletar_newrelic": {"entidade": "sistema", "periodo": "3d", "tipo": "metricas"}
}

def test_endpoint(endpoint, payload):
    """Testa um endpoint específico"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\nTestando {url}...")
    try:
        response = requests.post(url, json=payload, timeout=10.0)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Sucesso! Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)[:150]}...")
            return True
        else:
            print(f"Falha! Erro: {response.text}")
            return False
    except Exception as e:
        print(f"Erro na requisição: {str(e)}")
        return False

def main():
    """Função principal para testar todos os endpoints"""
    print("=" * 60)
    print("TESTE DE ENDPOINTS AGNO")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    success = 0
    failures = 0
    
    for endpoint, payload in ENDPOINTS.items():
        if test_endpoint(endpoint, payload):
            success += 1
        else:
            failures += 1
    
    print("\n" + "=" * 60)
    print(f"Total de endpoints testados: {len(ENDPOINTS)}")
    print(f"Sucessos: {success}")
    print(f"Falhas: {failures}")
    
    if failures == 0:
        print("\nTodos os endpoints estão funcionando corretamente!")
        return 0
    else:
        print(f"\nAlguns endpoints ({failures}) não estão funcionando corretamente.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
