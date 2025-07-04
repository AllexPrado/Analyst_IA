#!/usr/bin/env python3
"""
Teste específico para validar o endpoint de chat do backend.
"""

import requests
import json
import sys
import os

# Adiciona o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_chat_endpoint():
    """Testa o endpoint de chat com diferentes tipos de pergunta."""
    
    base_url = "http://localhost:8000"
    
    # Testa se o backend está rodando
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code != 200:
            print("❌ Backend não está rodando. Execute: python backend/main.py")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend não está rodando. Execute: python backend/main.py")
        return False
    
    print("✅ Backend está rodando")
    
    # Testes de diferentes tipos de pergunta
    test_cases = [
        {
            "name": "Mensagem inicial",
            "pergunta": "mensagem_inicial",
            "expected_no_error": True
        },
        {
            "name": "Pergunta simples",
            "pergunta": "Como está o status das aplicações?",
            "expected_no_error": True
        },
        {
            "name": "Pergunta técnica",
            "pergunta": "Quais são as principais métricas de performance das minhas aplicações APM?",
            "expected_no_error": True
        },
        {
            "name": "Pergunta de troubleshooting",
            "pergunta": "Existe algum problema de performance ou erro crítico que precisa de atenção imediata?",
            "expected_no_error": True
        }
    ]
    
    success_count = 0
    
    for test in test_cases:
        print(f"\n🧪 Testando: {test['name']}")
        print(f"   Pergunta: {test['pergunta']}")
        
        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json={"pergunta": test['pergunta']},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "resposta" in data and data["resposta"]:
                    print(f"   ✅ Sucesso! Resposta recebida ({len(data['resposta'])} chars)")
                    success_count += 1
                else:
                    print(f"   ❌ Resposta vazia ou malformada")
            else:
                print(f"   ❌ Erro HTTP {response.status_code}: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout - pode estar processando")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print(f"\n📊 RESULTADO: {success_count}/{len(test_cases)} testes passaram")
    
    if success_count == len(test_cases):
        print("🎉 TODOS OS TESTES PASSARAM! O backend está funcionando corretamente.")
        return True
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs do backend.")
        return False

if __name__ == "__main__":
    print("🔧 Testando endpoint de chat do backend...")
    print("=" * 60)
    
    success = test_chat_endpoint()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
