#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar os endpoints da API
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_health():
    """Testa o endpoint de saúde do sistema"""
    url = f"{BASE_URL}/health"
    print(f"Testando GET {url}")
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_chat():
    """Testa o endpoint de chat"""
    url = f"{BASE_URL}/chat"
    data = {"pergunta": "Como está o desempenho do sistema?"}
    print(f"Testando POST {url}")
    print(f"Dados: {json.dumps(data, ensure_ascii=False)}")
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_kpis():
    """Testa o endpoint de KPIs"""
    url = f"{BASE_URL}/kpis"
    print(f"Testando GET {url}")
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_cobertura():
    """Testa o endpoint de cobertura"""
    url = f"{BASE_URL}/cobertura"
    print(f"Testando GET {url}")
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_tendencias():
    """Testa o endpoint de tendências"""
    url = f"{BASE_URL}/tendencias"
    print(f"Testando GET {url}")
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_insights():
    """Testa o endpoint de insights"""
    url = f"{BASE_URL}/insights"
    print(f"Testando GET {url}")
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False

def run_all_tests():
    """Executa todos os testes"""
    print("=" * 50)
    print("INICIANDO TESTES DE API")
    print("=" * 50)
    
    tests = [
        ("Health", test_health),
        ("KPIs", test_kpis),
        ("Cobertura", test_cobertura),
        ("Tendências", test_tendencias),
        ("Insights", test_insights),
        ("Chat", test_chat)
    ]
    
    results = []
    
    for name, test_func in tests:
        print("\n" + "=" * 50)
        print(f"Testando endpoint: {name}")
        print("-" * 50)
        success = test_func()
        results.append((name, success))
        print("-" * 50)
        print(f"Resultado: {'✅ SUCESSO' if success else '❌ FALHA'}")
    
    print("\n" + "=" * 50)
    print("RESUMO DOS TESTES")
    print("-" * 50)
    
    all_passed = True
    for name, success in results:
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"{name}: {status}")
        if not success:
            all_passed = False
    
    print("-" * 50)
    print(f"Resultado final: {'✅ TODOS OS TESTES PASSARAM' if all_passed else '❌ ALGUNS TESTES FALHARAM'}")
    print("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    # Se receber argumentos, teste apenas os endpoints especificados
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == "health":
                test_health()
            elif arg == "kpis":
                test_kpis()
            elif arg == "cobertura":
                test_cobertura()
            elif arg == "tendencias":
                test_tendencias()
            elif arg == "insights":
                test_insights()
            elif arg == "chat":
                test_chat()
            else:
                print(f"Endpoint desconhecido: {arg}")
    else:
        # Se não houver argumentos, execute todos os testes
        run_all_tests()
