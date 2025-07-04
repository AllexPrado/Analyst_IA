#!/usr/bin/env python3
"""
Script simples para testar o backend
"""
import requests
import json

def test_backend():
    """Testa os endpoints principais do backend"""
    base_url = "http://localhost:8000"
    
    print("=== Testando Backend ===")
    
    # Teste 1: Health check
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ Health check falhou: {e}")
    
    # Teste 2: Status
    try:
        response = requests.get(f"{base_url}/api/status", timeout=10)
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total entidades: {data.get('totalEntidades', 0)}")
    except Exception as e:
        print(f"❌ Status falhou: {e}")
    
    # Teste 3: Diagnóstico
    try:
        response = requests.get(f"{base_url}/api/diagnostico", timeout=15)
        print(f"✅ Diagnóstico: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Métricas encontradas: {len(data.get('metricas', []))}")
    except Exception as e:
        print(f"❌ Diagnóstico falhou: {e}")
    
    # Teste 4: Chat (teste pequeno)
    try:
        response = requests.post(
            f"{base_url}/api/chat", 
            json={"pergunta": "Olá, como está o sistema?"}, 
            timeout=30
        )
        print(f"✅ Chat: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Resposta: {data.get('resposta', 'N/A')[:50]}...")
        elif response.status_code == 400:
            data = response.json()
            print(f"   Erro 400: {data.get('mensagem', 'N/A')}")
    except Exception as e:
        print(f"❌ Chat falhou: {e}")
    
    print("\n=== Testes concluídos ===")

if __name__ == "__main__":
    test_backend()
