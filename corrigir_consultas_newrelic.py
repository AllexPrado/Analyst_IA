"""
Script para corrigir as consultas GraphQL e NRQL no coletor avançado do New Relic
"""
import os
import sys
import json
import logging
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def corrigir_consulta_entidades():
    """Corrige a consulta de entidades para evitar domínios duplicados"""
    
    file_path = Path(__file__).parent / "backend" / "utils" / "newrelic_advanced_collector.py"
    
    if not file_path.exists():
        logger.error(f"Arquivo não encontrado: {file_path}")
        return False
        
    logger.info(f"Corrigindo consulta de entidades em {file_path}")
    
    # Faz backup do arquivo original
    backup_path = file_path.with_suffix(".py.bak")
    with open(file_path, "r", encoding="utf-8") as src, open(backup_path, "w", encoding="utf-8") as dst:
        dst.write(src.read())
    
    logger.info(f"Backup criado em {backup_path}")
    
    # Procura e substitui a consulta problemática
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Consulta problemática atual - com domínios duplicados
    old_query = """query EntitiesQuery {
      actor {
        entitySearch(queryBuilder: {domain: APM, domain: BROWSER, domain: INFRA, domain: MOBILE, domain: SYNTH, domain: EXT}) {
          results {
            entities {
              guid
              name
              domain
              entityType
              accountId
              tags {
                key
                values
              }
            }
            nextCursor
          }
        }
      }
    }"""
    
    # Consulta corrigida - com domínios não duplicados
    new_query = """query EntitiesQuery {
      actor {
        entitySearch(queryBuilder: {domainTypes: {domain: APM, types: []}, domainTypes: {domain: BROWSER, types: []}, domainTypes: {domain: INFRA, types: []}, domainTypes: {domain: MOBILE, types: []}, domainTypes: {domain: SYNTH, types: []}, domainTypes: {domain: EXT, types: []}}) {
          results {
            entities {
              guid
              name
              domain
              entityType
              accountId
              tags {
                key
                values
              }
            }
            nextCursor
          }
        }
      }
    }"""
    
    # Corrigir a consulta paginada também
    old_paged_query = """query EntitiesQuery($cursor: String!) {
              actor {
                entitySearch(queryBuilder: {domain: APM, domain: BROWSER, domain: INFRA, domain: MOBILE, domain: SYNTH, domain: EXT}) {
                  results(cursor: $cursor) {
                    entities {
                      guid
                      name
                      domain
                      entityType
                      accountId
                      tags {
                        key
                        values
                      }
                    }
                    nextCursor
                  }
                }
              }
            }"""
            
    new_paged_query = """query EntitiesQuery($cursor: String!) {
              actor {
                entitySearch(queryBuilder: {domainTypes: {domain: APM, types: []}, domainTypes: {domain: BROWSER, types: []}, domainTypes: {domain: INFRA, types: []}, domainTypes: {domain: MOBILE, types: []}, domainTypes: {domain: SYNTH, types: []}, domainTypes: {domain: EXT, types: []}}) {
                  results(cursor: $cursor) {
                    entities {
                      guid
                      name
                      domain
                      entityType
                      accountId
                      tags {
                        key
                        values
                      }
                    }
                    nextCursor
                  }
                }
              }
            }"""
    
    # Substitui as consultas
    modified_content = content.replace(old_query, new_query).replace(old_paged_query, new_paged_query)
    
    # Se houve mudanças, salva o arquivo
    if content != modified_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
        logger.info("✅ Consultas GraphQL corrigidas com sucesso!")
        return True
    else:
        logger.warning("⚠️ Nenhuma alteração feita nas consultas.")
        return False

