import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

print("=== DIAGNÓSTICO COMPLETO DO SISTEMA ===")

# Test 1: Basic imports
print("\n1. TESTANDO IMPORTS BÁSICOS:")
try:
    from utils.newrelic_collector import rate_controller
    print("   ✅ rate_controller")
except Exception as e:
    print(f"   ❌ rate_controller: {e}")
    sys.exit(1)

try:
    from utils.newrelic_collector import NewRelicCollector
    print("   ✅ NewRelicCollector")
except Exception as e:
    print(f"   ❌ NewRelicCollector: {e}")
    sys.exit(1)

try:
    from utils.newrelic_collector import executar_nrql_graphql, buscar_todas_entidades
    print("   ✅ Funções NRQL")
except Exception as e:
    print(f"   ❌ Funções NRQL: {e}")

# Test 2: Circuit breaker status
print("\n2. STATUS DO CIRCUIT BREAKER:")
try:
    status = rate_controller.get_status()
    print(f"   Estado: {status['circuit_state']}")
    print(f"   Falhas consecutivas: {status['consecutive_failures']}")
    print(f"   Sucessos consecutivos: {status['consecutive_successes']}")
    print(f"   Total de requests: {status['request_count']}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# Test 3: NewRelicCollector instantiation
print("\n3. TESTANDO INSTANCIAÇÃO:")
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('NEW_RELIC_API_KEY', 'fake_key')
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID', 'fake_id')
    
    collector = NewRelicCollector(api_key=api_key, account_id=account_id)
    print("   ✅ NewRelicCollector instanciado")
    
    health = collector.get_health_status()
    print(f"   Status de saúde: {health['status']}")
    print(f"   API Key configurada: {health['api_key_configured']}")
    print(f"   Account ID configurado: {health['account_id_configured']}")
    
except Exception as e:
    print(f"   ❌ Erro na instanciação: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Cache system
print("\n4. SISTEMA DE CACHE:")
try:
    from utils.cache import diagnosticar_cache
    cache_info = diagnosticar_cache()
    print(f"   Cache válido: {cache_info.get('cache_valido', False)}")
    print(f"   Idade (horas): {cache_info.get('idade_horas', 0)}")
    print(f"   Total entidades: {cache_info.get('total_entidades', 0)}")
except Exception as e:
    print(f"   ❌ Erro no cache: {e}")

# Test 5: OpenAI connector
print("\n5. OPENAI CONNECTOR:")
try:
    from utils.openai_connector import gerar_resposta_ia
    print("   ✅ OpenAI connector importado")
except Exception as e:
    print(f"   ❌ Erro no OpenAI: {e}")

print("\n=== DIAGNÓSTICO CONCLUÍDO ===")
print("Se todos os itens acima mostraram ✅, o sistema está funcionando!")
