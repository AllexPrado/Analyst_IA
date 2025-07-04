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

# Adiciona o diretório backend ao path
backend_dir = Path(__file__).parent / 'backend'
sys.path.append(str(backend_dir))

# Import direto do módulo utils
utils_dir = backend_dir / 'utils'
sys.path.append(str(utils_dir))

# Importa do módulo original newrelic_collector que tem todas as funções
try:
    from utils.newrelic_collector import rate_controller
    # Cria uma classe simples para teste
    class NewRelicCollector:
        def __init__(self, api_key, account_id):
            self.api_key = api_key
            self.account_id = account_id
            self.rate_controller = rate_controller
            
        def get_health_status(self):
            return {
                "status": "healthy" if self.rate_controller.circuit_state == "CLOSED" else "degraded",
                "circuit_breaker": self.rate_controller.get_status(),
                "api_key_configured": bool(self.api_key),
                "account_id_configured": bool(self.account_id)
            }
            
        async def execute_nrql_query(self, query):
            # Importa a função executar_nrql_graphql
            from utils.newrelic_collector import executar_nrql_graphql
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                return await executar_nrql_graphql(session, query)
                
        async def collect_entities(self):
            from utils.newrelic_collector import buscar_todas_entidades
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                return await buscar_todas_entidades(session)
                
except ImportError as import_error:
    print(f"Erro no import: {import_error}")
    print("Tentando import direto...")
    
    # Fallback: import direto dos arquivos
    import sys
    sys.path.insert(0, str(utils_dir))
    from newrelic_collector import rate_controller
    
    class NewRelicCollector:
        def __init__(self, api_key, account_id):
            self.api_key = api_key
            self.account_id = account_id
            self.rate_controller = rate_controller
            
        def get_health_status(self):
            return {
                "status": "healthy" if self.rate_controller.circuit_state == "CLOSED" else "degraded",
                "circuit_breaker": self.rate_controller.get_status(),
                "api_key_configured": bool(self.api_key),
                "account_id_configured": bool(self.account_id)
            }

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_collector():
    """
    Teste completo do NewRelicCollector
    """
    print("=" * 60)
    print("TESTE DO NEW RELIC COLLECTOR")
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
    
    # Teste 2: Query de entidades
    print("\n--- TESTE 2: ENTIDADES ---")
    try:
        entities_query = f"""
        SELECT 
            entityGuid,
            entityName,
            entityType,
            domain
        FROM EntitySearch 
        WHERE domain IN ('APM', 'BROWSER', 'MOBILE', 'INFRA', 'SYNTH') 
        AND entityType IN ('APPLICATION', 'HOST', 'MONITOR', 'SERVICE')
        LIMIT 10
        """
        print("Buscando entidades...")
        result = await collector.execute_nrql_query(entities_query)
        
        if result and 'results' in result:
            entities = result['results']
            print(f"✅ Entidades encontradas: {len(entities)}")
            
            # Mostra algumas entidades
            for i, entity in enumerate(entities[:3]):
                print(f"   {i+1}. {entity.get('entityName', 'N/A')} ({entity.get('entityType', 'N/A')})")
        else:
            print("⚠️  Nenhuma entidade encontrada")
            
    except Exception as e:
        print(f"❌ Erro na busca de entidades: {e}")
    
    # Status após teste 2
    print("\n--- STATUS APÓS ENTIDADES ---")
    health = collector.get_health_status()
    print(f"Status: {health['status']}")
    print(f"Circuit State: {health['circuit_breaker']['circuit_state']}")
    print(f"Consecutive Failures: {health['circuit_breaker']['consecutive_failures']}")
    
    # Teste 3: Função de coleta completa
    print("\n--- TESTE 3: COLETA COMPLETA ---")
    try:
        print("Executando coleta completa de entidades...")
        entities = await collector.collect_entities()
        print(f"✅ Coleta completa executada!")
        print(f"   Total de entidades: {len(entities)}")
        
        # Conta por tipo
        tipos = {}
        for entity in entities:
            tipo = entity.get('entityType', 'UNKNOWN')
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        print("   Distribuição por tipo:")
        for tipo, count in tipos.items():
            print(f"     {tipo}: {count}")
            
    except Exception as e:
        print(f"❌ Erro na coleta completa: {e}")
    
    # Status final
    print("\n--- STATUS FINAL ---")
    health = collector.get_health_status()
    print(f"Status: {health['status']}")
    print(f"Circuit State: {health['circuit_breaker']['circuit_state']}")
    print(f"Consecutive Failures: {health['circuit_breaker']['consecutive_failures']}")
    print(f"Consecutive Successes: {health['circuit_breaker']['consecutive_successes']}")
    print(f"Request Count: {health['circuit_breaker']['request_count']}")
    
    if health['circuit_breaker']['circuit_state'] == 'OPEN':
        print(f"⏰ Tempo para retry: {health['circuit_breaker']['time_until_retry']:.1f}s")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)

async def test_circuit_breaker():
    """
    Teste específico do circuit breaker com queries que devem falhar
    """
    print("\n" + "=" * 60)
    print("TESTE DO CIRCUIT BREAKER")
    print("=" * 60)
    
    load_dotenv()
    api_key = os.getenv('NEW_RELIC_API_KEY')
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
    
    if not api_key or not account_id:
        print("❌ Credenciais não configuradas")
        return
    
    collector = NewRelicCollector(api_key=api_key, account_id=account_id)
    
    # Força muitas falhas para abrir o circuit breaker
    print("Forçando falhas para testar circuit breaker...")
    
    for i in range(15):  # Mais que o limite de 10 falhas
        try:
            # Query inválida para forçar erro
            bad_query = f"SELECT invalid_field FROM NonExistentTable WHERE fake = true LIMIT 1"
            await collector.execute_nrql_query(bad_query)
        except Exception as e:
            print(f"Falha {i+1}: {str(e)[:100]}...")
        
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
    
    print("\nAguardando circuit breaker tentar HALF_OPEN...")
    
    # Espera o timeout do circuit breaker (60 segundos configurado)
    health = collector.get_health_status()
    wait_time = health['circuit_breaker']['time_until_retry']
    print(f"Aguardando {wait_time:.1f}s...")
    
    # Aguarda um pouco e testa novamente
    await asyncio.sleep(min(wait_time + 5, 10))  # Máximo 10s para teste
    
    print("Testando transição para HALF_OPEN...")
    try:
        good_query = f"SELECT count(*) FROM Transaction LIMIT 1"
        result = await collector.execute_nrql_query(good_query)
        print("✅ Query executada em modo HALF_OPEN")
    except Exception as e:
        print(f"Query ainda bloqueada: {e}")
    
    final_health = collector.get_health_status()
    print(f"Estado final do circuit: {final_health['circuit_breaker']['circuit_state']}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Teste do NewRelicCollector')
    parser.add_argument('--circuit', action='store_true', help='Testa especificamente o circuit breaker')
    args = parser.parse_args()
    
    if args.circuit:
        asyncio.run(test_circuit_breaker())
    else:
        asyncio.run(test_collector())
