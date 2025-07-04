import os
import sys
import asyncio
import logging
import json
import aiohttp
from datetime import datetime
from pathlib import Path

# Configure logging to display detailed information
logging.basicConfig(level=logging.INFO, 
                   format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)

# Import cache and collector functionality
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.newrelic_collector import (
    buscar_todas_entidades, entidade_tem_dados, coletar_metricas_entidade,
    executar_nrql_graphql, PERIODOS
)

async def test_entity_filtering():
    """
    Detalhadamente analisar por que tantas entidades estão sendo filtradas na coleta de métricas.
    """
    logger.info("Iniciando diagnóstico detalhado de filtragem de entidades")
    results = {
        "timestamp": datetime.now().isoformat(),
        "overview": {},
        "detailed_analysis": {},
        "raw_data_samples": {},
        "nrql_query_results": {}
    }
    
    try:
        # Step 1: Collect all entities
        logger.info("Coletando todas as entidades do New Relic...")
        async with aiohttp.ClientSession() as session:
            all_entities = await buscar_todas_entidades(session)
            
            if not all_entities:
                logger.error("Nenhuma entidade encontrada!")
                results["overview"]["error"] = "Nenhuma entidade encontrada na API"
                return results
                
            # Basic statistics
            results["overview"]["total_entities"] = len(all_entities)
            reporting_entities = [e for e in all_entities if e.get("reporting", False)]
            results["overview"]["reporting_entities"] = len(reporting_entities)
            
            # Count by domain
            domain_counts = {}
            for entity in all_entities:
                domain = entity.get("domain", "UNKNOWN")
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            results["overview"]["entities_by_domain"] = domain_counts
            logger.info(f"Encontradas {len(all_entities)} entidades, {len(reporting_entities)} reportando")
            logger.info(f"Distribuição por domínio: {domain_counts}")
            
            # Step 2: Select a sample of entities for detailed testing
            selected_entities = {}
            for domain in domain_counts.keys():
                # Select up to 2 reporting entities from each domain
                domain_entities = [e for e in reporting_entities if e.get("domain") == domain]
                if domain_entities:
                    selected_entities[domain] = domain_entities[:2]
                    
            # Save a raw sample
            results["raw_data_samples"]["sample_entities"] = {
                domain: [{"name": e.get("name"), "guid": e.get("guid"), "type": e.get("type")} 
                        for e in entities]
                for domain, entities in selected_entities.items()
            }
            
            # Step 3: Test metric collection for each sample entity
            for domain, entities in selected_entities.items():
                logger.info(f"Testando coleta de métricas para domínio {domain}...")
                results["detailed_analysis"][domain] = []
                
                for entity in entities:
                    entity_result = {
                        "guid": entity.get("guid"),
                        "name": entity.get("name"),
                        "type": entity.get("type"),
                        "metrics_collected": False,
                        "has_valid_data": False,
                        "metrics_by_period": {},
                        "detailed_validation": {}
                    }
                    
                    # Collect metrics for this entity
                    logger.info(f"Coletando métricas para {entity.get('name')} ({entity.get('guid')})")
                    metrics = await coletar_metricas_entidade(entity)
                    entity_result["metrics_collected"] = bool(metrics)
                    
                    if metrics:
                        # Test if the entity has valid data according to validation function
                        has_data = entidade_tem_dados(metrics)
                        entity_result["has_valid_data"] = has_data
                        
                        # Count metrics by period
                        for period, period_data in metrics.items():
                            entity_result["metrics_by_period"][period] = {
                                "total_metrics": len(period_data) if isinstance(period_data, dict) else 0,
                                "metrics_with_values": sum(1 for v in period_data.values() if v not in (None, [], 0, "")) if isinstance(period_data, dict) else 0
                            }
                            
                        # Detailed validation analysis
                        validation_details = analyze_entity_data_validation(metrics)
                        entity_result["detailed_validation"] = validation_details
                        
                        # Sample the raw metrics for reference (for the first period only)
                        if "30min" in metrics:
                            entity_result["metric_sample"] = metrics["30min"]
                            
                        logger.info(f"Entidade {entity.get('name')} tem dados válidos: {has_data}")
                    else:
                        logger.warning(f"Nenhuma métrica coletada para {entity.get('name')}")
                    
                    results["detailed_analysis"][domain].append(entity_result)
                    
            # Step 4: Test NRQL queries directly for a few entities to see raw responses
            logger.info("Testando queries NRQL diretamente...")
            results["nrql_query_results"] = {}
            
            # Pick one entity from each domain for testing
            for domain, entities in selected_entities.items():
                if not entities:
                    continue
                    
                entity = entities[0]
                guid = entity.get("guid")
                results["nrql_query_results"][domain] = {}
                
                # Test NRQL queries based on domain
                if domain == "APM":
                    # Test a basic response time query
                    query = f"SELECT max(duration) FROM Transaction WHERE entityGuid = '{guid}' {PERIODOS['30min']}"
                    result = await executar_nrql_graphql(session, query)
                    results["nrql_query_results"][domain]["response_time"] = {
                        "query": query,
                        "result": result
                    }
                elif domain == "BROWSER":
                    # Test a basic LCP query
                    query = f"SELECT average(largestContentfulPaint) FROM PageViewTiming WHERE entityGuid = '{guid}' {PERIODOS['30min']}"
                    result = await executar_nrql_graphql(session, query)
                    results["nrql_query_results"][domain]["lcp"] = {
                        "query": query,
                        "result": result
                    }
                elif domain == "INFRA":
                    # Test a basic CPU query
                    query = f"SELECT average(cpuPercent) FROM SystemSample WHERE entityGuid = '{guid}' {PERIODOS['30min']}"
                    result = await executar_nrql_graphql(session, query)
                    results["nrql_query_results"][domain]["cpu"] = {
                        "query": query,
                        "result": result
                    }
                    
        # Step 5: Summary and filtering statistics
        filtered_count = results["overview"]["reporting_entities"] - sum(results["overview"].get("entities_in_cache", {}).values())
        results["overview"]["filtered_entities"] = filtered_count
        results["overview"]["filter_rate_percent"] = round(filtered_count / results["overview"]["reporting_entities"] * 100, 2) if results["overview"]["reporting_entities"] else 0
        
    except Exception as e:
        logger.exception(f"Erro durante diagnóstico: {e}")
        results["overview"]["error"] = str(e)
        
    # Save results to file
    output_path = Path("diagnostics_entity_filtering.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Análise completa salva em {output_path}")
    
    return results

