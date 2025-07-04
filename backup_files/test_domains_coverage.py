"""
Test script to validate that the New Relic collector is correctly fetching 
and processing metrics for all domains (APM, BROWSER, INFRA, DB, MOBILE, IOT, SERVERLESS, EXT, SYNTH).
"""
import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Add parent directory to path to import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.newrelic_collector import (
    coletar_contexto_completo, 
    buscar_todas_entidades, 
    coletar_metricas_entidade,
    coletar_metricas_nrql
)

async def test_collector_domains():
    """
    Test that the collector retrieves entities from all specified domains
    """
    logger.info("Testing New Relic collector domain coverage...")
    
    try:
        # Get all entities
        entidades = await buscar_todas_entidades()
        logger.info(f"Total de entidades coletadas: {len(entidades)}")
        
        # Group entities by domain
        dominios = {}
        for entidade in entidades:
            domain = entidade.get('domain', 'UNKNOWN')
            if domain not in dominios:
                dominios[domain] = []
            dominios[domain].append(entidade)
        
        # Print domain counts
        logger.info("Entidades por domínio:")
        for domain, entities in dominios.items():
            logger.info(f"  {domain}: {len(entities)} entidades")
        
        # Verify we have all expected domains
        expected_domains = {'APM', 'BROWSER', 'INFRA', 'DB', 'MOBILE', 'IOT', 'SERVERLESS', 'EXT', 'SYNTH'}
        missing_domains = expected_domains - set(dominios.keys())
        if missing_domains:
            logger.warning(f"Domínios ausentes: {missing_domains}")
        else:
            logger.info("Todos os domínios esperados foram encontrados!")
            
        return dominios
    except Exception as e:
        logger.error(f"Erro durante teste de cobertura de domínios: {e}")
        return None

async def test_metrics_collection(dominios):
    """
    Test metric collection for each domain
    """
    if not dominios:
        logger.error("Nenhum domínio para testar.")
        return
    
    results = {}
    
    for domain, entities in dominios.items():
        if not entities:
            logger.warning(f"Nenhuma entidade para o domínio {domain}.")
            continue
            
        # Test with first entity of each domain
        sample_entity = entities[0]
        logger.info(f"Testando coleta de métricas para domínio {domain}, entidade: {sample_entity.get('name', 'Sem nome')}")
        
        try:
            # Test direct metrics collection
            metrics = await coletar_metricas_entidade(sample_entity)
            logger.info(f"  Métricas diretas coletadas para {domain}: {list(metrics.keys())}")
            
            # Check if we got metrics for each period
            periods = list(metrics.keys())
            if not periods:
                logger.warning(f"  Nenhum período de métricas encontrado para {domain}")
            
            # Test NRQL metrics collection
            nrql_metrics = await coletar_metricas_nrql(sample_entity)
            logger.info(f"  Métricas NRQL coletadas para {domain}: {list(nrql_metrics.keys())}")
            
            results[domain] = {
                'entity': sample_entity.get('name', 'Sem nome'),
                'guid': sample_entity.get('guid', 'Sem GUID'),
                'metrics_success': len(metrics) > 0,
                'nrql_success': len(nrql_metrics) > 0,
                'periods': periods
            }
        except Exception as e:
            logger.error(f"  Erro ao coletar métricas para {domain}: {e}")
            results[domain] = {
                'entity': sample_entity.get('name', 'Sem nome'),
                'guid': sample_entity.get('guid', 'Sem GUID'),
                'error': str(e)
            }
    
    return results

async def run_full_collection_test():
    """
    Run a full context collection test
    """
    logger.info("Iniciando coleta completa de contexto...")
    start_time = datetime.now()
    
    try:
        context = await coletar_contexto_completo()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Coleta completa finalizada em {duration:.2f} segundos")
        
        # Analyze results
        entidades = context.get('entidades', [])
        logger.info(f"Total de entidades no contexto: {len(entidades)}")
        
        # Count entities by domain
        dominios = {}
        for entidade in entidades:
            domain = entidade.get('domain', 'UNKNOWN')
            if domain not in dominios:
                dominios[domain] = {'total': 0, 'with_metrics': 0}
            
            dominios[domain]['total'] += 1
            
            # Check if this entity has metrics
            if entidade.get('metricas'):
                dominios[domain]['with_metrics'] += 1
        
        # Report results
        logger.info("\nResumo de cobertura de métricas por domínio:")
        logger.info("=" * 60)
        logger.info(f"{'Domínio':<12} | {'Entidades':<10} | {'Com Métricas':<12} | {'% Cobertura':<12}")
        logger.info("-" * 60)
        
        for domain, counts in dominios.items():
            coverage = (counts['with_metrics'] / counts['total'] * 100) if counts['total'] > 0 else 0
            logger.info(f"{domain:<12} | {counts['total']:<10} | {counts['with_metrics']:<12} | {coverage:<10.1f}%")
        
        # Save full context to file for inspection
        output_path = os.path.join(parent_dir, "test_context_output.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\nContexto completo salvo em: {output_path}")
        
    except Exception as e:
        logger.error(f"Erro durante teste de coleta completa: {e}")
        return None

async def main():
    logger.info("Iniciando testes do New Relic Collector")
    
    # Test domain coverage
    dominios = await test_collector_domains()
    
    if dominios:
        # Test metrics collection for each domain
        metrics_results = await test_metrics_collection(dominios)
        
        if metrics_results:
            # Print summary
            logger.info("\nResumo dos testes de métricas por domínio:")
            logger.info("=" * 60)
            logger.info(f"{'Domínio':<12} | {'Entidade':<25} | {'Métricas':<8} | {'NRQL':<8}")
            logger.info("-" * 60)
            
            for domain, result in metrics_results.items():
                if 'error' in result:
                    logger.info(f"{domain:<12} | {result['entity'][:25]:<25} | {'❌':<8} | {'❌':<8} | Erro: {result['error']}")
                else:
                    metrics_status = "✅" if result['metrics_success'] else "❌"
                    nrql_status = "✅" if result['nrql_success'] else "❌"
                    logger.info(f"{domain:<12} | {result['entity'][:25]:<25} | {metrics_status:<8} | {nrql_status:<8}")
    
    # Run a full collection test
    await run_full_collection_test()
    
    logger.info("Testes concluídos!")

if __name__ == "__main__":
    asyncio.run(main())