def corrigir_consulta_nrql():
    """Corrige consultas NRQL para evitar erros de sintaxe"""
    
    file_path = Path(__file__).parent / "backend" / "utils" / "newrelic_advanced_collector.py"
    
    if not file_path.exists():
        logger.error(f"Arquivo não encontrado: {file_path}")
        return False
        
    logger.info(f"Corrigindo consultas NRQL em {file_path}")
    
    # Lê o arquivo
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verifica se há consultas JSON literais sendo enviadas como NRQL
    if "data = {\n        \"query\": nrql\n    }" in content:
        modified_content = content.replace(
            "data = {\n        \"query\": nrql\n    }", 
            "data = {\n        \"nrql\": nrql\n    }"
        )
        
        # Se houve mudanças, salva o arquivo
        if content != modified_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_content)
            logger.info("✅ Consultas NRQL corrigidas com sucesso!")
            return True
        else:
            logger.warning("⚠️ Nenhuma alteração feita nas consultas NRQL.")
            return False
    else:
        logger.info("ℹ️ Formato de consulta NRQL parece estar correto.")
        return False

def gerar_dados_simulados():
    """Gera dados simulados para testes quando não for possível conectar ao New Relic"""
    
    # Verifica se já existem dados simulados
    cache_dir = Path(__file__).parent / "backend" / "cache"
    cache_dir.mkdir(exist_ok=True)
    
    # Arquivos de cache que precisamos
    cache_files = {
        "kubernetes_metrics.json": {
            "pods": [{"name": "api-gateway", "status": "Running", "cpu": 0.45, "memory": 0.62, "restarts": 0},
                     {"name": "auth-service", "status": "Running", "cpu": 0.32, "memory": 0.48, "restarts": 1},
                     {"name": "database", "status": "Running", "cpu": 0.75, "memory": 0.81, "restarts": 0},
                     {"name": "frontend", "status": "Running", "cpu": 0.28, "memory": 0.36, "restarts": 0}],
            "services": [{"name": "api", "type": "ClusterIP", "endpoints": 3, "selectors": ["app=api"]},
                         {"name": "auth", "type": "ClusterIP", "endpoints": 2, "selectors": ["app=auth"]},
                         {"name": "db", "type": "ClusterIP", "endpoints": 1, "selectors": ["app=db"]},
                         {"name": "web", "type": "LoadBalancer", "endpoints": 3, "selectors": ["app=web"]}],
            "deployments": [{"name": "api-gateway", "replicas": 3, "available": 3, "upToDate": 3},
                            {"name": "auth-service", "replicas": 2, "available": 2, "upToDate": 2},
                            {"name": "database", "replicas": 1, "available": 1, "upToDate": 1},
                            {"name": "frontend", "replicas": 3, "available": 3, "upToDate": 3}],
            "timestamp": datetime.now().isoformat(),
            "cluster_health": 0.95
        },
        "infrastructure_detailed.json": {
            "hosts": [{"name": "prod-app-01", "status": "up", "cpu": 0.42, "memory": 0.68, "disk": 0.56, "net": 0.35},
                      {"name": "prod-app-02", "status": "up", "cpu": 0.38, "memory": 0.62, "disk": 0.48, "net": 0.32},
                      {"name": "prod-db-01", "status": "up", "cpu": 0.72, "memory": 0.84, "disk": 0.78, "net": 0.45},
                      {"name": "prod-cache-01", "status": "up", "cpu": 0.36, "memory": 0.45, "disk": 0.28, "net": 0.26}],
            "containers": [{"id": "c123", "image": "api:v2", "status": "running", "cpu": 0.38, "memory": 0.56},
                           {"id": "c124", "image": "auth:v1", "status": "running", "cpu": 0.26, "memory": 0.42},
                           {"id": "c125", "image": "postgres:12", "status": "running", "cpu": 0.65, "memory": 0.72},
                           {"id": "c126", "image": "redis:6", "status": "running", "cpu": 0.32, "memory": 0.28}],
            "networks": [{"name": "frontend-net", "type": "bridge", "status": "active"},
                         {"name": "backend-net", "type": "bridge", "status": "active"},
                         {"name": "db-net", "type": "bridge", "status": "active"}],
            "timestamp": datetime.now().isoformat(),
            "summary": {"total_hosts": 4, "up_hosts": 4, "containers": 4, "networks": 3, "storage_usage": 0.65}
        },
        "service_topology.json": {
            "nodes": [{"id": "api-gateway", "type": "service", "status": "healthy", "response_time": 120, "error_rate": 0.02},
                      {"id": "auth-service", "type": "service", "status": "healthy", "response_time": 85, "error_rate": 0.01},
                      {"id": "user-service", "type": "service", "status": "degraded", "response_time": 220, "error_rate": 0.05},
                      {"id": "product-service", "type": "service", "status": "healthy", "response_time": 95, "error_rate": 0.01},
                      {"id": "postgres", "type": "database", "status": "healthy", "response_time": 35, "error_rate": 0.0},
                      {"id": "redis", "type": "cache", "status": "healthy", "response_time": 5, "error_rate": 0.0},
                      {"id": "frontend", "type": "ui", "status": "healthy", "response_time": 280, "error_rate": 0.02}],
            "links": [{"source": "frontend", "target": "api-gateway", "calls_per_minute": 320, "error_rate": 0.02},
                      {"source": "api-gateway", "target": "auth-service", "calls_per_minute": 180, "error_rate": 0.01},
                      {"source": "api-gateway", "target": "user-service", "calls_per_minute": 145, "error_rate": 0.04},
                      {"source": "api-gateway", "target": "product-service", "calls_per_minute": 220, "error_rate": 0.01},
                      {"source": "auth-service", "target": "postgres", "calls_per_minute": 120, "error_rate": 0.0},
                      {"source": "user-service", "target": "postgres", "calls_per_minute": 95, "error_rate": 0.03},
                      {"source": "product-service", "target": "postgres", "calls_per_minute": 190, "error_rate": 0.01},
                      {"source": "auth-service", "target": "redis", "calls_per_minute": 210, "error_rate": 0.0},
                      {"source": "user-service", "target": "redis", "calls_per_minute": 130, "error_rate": 0.0}],
            "timestamp": datetime.now().isoformat(),
            "metrics": {"total_calls": 1290, "avg_latency": 120, "overall_health": 0.92}
        }
    }
    
    # Gera os arquivos de dados simulados se não existirem
    for filename, data in cache_files.items():
        file_path = cache_dir / filename
        if not file_path.exists():
            logger.info(f"Gerando arquivo de dados simulados: {filename}")
            with open(file_path, "w", encoding="utf-8") as f:
                # Para transformar datetime.now() em string na serialização JSON
                json.dump(data, f, indent=2, default=str)
    
    # Também gera o arquivo indicador de origem dos dados
    data_source_path = cache_dir / "data_source_indicator.json"
    with open(data_source_path, "w", encoding="utf-8") as f:
        json.dump({
            "using_real_data": False,
            "timestamp": datetime.now().isoformat(),
            "source": "Dados simulados (fallback)",
            "reason": "Problemas de conexão com New Relic"
        }, f, indent=2, default=str)
    
    logger.info("✅ Dados simulados gerados com sucesso")
    return True

if __name__ == "__main__":
    from datetime import datetime
    
    logger.info("=== Correção de consultas New Relic ===")
    
    try:
        logger.info("1. Corrigindo consultas GraphQL com domínios duplicados...")
        graphql_corrigido = corrigir_consulta_entidades()
        
        logger.info("2. Corrigindo consultas NRQL com formato incorreto...")
        nrql_corrigido = corrigir_consulta_nrql()
        
        logger.info("3. Gerando dados simulados para fallback...")
        gerar_dados_simulados()
        
        if graphql_corrigido or nrql_corrigido:
            logger.info("\n✅ Correções aplicadas com sucesso!\n")
            logger.info("Por favor, reinicie o backend para aplicar as alterações:")
            logger.info("    python backend/main.py")
        else:
            logger.info("\nℹ️ Nenhuma correção foi necessária nos arquivos de consulta.")
            
    except Exception as e:
        logger.error(f"❌ Erro durante a correção: {e}")
        sys.exit(1)
