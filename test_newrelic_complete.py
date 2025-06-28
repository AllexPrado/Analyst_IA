#!/usr/bin/env python3
"""
Teste completo do sistema New Relic com circuit breaker
"""

import os
import sys
import asyncio
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Adiciona backend ao path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_nrql_with_circuit_breaker():
    """
    Teste da execução NRQL com circuit breaker
    """
    print("=" * 60)
    print("TESTE NRQL COM CIRCUIT BREAKER")
    print("=" * 60)
    
    # Carrega variáveis de ambiente
    load_dotenv()
    
    api_key = os.getenv('NEW_RELIC_API_KEY')
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
    
    if not api_key or not account_id:
        print("❌ NEW_RELIC_API_KEY e NEW_RELIC_ACCOUNT_ID devem estar configurados no .env")
        return
    
    print(f"✅ API Key configurada: {api_key[:10]}...")
    print(f"✅ Account ID: {account_id}")
    
    try:
        from utils.newrelic_collector import executar_nrql_graphql, rate_controller
        import aiohttp
        
        # Status inicial do circuit breaker
        print("\n--- STATUS INICIAL DO CIRCUIT BREAKER ---")
        status = rate_controller.get_status()
        print(f"Circuit State: {status['circuit_state']}")
        print(f"Consecutive Failures: {status['consecutive_failures']}")
        
        # Teste 1: Query válida
        print("\n--- TESTE 1: QUERY VÁLIDA ---")
        try:
            query = "SELECT count(*) FROM Transaction SINCE 1 hour ago LIMIT 1"
            print(f"Executando: {query}")
            
            async with aiohttp.ClientSession() as session:
                result = await executar_nrql_graphql(session, query)
                
            if result:
                print(f"✅ Query executada com sucesso!")
                print(f"   Resultado: {result}")
            else:
                print("⚠️  Query executada mas sem resultados")
                
        except Exception as e:
            print(f"❌ Erro na query válida: {e}")
        
        # Status após query válida
        print("\n--- STATUS APÓS QUERY VÁLIDA ---")
        status = rate_controller.get_status()
        print(f"Circuit State: {status['circuit_state']}")
        print(f"Consecutive Failures: {status['consecutive_failures']}")
        print(f"Request Count: {status['request_count']}")
        
        # Teste 2: Busca de entidades
        print("\n--- TESTE 2: BUSCA DE ENTIDADES ---")
        try:
            from utils.newrelic_collector import buscar_todas_entidades
            
            async with aiohttp.ClientSession() as session:
                entities = await buscar_todas_entidades(session)
            
            print(f"✅ Entidades encontradas: {len(entities)}")
            
            # Mostra algumas entidades
            for i, entity in enumerate(entities[:3]):
                print(f"   {i+1}. {entity.get('name', 'N/A')} ({entity.get('domain', 'N/A')})")
                
        except Exception as e:
            print(f"❌ Erro na busca de entidades: {e}")
        
        # Status final
        print("\n--- STATUS FINAL ---")
        status = rate_controller.get_status()
        print(f"Circuit State: {status['circuit_state']}")
        print(f"Consecutive Failures: {status['consecutive_failures']}")
        print(f"Consecutive Successes: {status['consecutive_successes']}")
        print(f"Request Count: {status['request_count']}")
        
        if status['circuit_state'] == 'OPEN':
            print(f"⏰ Tempo para retry: {status['time_until_retry']:.1f}s")
        
    except ImportError as e:
        print(f"❌ Erro de import: {e}")
        return
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

async def test_circuit_breaker_behavior():
    """
    Teste específico do comportamento do circuit breaker
    """
    print("\n" + "=" * 60)
    print("TESTE COMPORTAMENTO DO CIRCUIT BREAKER")
    print("=" * 60)
    
    try:
        from utils.newrelic_collector import executar_nrql_graphql, rate_controller
        import aiohttp
        
        # Força o circuit breaker a abrir com queries inválidas
        print("Forçando falhas para abrir o circuit breaker...")
        
        for i in range(12):  # Mais que o limite de 10 falhas
            try:
                # Query inválida para forçar erro
                bad_query = f"SELECT invalid_field FROM NonExistentTable{i} LIMIT 1"
                
                async with aiohttp.ClientSession() as session:
                    await executar_nrql_graphql(session, bad_query)
                    
            except Exception as e:
                pass  # Erro esperado
            
            status = rate_controller.get_status()
            print(f"  Tentativa {i+1}: State={status['circuit_state']}, Failures={status['consecutive_failures']}")
            
            if status['circuit_state'] == 'OPEN':
                print("🔴 Circuit breaker ABERTO!")
                break
            
            await asyncio.sleep(0.1)  # Pequena pausa
        
        # Tenta executar uma query com circuit aberto
        print("\nTentando query com circuit breaker aberto...")
        try:
            good_query = "SELECT count(*) FROM Transaction LIMIT 1"
            
            async with aiohttp.ClientSession() as session:
                await executar_nrql_graphql(session, good_query)
                
            print("❌ Query executada - circuit breaker não está funcionando!")
            
        except Exception as e:
            if "Circuit breaker OPEN" in str(e):
                print("✅ Query bloqueada pelo circuit breaker como esperado")
            else:
                print(f"⚠️  Query falhou por outro motivo: {e}")
        
        # Status final do circuit breaker
        final_status = rate_controller.get_status()
        print(f"\nEstado final do circuit breaker: {final_status['circuit_state']}")
        print(f"Tempo até próxima tentativa: {final_status['time_until_retry']:.1f}s")
        
    except Exception as e:
        print(f"❌ Erro no teste do circuit breaker: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """
    Função principal que executa todos os testes
    """
    print("=" * 60)
    print("TESTE COMPLETO DO SISTEMA NEW RELIC")
    print("=" * 60)
    
    # Teste 1: NRQL com circuit breaker
    await test_nrql_with_circuit_breaker()
    
    # Teste 2: Comportamento do circuit breaker
    await test_circuit_breaker_behavior()
    
    print("\n" + "=" * 60)
    print("TODOS OS TESTES CONCLUÍDOS")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
