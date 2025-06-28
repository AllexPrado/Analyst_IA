#!/usr/bin/env python3
"""
Script para testar o NewRelicCollector independentemente
Usado para diagnosticar problemas de rate limit e circuit breaker
"""

import os
import sys
import asyncio
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
import aiohttp

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Adiciona o diretório backend ao path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Garante que o arquivo newrelic_collector.py existe no diretório backend
if not (backend_dir / "newrelic_collector.py").exists():
    print(f"❌ Arquivo 'newrelic_collector.py' não encontrado em {backend_dir}")
    sys.exit(1)

# Importa diretamente das células originais
try:
    from newrelic_collector import (
        rate_controller, 
        executar_nrql_graphql, 
        buscar_todas_entidades,
        NEW_RELIC_API_KEY,
        NEW_RELIC_ACCOUNT_ID
    )
    print("✅ Importação das funções originais bem-sucedida")
except ImportError as e:
    print(f"❌ Erro no import das funções originais: {e}")
    sys.exit(1)

class NewRelicCollector:
    """Classe wrapper para testes do NewRelicCollector"""
    
    def __init__(self, api_key, account_id):
        self.api_key = api_key
        self.account_id = account_id
        self.rate_controller = rate_controller
        
    def get_health_status(self):
        """Retorna status de saúde do coletor"""
        return {
            "status": "healthy" if self.rate_controller.circuit_state == "CLOSED" else "degraded" if self.rate_controller.circuit_state == "HALF_OPEN" else "unhealthy",
            "circuit_breaker": self.rate_controller.get_status(),
            "api_key_configured": bool(self.api_key),
            "account_id_configured": bool(self.account_id)
        }
        
    async def execute_nrql_query(self, query):
        """Executa query NRQL usando as funções originais"""
        async with aiohttp.ClientSession() as session:
            return await executar_nrql_graphql(session, query)
            
    async def collect_entities(self):
        """Coleta entidades usando as funções originais"""
        async with aiohttp.ClientSession() as session:
            return await buscar_todas_entidades(session)

async def test_collector():
    """
    Teste completo do NewRelicCollector
    """
    print("=" * 60)
    print("TESTE DO NEW RELIC COLLECTOR")
    print("=" * 60)
    
    # Carrega variáveis de ambiente
    load_dotenv()
    
    api_key = os.getenv('NEW_RELIC_API_KEY') or NEW_RELIC_API_KEY
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID') or NEW_RELIC_ACCOUNT_ID
    
    if not api_key or not account_id:
        print("❌ NEW_RELIC_API_KEY e NEW_RELIC_ACCOUNT_ID devem estar configurados no .env")
        return
    
    print(f"✅ API Key configurada: {api_key[:10]}...")
    print(f"✅ Account ID: {account_id}")
    
    # Instancia o coletor
    collector = NewRelicCollector(api_key=api_key, account_id=account_id)
    
    # Status inicial
    print("\n--- STATUS INICIAL ---")
    health = collector.get_health_status()
    print(f"Status: {health['status']}")
    print(f"Circuit State: {health['circuit_breaker']['circuit_state']}")
    print(f"Consecutive Failures: {health['circuit_breaker']['consecutive_failures']}")
    
    # Teste 1: Query simples para testar conectividade
    print("\n--- TESTE 1: CONECTIVIDADE ---")
    try:
        test_query = f"SELECT count(*) FROM Transaction WHERE appName IS NOT NULL SINCE 1 hour ago LIMIT 1"
        print(f"Executando: {test_query}")
        result = await collector.execute_nrql_query(test_query)
        print(f"✅ Conectividade OK!")
        print(f"   Resultado: {result}")
    except Exception as e:
        print(f"❌ Erro de conectividade: {e}")
    
    # Status após teste 1
    print("\n--- STATUS APÓS CONECTIVIDADE ---")
    health = collector.get_health_status()
    print(f"Status: {health['status']}")
    print(f"Circuit State: {health['circuit_breaker']['circuit_state']}")
    print(f"Consecutive Failures: {health['circuit_breaker']['consecutive_failures']}")
    
    # Teste 2: Coleta de entidades
    print("\n--- TESTE 2: COLETA DE ENTIDADES ---")
    try:
        print("Executando coleta de entidades...")
        entities = await collector.collect_entities()
        print(f"✅ Coleta de entidades executada!")
        print(f"   Total de entidades: {len(entities)}")
        
        if entities:
            # Conta por domínio
            dominios = {}
            for entity in entities[:10]:  # Limita para mostrar apenas 10
                dominio = entity.get('domain', 'UNKNOWN')
                dominios[dominio] = dominios.get(dominio, 0) + 1
                print(f"   - {entity.get('name', 'N/A')} ({dominio})")
            
            print("\n   Distribuição por domínio:")
            for dominio, count in dominios.items():
                print(f"     {dominio}: {count}")
        else:
            print("   ⚠️ Nenhuma entidade encontrada")
            
    except Exception as e:
        print(f"❌ Erro na coleta de entidades: {e}")
        print(f"   Detalhes: {str(e)}")
    
    # Status final
    print("\n--- STATUS FINAL ---")
    health = collector.get_health_status()
    print(f"Status: {health['status']}")
    print(f"Circuit State: {health['circuit_breaker']['circuit_state']}")
    print(f"Consecutive Failures: {health['circuit_breaker']['consecutive_failures']}")
    print(f"Request Count: {health['circuit_breaker']['request_count']}")
    
    if health['circuit_breaker']['circuit_state'] == 'OPEN':
        print(f"⏰ Tempo para retry: {health['circuit_breaker']['time_until_retry']:.1f}s")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)

