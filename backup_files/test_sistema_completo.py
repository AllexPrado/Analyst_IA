#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar todos os componentes do sistema Analyst_IA
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuração
BASE_URL = "http://localhost:8000/api"
TEST_LOG = Path(__file__).parent / "test_results.json"

def print_header(title):
    """Imprime um cabeçalho formatado"""
    print("=" * 80)
    print(f" {title}")
    print("=" * 80)

def test_backend_health():
    """Testa o endpoint de saúde do sistema"""
    print_header("TESTANDO SAÚDE DO SISTEMA")
    
    url = f"{BASE_URL}/health"
    print(f"GET {url}")
    
    try:
        response = requests.get(url, timeout=5)
        status_code = response.status_code
        
        if status_code == 200:
            print("✅ Servidor backend está operacional")
            try:
                data = response.json()
                print(f"Resposta: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            except Exception as e:
                print(f"❌ Erro ao processar resposta: {e}")
                return False
        else:
            print(f"❌ Servidor retornou status {status_code}")
            print(f"Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar ao servidor: {e}")
        return False

def test_endpoints():
    """Testa todos os endpoints principais da API"""
    print_header("TESTANDO ENDPOINTS PRINCIPAIS")
    
    endpoints = [
        ("/status", "GET", None),
        ("/kpis", "GET", None),
        ("/cobertura", "GET", None),
        ("/tendencias", "GET", None),
        ("/insights", "GET", None),
        ("/chat", "POST", {"pergunta": "Como está o sistema?"})
    ]
    
    results = []
    
    for path, method, data in endpoints:
        url = f"{BASE_URL}{path}"
        print(f"\nTestando {method} {path}")
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            else:  # POST
                response = requests.post(url, json=data, timeout=15)
                
            status_code = response.status_code
            print(f"Status: {status_code}")
            
            if status_code == 200:
                print("✅ Sucesso")
                try:
                    data = response.json()
                    # Mostrar uma prévia dos dados (limitada para não sobrecarregar o console)
                    data_preview = json.dumps(data, indent=2, ensure_ascii=False)
                    if len(data_preview) > 500:
                        data_preview = data_preview[:500] + "..."
                    print(f"Dados: {data_preview}")
                    
                    results.append({
                        "endpoint": path,
                        "method": method,
                        "success": True,
                        "status_code": status_code,
                    })
                except Exception as e:
                    print(f"❌ Erro ao processar resposta JSON: {e}")
                    results.append({
                        "endpoint": path,
                        "method": method,
                        "success": False,
                        "status_code": status_code,
                        "error": f"Erro ao processar JSON: {str(e)}"
                    })
            else:
                print(f"❌ Falha - Status {status_code}")
                print(f"Resposta: {response.text}")
                results.append({
                    "endpoint": path,
                    "method": method,
                    "success": False,
                    "status_code": status_code,
                    "error": response.text
                })
        except Exception as e:
            print(f"❌ Erro ao fazer requisição: {e}")
            results.append({
                "endpoint": path,
                "method": method,
                "success": False,
                "error": str(e)
            })
    
    # Resumo dos resultados
    success_count = sum(1 for r in results if r.get("success", False))
    print(f"\n{success_count}/{len(endpoints)} endpoints funcionando corretamente")
    
    return results

def test_chat_conversation():
    """Testa uma conversa completa com o endpoint de chat"""
    print_header("TESTANDO CONVERSA COM CHAT")
    
    url = f"{BASE_URL}/chat"
    perguntas = [
        "Como está o sistema?",
        "Quais são as métricas mais importantes?",
        "Algum problema de performance?",
        "Qual é o status da infraestrutura?"
    ]
    
    for i, pergunta in enumerate(perguntas, 1):
        print(f"\nPergunta {i}: '{pergunta}'")
        
        try:
            response = requests.post(url, json={"pergunta": pergunta}, timeout=15)
            
            if response.status_code == 200:
                print("✅ Resposta recebida")
                try:
                    data = response.json()
                    print(f"Resposta: {data.get('resposta', 'Sem resposta')}")
                except Exception as e:
                    print(f"❌ Erro ao processar resposta: {e}")
            else:
                print(f"❌ Erro - Status {response.status_code}")
                print(f"Resposta: {response.text}")
        except Exception as e:
            print(f"❌ Erro ao fazer requisição: {e}")
    
    print("\n✅ Teste de conversa concluído")

def save_test_results(results):
    """Salva os resultados do teste em um arquivo JSON"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "results": results
    }
    
    with open(TEST_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\nResultados salvos em: {TEST_LOG}")

def main():
    """Função principal que executa todos os testes"""
    print_header("TESTES DO SISTEMA ANALYST_IA")
    print(f"Data e hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar se o backend está rodando
    if not test_backend_health():
        print("\n❌ Servidor backend não está respondendo. Abortando testes.")
        sys.exit(1)
    
    # Testar endpoints principais
    endpoint_results = test_endpoints()
    
    # Testar conversa com o chat
    test_chat_conversation()
    
    # Salvar resultados
    save_test_results(endpoint_results)
    
    print_header("TESTES CONCLUÍDOS")

if __name__ == "__main__":
    main()
