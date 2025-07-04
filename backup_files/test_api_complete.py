#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar todos os endpoints da API do Analyst-IA
"""
import requests
import json
import sys
from datetime import datetime
from pathlib import Path

# Configuração básica
BASE_URL = "http://localhost:8000/api"

def test_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Testa um endpoint específico e verifica se a resposta é válida"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Testando endpoint: {endpoint} ({method})")
    
    try:
        if method.upper() == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        elif method.upper() == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        else:
            print(f"❌ Método {method} não suportado")
            return False
        
        print(f"Status code: {response.status_code}")
        
        # Verificar status code
        if response.status_code != expected_status:
            print(f"❌ Status code inesperado: {response.status_code} (esperado: {expected_status})")
            print(f"Resposta: {response.text[:200]}...")
            return False
        
        # Verificar se a resposta é JSON válido
        try:
            resp_json = response.json()
            print(f"✅ Resposta recebida: {json.dumps(resp_json, indent=2, ensure_ascii=False)[:500]}...")
            return True
        except Exception as e:
            print(f"❌ Resposta não é JSON válido: {str(e)}")
            print(f"Resposta: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar endpoint: {str(e)}")
        return False

def run_all_tests():
    """Executa testes em todos os endpoints da API"""
    print("=" * 80)
    print(" 🧪 TESTE COMPLETO DOS ENDPOINTS DA API")
    print("=" * 80)
    
    # Lista de testes a executar
    tests = [
        # Endpoint, método, dados (se POST), status esperado
        ("/health", "GET", None, 200),
        ("/status", "GET", None, 200),
        ("/kpis", "GET", None, 200),
        ("/tendencias", "GET", None, 200),
        ("/cobertura", "GET", None, 200),
        ("/insights", "GET", None, 200),
        ("/chat", "POST", {"pergunta": "Como está o sistema?"}, 200),
    ]
    
    # Executar cada teste
    results = {}
    for endpoint, method, data, expected_status in tests:
        results[endpoint] = test_endpoint(endpoint, method, data, expected_status)
    
    # Resumo dos resultados
    print("\n" + "=" * 80)
    print(" RESUMO DOS TESTES")
    print("=" * 80)
    
    all_passed = True
    for endpoint, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{status} - {endpoint}")
        if not passed:
            all_passed = False
    
    # Resultado final
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
    print("=" * 80)

if __name__ == "__main__":
    run_all_tests()
