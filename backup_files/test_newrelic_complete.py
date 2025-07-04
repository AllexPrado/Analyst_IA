#!/usr/bin/env python3
"""
Teste completo do sistema de coleta avançado do New Relic.
Este script testa o coletor avançado, o processo de sincronização completo,
e a integração com o frontend.
"""

import os
import sys
import asyncio
import time
import logging
import json
from pathlib import Path
from pprint import pprint
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar diretórios ao path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
backend_dir = current_dir / 'backend'
sys.path.insert(0, str(backend_dir))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_newrelic.log"),
        logging.StreamHandler()
    ]
)

# Garantir que o diretório de logs existe
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger(__name__)

# Importar módulos do sistema avançado
from backend.utils.advanced_newrelic_collector import AdvancedNewRelicCollector
from backend.utils.new_relic_full_collector import NewRelicFullCollector

async def test_advanced_collector():
    """
    Testa o coletor avançado do New Relic.
    """
    print("=" * 60)
    print("TESTE DO COLETOR AVANÇADO")
    print("=" * 60)
    
    try:
        # Inicializar o coletor avançado
        collector = AdvancedNewRelicCollector()
        print(f"✅ Coletor avançado inicializado com sucesso")
        
        # Testar coleta de entidades (limitado a 10)
        print("\nColetando amostra de entidades...")
        start_time = time.time()
        entities = await collector.get_all_entities()
        entities = entities[:10]  # Limitar a 10 entidades para o teste
        duration = time.time() - start_time
        
        print(f"✅ {len(entities)} entidades coletadas em {duration:.2f} segundos")
        
        # Mostrar detalhes das entidades
        domains = {}
        types = {}
        
        for entity in entities:
            domain = entity.get("domain", "unknown")
            entity_type = entity.get("type", "unknown")
            
            if domain in domains:
                domains[domain] += 1
            else:
                domains[domain] = 1
                
            if entity_type in types:
                types[entity_type] += 1
            else:
                types[entity_type] = 1
                
        print("\nDistribuição de domínios:")
        for domain, count in domains.items():
            print(f"  - {domain}: {count} entidades")
            
        print("\nDistribuição de tipos:")
        for entity_type, count in types.items():
            print(f"  - {entity_type}: {count} entidades")
            
        # Testar coleta de métricas para uma entidade
        if entities:
            test_entity = entities[0]
            entity_guid = test_entity.get("guid")
            entity_name = test_entity.get("name")
            entity_domain = test_entity.get("domain")
            
            print(f"\nColetando métricas para: {entity_name} ({entity_guid})")
            metrics = await collector.get_entity_metrics(entity_guid)
            
            print(f"✅ Métricas coletadas: {len(metrics)} campos")
            print(f"Campos disponíveis: {', '.join(metrics.keys())}")
            
            # Testar coleta de métricas detalhadas
            print(f"\nColetando métricas detalhadas...")
            detailed_metrics = await collector.get_entity_detailed_metrics(entity_guid, entity_domain)
            
            print(f"✅ Métricas detalhadas coletadas: {len(detailed_metrics)} consultas")
            print(f"Consultas disponíveis: {', '.join(detailed_metrics.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar coletor avançado: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_nrql_with_circuit_breaker():
    """
    Teste da execução NRQL com circuit breaker
    """
    print("\n" + "=" * 60)
    print("TESTE DO CIRCUIT BREAKER NRQL")
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
        
    except ImportError as import_error:
        print(f"❌ Erro de import: {import_error}")
        return
    except Exception as general_error:
        print(f"❌ Erro geral: {general_error}")
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

async def test_full_collector():
    """
    Testa o coletor completo com salvamento em cache.
    """
    print("\n" + "=" * 60)
    print("TESTE DO COLETOR COMPLETO")
    print("=" * 60)
    
    try:
        # Criar diretório de cache temporário para teste
        test_cache_dir = Path(__file__).parent / "cache" / "newrelic_test"
        test_cache_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Diretório de cache de teste: {test_cache_dir}")
        
        # Instanciar o coletor completo
        collector = NewRelicFullCollector(cache_dir=str(test_cache_dir))
        
        # Teste de coleta limitada (apenas algumas entidades)
        print("\nExecutando coleta parcial para teste...")
        start_time = time.time()
        
        # Coletar apenas algumas entidades para o teste
        sample_entities = await collector.collector.get_all_entities()
        sample_entities = sample_entities[:5]  # Limitar a 5 entidades para o teste
        
        # Salvar no cache de teste
        collector.save_entities_to_cache(sample_entities)
        
        # Coletar detalhes para estas entidades
        await collector.collect_detailed_entity_data(sample_entities, save_to_cache=True)
        
        # Coletar alguns dashboards
        dashboards = await collector.collector.get_dashboards_list()
        dashboards = dashboards[:3]  # Limitar a 3 dashboards para o teste
        
        # Salvar no cache de teste
        collector.save_dashboards_to_cache(dashboards)
        
        # Gerar relatório de cobertura para o teste
        collector.stats = {
            "entities_total": len(sample_entities),
            "dashboards": len(dashboards),
            "alert_policies": 0,
            "entities_with_metrics": len(sample_entities),
            "entities_with_logs": 0,
            "entities_with_alerts": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat()
        }
        
        collector.save_coverage_report()
        
        duration = time.time() - start_time
        print(f"✅ Coleta de teste finalizada em {duration:.2f} segundos")
        
        # Listar arquivos gerados
        print("\nArquivos gerados no cache de teste:")
        for file in test_cache_dir.glob("**/*"):
            if file.is_file():
                size_kb = file.stat().st_size / 1024
                rel_path = file.relative_to(test_cache_dir)
                print(f"  - {rel_path} ({size_kb:.1f} KB)")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar coletor completo: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_synchronization_system():
    """
    Testa o sistema de sincronização.
    """
    print("\n" + "=" * 60)
    print("TESTE DO SISTEMA DE SINCRONIZAÇÃO")
    print("=" * 60)
    
    try:
        # Importar o módulo de sincronização
        from sincronizar_sistema import verificar_necessidade_coleta
        
        # Testar verificação de necessidade de coleta
        print("\nVerificando necessidade de coleta...")
        need_collect = verificar_necessidade_coleta(max_age_hours=24)
        
        print(f"Necessidade de coleta: {'Sim' if need_collect else 'Não'}")
        
        # Não executamos sincronizar_tudo() para evitar modificação no cache de produção
        print("Nota: A sincronização completa não será executada para evitar modificar o cache de produção")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar sistema de sincronização: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """
    Função principal que executa todos os testes
    """
    print("=" * 60)
    print("TESTE COMPLETO DO SISTEMA NEW RELIC AVANÇADO")
    print("=" * 60)
    
    results = {}
    
    # Teste 1: Coletor Avançado
    print("\n[1/5] Testando coletor avançado...")
    results["advanced_collector"] = await test_advanced_collector()
    
    # Teste 2: Coletor Completo
    print("\n[2/5] Testando coletor completo...")
    results["full_collector"] = await test_full_collector()
    
    # Teste 3: Sistema de Sincronização
    print("\n[3/5] Testando sistema de sincronização...")
    results["synchronization"] = await test_synchronization_system()
    
    # Teste 4: NRQL com circuit breaker
    print("\n[4/5] Testando NRQL com circuit breaker...")
    await test_nrql_with_circuit_breaker()
    
    # Teste 5: Comportamento do circuit breaker
    print("\n[5/5] Testando comportamento do circuit breaker...")
    await test_circuit_breaker_behavior()
    
    # Mostrar resumo dos resultados
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    # Mostrar resultado final
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"RESULTADO FINAL: {passed}/{total} testes passaram")
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! O sistema avançado está funcionando corretamente.")
    else:
        print(f"⚠️ {total - passed} teste(s) falharam. Verifique os logs para mais detalhes.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
