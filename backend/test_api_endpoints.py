#!/usr/bin/env python3
"""
Script para testar os endpoints da API do Analyst-IA
"""

import requests
import json
from datetime import datetime
import sys
import os
from pathlib import Path

# Configuração
BASE_URL = "http://localhost:8000/api"
ENDPOINTS = [
    {"url": "/health", "method": "GET", "name": "Saúde do sistema"},
    {"url": "/status", "method": "GET", "name": "Status do sistema"},
    {"url": "/kpis", "method": "GET", "name": "KPIs"},
    {"url": "/tendencias", "method": "GET", "name": "Tendências"},
    {"url": "/cobertura", "method": "GET", "name": "Cobertura"},
    {"url": "/insights", "method": "GET", "name": "Insights"},
    {"url": "/chat", "method": "POST", "name": "Chat", "data": {"pergunta": "Como está o sistema?"}}
]

def test_endpoint(endpoint_info):
    """Testa um endpoint específico da API"""
    url = BASE_URL + endpoint_info["url"]
    method = endpoint_info["method"]
    name = endpoint_info["name"]
    data = endpoint_info.get("data")
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Testando endpoint: {name} ({url})")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ Método não suportado: {method}")
            return False
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Conexão bem-sucedida")
            try:
                data = response.json()
                # Mostrar apenas parte da resposta para não sobrecarregar o console
                response_excerpt = json.dumps(data, indent=2, ensure_ascii=False)
                if len(response_excerpt) > 500:
                    response_excerpt = response_excerpt[:500] + "..."
                print(f"Resposta: {response_excerpt}")
                print("✅ Resposta JSON válida")
                return True
            except json.JSONDecodeError:
                print(f"❌ Resposta não é um JSON válido: {response.text[:200]}...")
                return False
        else:
            print(f"❌ Status code inesperado: {response.status_code}")
            print(f"Resposta: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar endpoint: {str(e)}")
        return False

def test_all_endpoints():
    """Testa todos os endpoints configurados"""
    print("=" * 80)
    print(" 🧪 TESTE DE TODOS OS ENDPOINTS DA API")
    print("=" * 80)
    
    results = []
    for endpoint in ENDPOINTS:
        success = test_endpoint(endpoint)
        results.append({
            "endpoint": endpoint["name"],
            "success": success
        })
    
    # Resumo dos resultados
    print("\n" + "=" * 80)
    print(" 📊 RESUMO DOS TESTES")
    print("=" * 80)
    
    total_success = sum(1 for r in results if r["success"])
    
    print(f"Total de endpoints testados: {len(results)}")
    print(f"Endpoints funcionando: {total_success}")
    print(f"Endpoints com falha: {len(results) - total_success}")
    
    # Listar falhas
    if len(results) - total_success > 0:
        print("\nEndpoints com falha:")
        for result in results:
            if not result["success"]:
                print(f"- {result['endpoint']}")
    
    print("=" * 80)
    return total_success == len(results)

if __name__ == "__main__":
    success = test_all_endpoints()
    sys.exit(0 if success else 1)
