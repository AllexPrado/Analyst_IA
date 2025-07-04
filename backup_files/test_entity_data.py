import os
import sys
import asyncio
import logging
from datetime import datetime
import json
from pathlib import Path

# Configure logging to display detailed information
logging.basicConfig(level=logging.INFO, 
                   format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)

# Import New Relic collector functionality
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.newrelic_collector import buscar_todas_entidades, coletar_metricas_entidade, entidade_tem_dados
import aiohttp

async def main():
    logger.info("Starting entity data diagnostic test")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Fetch all entities
            entities = await buscar_todas_entidades(session)
            
            if not entities or len(entities) == 0:
                logger.error("No entities found. Check New Relic API key and account ID.")
                return
            
            logger.info(f"Found {len(entities)} entities")
            logger.info(f"Entity domains: {set([e.get('domain') for e in entities])}")
            
            # Get reporting entities only
            reporting_entities = [e for e in entities if e.get("reporting", False)]
            logger.info(f"Found {len(reporting_entities)} reporting entities")
            
            # Step 2: Sample entities from each domain for testing
            domain_samples = {}
            for entity in reporting_entities:
                domain = entity.get("domain")
                if domain not in domain_samples:
                    domain_samples[domain] = entity
            
            logger.info(f"Testing {len(domain_samples)} domain samples: {list(domain_samples.keys())}")
            
            # Step 3: Test each sample entity
            results = {
                "total_entities": len(entities),
                "reporting_entities": len(reporting_entities),
                "domains": list(domain_samples.keys()),
                "sample_results": {}
            }
            
            for domain, entity in domain_samples.items():
                logger.info(f"Testing entity {entity.get('name')} from domain {domain}")
                
                # Test metrics collection
                metrics = await coletar_metricas_entidade(entity)
                
                # See if entity has valid data
                has_data = entidade_tem_dados(metrics)
                
                # Record results
                results["sample_results"][domain] = {
                    "entity_name": entity.get("name"),
                    "entity_guid": entity.get("guid"),
                    "has_data": has_data,
                    "metrics_snapshot": {
                        period: {
                            metric: (
                                "data_present" if metric_data else "no_data"
                            ) for metric, metric_data in period_data.items()
                        } for period, period_data in metrics.items()
                    },
                    # Add detailed information for one period as example
                    "sample_period_detail": metrics.get("30min", {})
                }
                
                logger.info(f"Entity {entity.get('name')} has data: {has_data}")
            
            # Step 4: Save and display results
            output_path = Path("diagnostics_entity_data.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to {output_path}")
            logger.info(f"Overall results: {len([v for v in results['sample_results'].values() if v['has_data']])}/{len(results['sample_results'])} entities have valid data")
            
    except Exception as e:
        logger.exception(f"Error during diagnostics: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
