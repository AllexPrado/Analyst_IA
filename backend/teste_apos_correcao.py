#!/usr/bin/env python
"""
Script para testar rapidamente os endpoints do Agno após a correção
"""
import requests
import json
import time
import sys

def test_endpoints():
    """Testa os endpoints do Agno em ambos os caminhos"""
    
    # Base URLs
    base_urls = [
        "http://localhost:8000/agno",
        "http://localhost:8000/api/agno"
    ]
    
    # Endpoints para testar
    endpoints = [
        "corrigir",
        "playbook",
        "feedback",
        "coletar_newrelic"
    ]
    
    # Payloads para os testes
    payloads = {
        "corrigir": {"entidade": "teste", "acao": "verificar"},
        "playbook": {"nome": "diagnostico", "contexto": {}},
        "feedback": {"feedback": {"tipo": "teste", "valor": "ok"}},
        "coletar_newrelic": {"entidade": "sistema", "periodo": "3d", "tipo": "metricas"}
    }
    
    # Resultados
    results = {
        "success": [],
        "failure": []
    }
    
    print("\n=====================================================")
    print("TESTE RÁPIDO DOS ENDPOINTS AGNO APÓS CORREÇÃO")
    print("=====================================================\n")
    
    # Testar cada combinação de base URL e endpoint
    for base_url in base_urls:
        print(f"\nTestando endpoints em {base_url}:")
        print("-----------------------------------------------------")
        
        for endpoint in endpoints:
            url = f"{base_url}/{endpoint}"
            payload = payloads.get(endpoint, {})
            
            print(f"  {url} ... ", end="", flush=True)
            
            try:
                response = requests.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    print("✓ OK (200)")
                    results["success"].append(url)
                else:
                    print(f"✗ ERRO ({response.status_code})")
                    results["failure"].append(f"{url} - Status {response.status_code}")
                
            except requests.exceptions.ConnectionError:
                print("✗ ERRO DE CONEXÃO")
                results["failure"].append(f"{url} - Erro de conexão")
                
            except Exception as e:
                print(f"✗ ERRO: {str(e)}")
                results["failure"].append(f"{url} - {str(e)}")
    
    # Resumo dos resultados
    print("\n=====================================================")
    print("RESUMO DOS TESTES")
    print("=====================================================")
    print(f"Total de endpoints testados: {len(base_urls) * len(endpoints)}")
    print(f"Sucessos: {len(results['success'])}")
    print(f"Falhas: {len(results['failure'])}")
    
    if results['failure']:
        print("\nEndpoints com falha:")
        for failure in results['failure']:
            print(f"  - {failure}")
    
    if len(results['success']) == len(base_urls) * len(endpoints):
        print("\n✅ SUCESSO! Todos os endpoints estão funcionando corretamente!")
    else:
        print("\n❌ ALERTA! Alguns endpoints não estão funcionando corretamente.")
    
    return results

if __name__ == "__main__":
    # Esperar um momento para o servidor iniciar/aplicar mudanças
    print("Aguardando o servidor inicializar completamente (5 segundos)...")
    time.sleep(5)
    
    # Executar os testes
    test_endpoints()
