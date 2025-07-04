import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_cache():
    """
    Analyze the cache file to verify if metrics are properly collected and stored.
    """
    cache_file = Path("historico") / "cache_completo.json"
    
    if not cache_file.exists():
        logger.error(f"Cache file not found at {cache_file}")
        return
    
    logger.info(f"Loading cache file: {cache_file}")
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        if not cache_data or not isinstance(cache_data, dict):
            logger.error("Cache file is empty or invalid")
            return
        
        # Check if 'entidades' key exists
        if 'entidades' not in cache_data:
            logger.error("No 'entidades' found in cache")
            return
        
        entities = cache_data['entidades']
        logger.info(f"Found {len(entities)} entities in cache")
        
        # Metrics counter
        entities_with_metrics = 0
        metric_types_count = {
            'apdex': 0,
            'response_time_max': 0,
            'error_rate': 0,
            'throughput': 0,
            'recent_error': 0,
            'page_load_time': 0,
            'js_errors': 0,
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'generic': 0
        }
        
        # Analyze each entity
        for idx, entity in enumerate(entities):
            entity_name = entity.get('name', 'Unknown')
            entity_domain = entity.get('domain', 'Unknown')
            
            has_metrics = False
            metrics_in_entity = set()
            
            # Check for metricas and detalhe fields
            if 'metricas' in entity and entity['metricas']:
                has_metrics = True
                
                # Check for metrics data in different periods
                for period, period_metrics in entity['metricas'].items():
                    if period != 'timestamp' and isinstance(period_metrics, dict):
                        # Count metric types
                        for metric_type in period_metrics:
                            if period_metrics[metric_type]:  # Only count non-empty metrics
                                metric_types_count[metric_type] = metric_types_count.get(metric_type, 0) + 1
                                metrics_in_entity.add(metric_type)
            
            # Check for 'detalhe' field (legacy format)
            elif 'detalhe' in entity and entity['detalhe']:
                try:
                    detalhe = json.loads(entity['detalhe']) if isinstance(entity['detalhe'], str) else entity['detalhe']
                    if detalhe:
                        has_metrics = True
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Log entity metrics status
            if has_metrics:
                entities_with_metrics += 1
                logger.info(f"Entity {idx+1}: {entity_name} ({entity_domain}) has metrics: {', '.join(metrics_in_entity)}")
            else:
                logger.info(f"Entity {idx+1}: {entity_name} ({entity_domain}) has NO metrics")
        
        # Summary
        logger.info(f"\n=== METRICS SUMMARY ===")
        logger.info(f"Total entities: {len(entities)}")
        logger.info(f"Entities with metrics: {entities_with_metrics} ({entities_with_metrics/len(entities)*100:.1f}%)")
        logger.info(f"\nMetric types distribution:")
        for metric_type, count in metric_types_count.items():
            logger.info(f"  {metric_type}: {count} entities")
        
        return {
            'total_entities': len(entities),
            'entities_with_metrics': entities_with_metrics,
            'metric_types_count': metric_types_count
        }
        
    except Exception as e:
        logger.error(f"Error analyzing cache: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    logger.info("Starting cache metrics analysis...")
    analysis_result = analyze_cache()
    
    if analysis_result:
        logger.info(f"Analysis complete. {analysis_result['entities_with_metrics']}/{analysis_result['total_entities']} entities have metrics.")
    else:
        logger.error("Analysis failed")
