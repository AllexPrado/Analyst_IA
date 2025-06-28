#!/usr/bin/env python3
"""
Teste de problemas do frontend
"""
import requests
import json

def test_frontend_errors():
    """Testa se os endpoints retornam dados adequados para o frontend"""
    
    print("🔍 Testando backend para diagnóstico de problemas do frontend...")
    
    # Testa diagnóstico
    try:
        print("\n📊 Testando endpoint /api/diagnostico")
        response = requests.get("http://localhost:8000/api/diagnostico", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status 200")
            
            # Verifica estrutura
            if isinstance(data, dict):
                print(f"   📋 Estrutura:")
                print(f"      - Tipo: {type(data)}")
                
                if 'metricas' in data:
                    metricas = data['metricas']
                    print(f"      - Métricas: {type(metricas)} com {len(metricas) if metricas else 0} itens")
                    
                    if metricas and len(metricas) > 0:
                        primeiro_item = metricas[0]
                        print(f"      - Primeiro item: {type(primeiro_item)}")
                        if isinstance(primeiro_item, dict):
                            print(f"        - Campos: {list(primeiro_item.keys())}")
                            print(f"        - Entidade: {primeiro_item.get('entidade', 'N/A')}")
                            print(f"        - Valor: {primeiro_item.get('valor', 'N/A')} ({type(primeiro_item.get('valor'))})")
                        else:
                            print(f"        - PROBLEMA: Item não é dict!")
                    else:
                        print(f"      - ⚠️ PROBLEMA: Lista de métricas está vazia!")
                else:
                    print(f"      - ⚠️ PROBLEMA: Campo 'metricas' não encontrado!")
                    print(f"      - Campos presentes: {list(data.keys())}")
                
                # Verifica outros campos importantes
                for campo in ['explicacao', 'impacto', 'recomendacao_tecnica', 'recomendacao_executiva']:
                    if campo in data:
                        valor = data[campo]
                        print(f"      - {campo}: {type(valor)} ({'vazio' if not valor else 'ok'})")
                    else:
                        print(f"      - {campo}: AUSENTE")
            else:
                print(f"   ❌ PROBLEMA: Resposta não é dict, é {type(data)}")
        else:
            print(f"   ❌ Status {response.status_code}")
            print(f"   Erro: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Testa health
    try:
        print("\n🏥 Testando endpoint /api/health")
        response = requests.get("http://localhost:8000/api/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status 200")
            print(f"   Health: {data}")
        else:
            print(f"   ❌ Status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Testa status
    try:
        print("\n📈 Testando endpoint /api/status")
        response = requests.get("http://localhost:8000/api/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status 200")
            
            if isinstance(data, dict):
                print(f"   Campos: {list(data.keys())}")
                entidades = data.get('entidades', 'N/A')
                print(f"   Entidades: {entidades} ({type(entidades)})")
            else:
                print(f"   ❌ PROBLEMA: Resposta não é dict")
        else:
            print(f"   ❌ Status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

if __name__ == "__main__":
    test_frontend_errors()
