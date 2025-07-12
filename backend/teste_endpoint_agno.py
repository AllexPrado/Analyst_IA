#!/usr/bin/env python
"""
Teste simples para verificar se o endpoint /agno/corrigir está acessível
"""
import requests
import json

def test_endpoint():
    # URL do endpoint
    url = "http://localhost:8000/agno/corrigir"
    
    # Dados para enviar
    payload = {
        "entidade": "teste",
        "acao": "verificar"
    }
    
    print(f"Testando o endpoint: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Fazer a requisição
        response = requests.post(url, json=payload, timeout=10)
        
        # Exibir resultados
        print(f"Status Code: {response.status_code}")
        print(f"Resposta: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("\n✅ SUCESSO! O endpoint está funcionando corretamente!")
        else:
            print(f"\n❌ ERRO! O endpoint retornou status {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO DE CONEXÃO! Não foi possível conectar ao servidor.")
        print("Verifique se o servidor está rodando na porta 8000.")
    
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
    
    # Também testar o endpoint via /api/agno
    api_url = "http://localhost:8000/api/agno/corrigir"
    print("\n===================================")
    print(f"Testando o endpoint alternativo: {api_url}")
    
    try:
        # Fazer a requisição
        response = requests.post(api_url, json=payload, timeout=10)
        
        # Exibir resultados
        print(f"Status Code: {response.status_code}")
        print(f"Resposta: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("\n✅ SUCESSO! O endpoint alternativo está funcionando corretamente!")
        else:
            print(f"\n❌ ERRO! O endpoint alternativo retornou status {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO DE CONEXÃO! Não foi possível conectar ao servidor via caminho alternativo.")
    
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")

if __name__ == "__main__":
    test_endpoint()