async def test_circuit_breaker():
    """
    Teste específico do circuit breaker
    """
    print("\n" + "=" * 60)
    print("TESTE DO CIRCUIT BREAKER")
    print("=" * 60)
    
    load_dotenv()
    api_key = os.getenv('NEW_RELIC_API_KEY') or NEW_RELIC_API_KEY
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID') or NEW_RELIC_ACCOUNT_ID
    
    if not api_key or not account_id:
        print("❌ Credenciais não configuradas")
        return
    
    collector = NewRelicCollector(api_key=api_key, account_id=account_id)
    
    print("Status inicial do circuit breaker:")
    health = collector.get_health_status()
    print(f"  Circuit State: {health['circuit_breaker']['circuit_state']}")
    print(f"  Consecutive Failures: {health['circuit_breaker']['consecutive_failures']}")
    
    # Força muitas falhas para abrir o circuit breaker
    print("\nForçando falhas para testar circuit breaker...")
    
    for i in range(12):  # Mais que o limite de 10 falhas
        try:
            # Query inválida para forçar erro
            bad_query = f"SELECT invalid_field FROM NonExistentTable WHERE fake = true LIMIT 1"
            await collector.execute_nrql_query(bad_query)
        except Exception as e:
            print(f"Falha {i+1}: {str(e)[:80]}...")
        
        health = collector.get_health_status()
        print(f"  Circuit State: {health['circuit_breaker']['circuit_state']} "
              f"(Failures: {health['circuit_breaker']['consecutive_failures']})")
        
        if health['circuit_breaker']['circuit_state'] == 'OPEN':
            print("🔴 Circuit breaker ABERTO!")
            break
        
        await asyncio.sleep(0.5)
    
    # Tenta executar uma query com circuit aberto
    print("\nTentando query com circuit breaker aberto...")
    try:
        good_query = f"SELECT count(*) FROM Transaction LIMIT 1"
        await collector.execute_nrql_query(good_query)
        print("❌ Query executada - circuit breaker não está funcionando!")
    except Exception as e:
        print(f"✅ Query bloqueada pelo circuit breaker: {e}")
    
    final_health = collector.get_health_status()
    print(f"\nEstado final do circuit: {final_health['circuit_breaker']['circuit_state']}")

def test_rate_controller():
    """
    Teste simples do rate controller
    """
    print("=" * 60)
    print("TESTE DO RATE CONTROLLER")
    print("=" * 60)
    
    print("Status inicial:")
    status = rate_controller.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\nSimulando algumas falhas...")
    for i in range(5):
        rate_controller.record_failure(is_rate_limit=(i % 2 == 0))
        status = rate_controller.get_status()
        print(f"  Falha {i+1} - State: {status['circuit_state']}, Failures: {status['consecutive_failures']}")
    
    print("\nSimulando sucessos...")
    for i in range(3):
        rate_controller.record_success()
        status = rate_controller.get_status()
        print(f"  Sucesso {i+1} - State: {status['circuit_state']}, Failures: {status['consecutive_failures']}")
    
    print("\nStatus final:")
    final_status = rate_controller.get_status()
    for key, value in final_status.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Teste do NewRelicCollector')
    parser.add_argument('--circuit', action='store_true', help='Testa especificamente o circuit breaker')
    parser.add_argument('--rate', action='store_true', help='Testa especificamente o rate controller')
    args = parser.parse_args()
    
    if args.circuit:
        asyncio.run(test_circuit_breaker())
    elif args.rate:
        test_rate_controller()
    else:
        asyncio.run(test_collector())
