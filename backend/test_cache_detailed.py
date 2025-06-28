import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Configure logging to display detailed information
logging.basicConfig(level=logging.INFO, 
                   format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)

# Import cache and collector functionality
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.cache import forcar_atualizacao_cache, diagnosticar_cache, carregar_cache_do_disco, salvar_cache_no_disco
from utils.newrelic_collector import coletar_contexto_completo, buscar_todas_entidades
import aiohttp

async def test_cache_cycle():
    logger.info("Starting detailed cache diagnostic test")
    
    try:
        # Step 1: Check initial cache state
        logger.info("Checking initial cache state...")
        await carregar_cache_do_disco()
        initial_state = diagnosticar_cache()
        logger.info(f"Initial cache state: {json.dumps(initial_state, indent=2)}")
        
        # Step 2: Fetch entities directly to verify API connectivity
        logger.info("Testing API connectivity to New Relic...")
        async with aiohttp.ClientSession() as session:
            entities = await buscar_todas_entidades(session)
            logger.info(f"API connectivity: found {len(entities)} entities via direct API call")
            
            # Filter reporting entities
            reporting_entities = [e for e in entities if e.get("reporting", False)]
            logger.info(f"Found {len(reporting_entities)}/{len(entities)} reporting entities")
            
            # Report entities by domain
            domains = {}
            for entity in entities:
                domain = entity.get("domain", "UNKNOWN")
                domains[domain] = domains.get(domain, 0) + 1
            logger.info(f"Entities by domain: {domains}")
        
        # Step 3: Force cache update with detailed logging
        logger.info("Forcing cache update...")
        update_result = await forcar_atualizacao_cache(coletar_contexto_completo)
        logger.info(f"Cache update result: {update_result}")
        
        # Step 4: Check updated cache state
        logger.info("Checking final cache state...")
        final_state = diagnosticar_cache()
        logger.info(f"Final cache state: {json.dumps(final_state, indent=2)}")
        
        # Step 5: Analyze any differences
        analysis = {
            "update_successful": update_result,
            "initial_state": initial_state,
            "final_state": final_state,
            "entities_from_api": len(entities),
            "reporting_entities": len(reporting_entities),
            "entities_by_domain": domains,
            "cache_populated": final_state.get("total_chaves_dados", 0) > 0,
            "timestamp_updated": initial_state.get("ultima_atualizacao") != final_state.get("ultima_atualizacao"),
        }
        
        # Save analysis
        analysis_path = Path("diagnostics_cache_update.json")
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        logger.info(f"Analysis saved to {analysis_path}")
        
        # Step 6: Report likely issues
        if not analysis["cache_populated"]:
            logger.error("ISSUE DETECTED: Cache remains empty after update")
            if analysis["entities_from_api"] > 0:
                logger.error("ISSUE CAUSE: Entities are available via API but not being stored in cache")
                logger.error("LIKELY PROBLEM: Entity data validation is filtering out all entities")
            else:
                logger.error("ISSUE CAUSE: No entities available via New Relic API")
                logger.error("CHECK: New Relic API credentials and account configuration")
        
        if analysis["update_successful"] and not analysis["cache_populated"]:
            logger.error("INCONSISTENT STATE: Update reported successful but cache remains empty")
            logger.error("LIKELY PROBLEM: atualizar_cache_completo function is not properly storing data")
        
    except Exception as e:
        logger.exception(f"Error during cache diagnostics: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_cache_cycle())
