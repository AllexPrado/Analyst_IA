"""
Este script testa o acesso às métricas no cache para validar que estão 
corretamente disponíveis para uso no sistema.
"""

import json
import logging
import sys
from pathlib import Path
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_metrics_access():
    """
    Test accessing metrics from the cache and using them in the system.
    """
    try:
        # Import required modules
        from utils.cache import carregar_cache_do_disco
        
        # Load cache
        logger.info("Loading cache from disk...")
        await carregar_cache_do_disco()
        
        # Import cache directly
        from utils.cache import _cache
        
        if not _cache or not _cache.get('dados') or not _cache['dados'].get('entidades'):
            logger.error("Cache not loaded or no entities found in cache")
            return False
        
        entities = _cache['dados'].get('entidades', [])
        logger.info(f"Cache loaded with {len(entities)} entities")
        
        # Test 1: Find APM entities with Apdex metrics
        logger.info("\n=== Test 1: Finding APM entities with Apdex metrics ===")
        apm_entities = [entity for entity in entities if entity.get('domain') == 'APM']
        
        if not apm_entities:
            logger.error("No APM entities found!")
            return False
            
        logger.info(f"Found {len(apm_entities)} APM entities")
        
        # Find entities with Apdex metrics
        apdex_entities = []
        for entity in apm_entities:
            name = entity.get('name', 'Unknown')
            metrics = entity.get('metricas', {})
            
            for period, period_metrics in metrics.items():
                if period != 'timestamp' and isinstance(period_metrics, dict):
                    if 'apdex' in period_metrics and period_metrics['apdex']:
                        apdex_entities.append({
                            'name': name,
                            'apdex': period_metrics['apdex'],
                            'period': period
                        })
                        break
        
        logger.info(f"Found {len(apdex_entities)} entities with Apdex metrics")
        for idx, entity in enumerate(apdex_entities[:5]):  # Show top 5
            logger.info(f"Entity {idx+1}: {entity['name']} - Period: {entity['period']}")
            
        # Test 2: Calculate average response time for API entities
        logger.info("\n=== Test 2: Calculating average response time for API entities ===")
        api_entities = [entity for entity in entities if 'API' in entity.get('name', '').upper() or 'api' in entity.get('name', '')]
        
        if not api_entities:
            logger.warning("No API entities found!")
        else:
            logger.info(f"Found {len(api_entities)} API entities")
            
            response_times = []
            for entity in api_entities:
                name = entity.get('name', 'Unknown')
                metrics = entity.get('metricas', {})
                
                for period, period_metrics in metrics.items():
                    if period != 'timestamp' and isinstance(period_metrics, dict):
                        if 'response_time_max' in period_metrics and period_metrics['response_time_max']:
                            try:
                                # Extract response time value from metric
                                resp_time_data = period_metrics['response_time_max']
                                if isinstance(resp_time_data, list) and len(resp_time_data) > 0:
                                    resp_item = resp_time_data[0]
                                    if isinstance(resp_item, dict) and 'max.duration' in resp_item:
                                        response_time = resp_item['max.duration']
                                        response_times.append({
                                            'name': name,
                                            'response_time': response_time,
                                            'period': period
                                        })
                                        break
                            except Exception as e:
                                logger.warning(f"Error extracting response time for {name}: {e}")
            
            logger.info(f"Found {len(response_times)} API entities with response time metrics")
            
            if response_times:
                # Calculate average
                avg_response_time = sum(item['response_time'] for item in response_times) / len(response_times)
                logger.info(f"Average API response time: {avg_response_time:.2f}ms")
                
                # Show top 3 slowest APIs
                sorted_apis = sorted(response_times, key=lambda x: x['response_time'], reverse=True)
                logger.info("Top 3 slowest APIs:")
                for idx, api in enumerate(sorted_apis[:3]):
                    logger.info(f"{idx+1}. {api['name']} - Response Time: {api['response_time']:.2f}ms")
        
        # Test 3: Find entities with high error rates
        logger.info("\n=== Test 3: Finding entities with high error rates ===")
        entities_with_errors = []
        
        for entity in entities:
            name = entity.get('name', 'Unknown')
            domain = entity.get('domain', 'Unknown')
            metrics = entity.get('metricas', {})
            
            for period, period_metrics in metrics.items():
                if period != 'timestamp' and isinstance(period_metrics, dict):
                    if 'error_rate' in period_metrics and period_metrics['error_rate']:
                        try:
                            # Extract error rate value from metric
                            error_data = period_metrics['error_rate']
                            if isinstance(error_data, list) and len(error_data) > 0:
                                error_item = error_data[0]
                                if isinstance(error_item, dict) and 'error_rate' in error_item:
                                    error_rate = error_item['error_rate']
                                    if error_rate > 0:  # Only interested in entities with errors
                                        entities_with_errors.append({
                                            'name': name,
                                            'domain': domain,
                                            'error_rate': error_rate,
                                            'period': period
                                        })
                                        break
                        except Exception as e:
                            logger.warning(f"Error extracting error rate for {name}: {e}")
        
        logger.info(f"Found {len(entities_with_errors)} entities with error rates > 0")
        
        if entities_with_errors:
            # Show entities with highest error rates
            sorted_entities = sorted(entities_with_errors, key=lambda x: x['error_rate'], reverse=True)
            logger.info("Entities with highest error rates:")
            for idx, entity in enumerate(sorted_entities[:5]):  # Show top 5
                logger.info(f"{idx+1}. {entity['name']} ({entity['domain']}) - Error Rate: {entity['error_rate']:.4f}%")
        
        logger.info("\n=== Metrics Access Tests Completed Successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"Error in test_metrics_access: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Starting metrics access test...")
    asyncio.run(test_metrics_access())