def analyze_entity_data_validation(metrics):
    """
    Analyze why an entity might fail the entidade_tem_dados validation.
    
    Args:
        metrics: Dictionary with metrics data
    
    Returns:
        Dictionary with validation analysis
    """
    if not metrics or not isinstance(metrics, dict):
        return {"valid": False, "reason": "metrics is None or not a dict"}
    
    results = {
        "valid": False,
        "periods_analyzed": 0,
        "periods_with_data": 0,
        "metrics_analyzed": 0,
        "metrics_with_data": 0,
        "details": {}
    }
    
    # For each period (30min, 24h, 7d, 30d)
    for periodo, periodo_data in metrics.items():
        period_result = {
            "valid": False,
            "metrics_analyzed": 0,
            "metrics_with_data": 0,
            "metric_details": {}
        }
        
        results["periods_analyzed"] += 1
        
        if not isinstance(periodo_data, dict):
            period_result["reason"] = f"periodo_data for {periodo} is not a dict"
            results["details"][periodo] = period_result
            continue
        
        # For each metric in this period
        for metrica_nome, metrica_valores in periodo_data.items():
            metric_result = {
                "valid": False,
                "type": type(metrica_valores).__name__,
                "is_empty_list": isinstance(metrica_valores, list) and len(metrica_valores) == 0,
                "is_null": metrica_valores is None,
            }
            
            period_result["metrics_analyzed"] += 1
            results["metrics_analyzed"] += 1
            
            # Skip null values
            if metrica_valores is None:
                metric_result["reason"] = "metric value is None"
                period_result["metric_details"][metrica_nome] = metric_result
                continue
            
            # Handle list of values
            if isinstance(metrica_valores, list):
                if not metrica_valores:
                    metric_result["reason"] = "empty list"
                    period_result["metric_details"][metrica_nome] = metric_result
                    continue
                
                # Check each item for valid values
                for item in metrica_valores:
                    if isinstance(item, dict) and item:
                        for key, val in item.items():
                            if val not in (None, 0, "", []):
                                metric_result["valid"] = True
                                metric_result["valid_key"] = key
                                metric_result["valid_value"] = str(val)[:100]  # Truncate long values
                                break
                
                if not metric_result["valid"]:
                    metric_result["reason"] = "no valid values in list items"
            # Handle direct values
            elif metrica_valores not in (None, 0, "", []):
                metric_result["valid"] = True
                metric_result["value"] = str(metrica_valores)[:100]  # Truncate long values
            else:
                metric_result["reason"] = f"invalid direct value: {metrica_valores}"
            
            # Update period stats
            if metric_result["valid"]:
                period_result["metrics_with_data"] += 1
                results["metrics_with_data"] += 1
            
            period_result["metric_details"][metrica_nome] = metric_result
        
        # Is this period valid?
        period_result["valid"] = period_result["metrics_with_data"] > 0
        
        # Update overall stats
        if period_result["valid"]:
            results["periods_with_data"] += 1
        
        results["details"][periodo] = period_result
    
    # Overall validation - is there at least one valid piece of data?
    results["valid"] = results["periods_with_data"] > 0
    
    return results

if __name__ == "__main__":
    asyncio.run(test_entity_filtering())
