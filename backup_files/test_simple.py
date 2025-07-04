#!/usr/bin/env python3
"""
Teste simples do sistema New Relic
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Adiciona o diretório backend ao path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

def test_imports():
    """Testa se os imports funcionam"""
    print("=== TESTE DE IMPORTS ===")
    
    try:
        from utils.newrelic_collector import rate_controller
        print("✅ rate_controller importado com sucesso")
        print(f"   Estado inicial: {rate_controller.__dict__}")
    except Exception as e:
        print(f"❌ Erro ao importar rate_controller: {e}")
        return False
    
    try:
        from utils.newrelic_collector import executar_nrql_graphql
        print("✅ executar_nrql_graphql importado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao importar executar_nrql_graphql: {e}")
        return False
    
    try:
        from utils.newrelic_collector import buscar_todas_entidades
        print("✅ buscar_todas_entidades importado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao importar buscar_todas_entidades: {e}")
        return False
        
    return True

async def test_basic_connection():
    """Testa conexão básica com New Relic"""
    print("\n=== TESTE DE CONEXÃO ===")
    
    load_dotenv()
    api_key = os.getenv('NEW_RELIC_API_KEY')
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
    
    if not api_key or not account_id:
        print("❌ Credenciais não configuradas")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...")
    print(f"✅ Account ID: {account_id}")
    
    try:
        from utils.newrelic_collector import executar_nrql_graphql
        import aiohttp
        
        # Query simples para testar conectividade
        query = "SELECT count(*) FROM Transaction SINCE 1 hour ago LIMIT 1"
        print(f"Executando query: {query}")
        
        async with aiohttp.ClientSession() as session:
            result = await executar_nrql_graphql(session, query)
            
        if result:
            print(f"✅ Conexão OK! Resultado: {result}")
            return True
        else:
            print("⚠️  Conexão OK mas sem resultados")
            return True
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

async def test_rate_controller():
    """Testa o rate controller"""
    print("\n=== TESTE DO RATE CONTROLLER ===")
    
    try:
        from utils.newrelic_collector import rate_controller
        
        print("Status inicial do rate controller:")
        if hasattr(rate_controller, 'get_status'):
            status = rate_controller.get_status()
            print(f"  Status: {status}")
        else:
            print(f"  Estado: {rate_controller.__dict__}")
        
        # Testa o método wait_if_needed
        print("Testando wait_if_needed...")
        await rate_controller.wait_if_needed()
        print("✅ wait_if_needed executado com sucesso")
        
        # Testa record_success
        print("Testando record_success...")
        rate_controller.record_success()
        print("✅ record_success executado com sucesso")
        
        # Testa record_failure
        print("Testando record_failure...")
        rate_controller.record_failure()
        print("✅ record_failure executado com sucesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do rate controller: {e}")
        return False

async def main():
    """Função principal de teste"""
    print("=" * 60)
    print("TESTE SIMPLES DO SISTEMA NEW RELIC")
    print("=" * 60)
    
    # Teste 1: Imports
    if not test_imports():
        print("❌ Falha nos imports - parando testes")
        return
    
    # Teste 2: Rate Controller
    if not await test_rate_controller():
        print("❌ Falha no rate controller")
    
    # Teste 3: Conexão
    if not await test_basic_connection():
        print("❌ Falha na conexão")
    
    print("\n" + "=" * 60)
    print("TESTES CONCLUÍDOS")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
