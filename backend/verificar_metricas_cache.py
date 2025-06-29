import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona um console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

async def verificar_metricas_cache():
    """
    Verifica se as entidades no cache possuem métricas reais
    """
    try:
        from utils.cache import get_cache
        from utils.entity_processor import filter_entities_with_data
        
        logger.info("Verificando métricas no cache atual...")
        
        # Obtém cache atual
        cache = await get_cache()
        if not cache or "entidades" not in cache:
            logger.error("Cache não encontrado ou sem entidades")
            return False
        
        entidades = cache.get("entidades", [])
        logger.info(f"Cache contém {len(entidades)} entidades")
        
        # Estatísticas de métricas
        metricas_stats = {
            "has_apdex": 0,
            "has_response_time": 0,
            "has_error_rate": 0,
            "has_throughput": 0,
            "any_metrics": 0,
            "no_metrics": 0
        }
        
        # Verifica métricas em cada entidade
        for entity in entidades:
            has_any_metric = False
            
            if entity and entity.get('metricas'):
                for period in entity['metricas'].values():
                    if not isinstance(period, dict):
                        continue
                        
                    # Verifica métricas específicas
                    if 'apdex' in period and period['apdex']:
                        metricas_stats['has_apdex'] += 1
                        has_any_metric = True
                        
                    if 'response_time_max' in period and period['response_time_max']:
                        metricas_stats['has_response_time'] += 1
                        has_any_metric = True
                        
                    if ('error_rate' in period and period['error_rate']) or ('recent_error' in period and period['recent_error']):
                        metricas_stats['has_error_rate'] += 1
                        has_any_metric = True
                        
                    if 'throughput' in period and period['throughput']:
                        metricas_stats['has_throughput'] += 1
                        has_any_metric = True
            
            if has_any_metric:
                metricas_stats['any_metrics'] += 1
            else:
                metricas_stats['no_metrics'] += 1
        
        # Exibe resultados
        logger.info("\n=== DIAGNÓSTICO DE MÉTRICAS NO CACHE ===")
        logger.info(f"Total de entidades: {len(entidades)}")
        logger.info(f"Entidades com qualquer métrica: {metricas_stats['any_metrics']} ({metricas_stats['any_metrics']/max(1,len(entidades))*100:.1f}%)")
        logger.info(f"Entidades sem métricas: {metricas_stats['no_metrics']} ({metricas_stats['no_metrics']/max(1,len(entidades))*100:.1f}%)")
        logger.info("\nMétricas específicas:")
        logger.info(f"- Apdex: {metricas_stats['has_apdex']} ({metricas_stats['has_apdex']/max(1,len(entidades))*100:.1f}%)")
        logger.info(f"- Response Time: {metricas_stats['has_response_time']} ({metricas_stats['has_response_time']/max(1,len(entidades))*100:.1f}%)")
        logger.info(f"- Error Rate: {metricas_stats['has_error_rate']} ({metricas_stats['has_error_rate']/max(1,len(entidades))*100:.1f}%)")
        logger.info(f"- Throughput: {metricas_stats['has_throughput']} ({metricas_stats['has_throughput']/max(1,len(entidades))*100:.1f}%)")
        
        # Exibe algumas amostras se tivermos entidades com métricas
        if metricas_stats['any_metrics'] > 0:
            # Encontra uma entidade com métricas para exemplo
            for entity in entidades:
                if entity and entity.get('metricas'):
                    for period in entity['metricas'].values():
                        if isinstance(period, dict) and (
                            ('apdex' in period and period['apdex']) or 
                            ('response_time_max' in period and period['response_time_max'])
                        ):
                            logger.info("\n=== EXEMPLO DE ENTIDADE COM MÉTRICAS ===")
                            logger.info(f"Nome: {entity.get('name', 'N/A')}")
                            logger.info(f"Domain: {entity.get('domain', 'N/A')}")
                            logger.info(f"Type: {entity.get('entityType', 'N/A')}")
                            
                            # Mostra detalhes de métricas para o período 30min
                            if '30min' in entity['metricas']:
                                period_data = entity['metricas']['30min']
                                if isinstance(period_data, dict):
                                    logger.info("\nMétricas (30min):")
                                    for metric_name, metric_data in period_data.items():
                                        if metric_data:
                                            logger.info(f"- {metric_name}: {json.dumps(metric_data)[:100]}...")
                            break
                    else:
                        continue
                    break
        
        return metricas_stats['any_metrics'] > 0
        
    except Exception as e:
        logger.error(f"Erro ao verificar métricas: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Iniciando verificação de métricas no cache...")
    resultado = asyncio.run(verificar_metricas_cache())
    
    if resultado:
        logger.info("✅ Cache contém entidades com métricas reais!")
    else:
        logger.error("❌ Não foram encontradas entidades com métricas reais no cache")
