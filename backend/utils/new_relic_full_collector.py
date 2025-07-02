"""
Sistema integrado de coleta completa do New Relic.
Este script implementa a coleta abrangente de todos os dados disponíveis no New Relic,
conforme os requisitos detalhados do projeto Analyst_IA.
"""

import os
import sys
import json
import logging
import asyncio
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/new_relic_collector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Garantir que o diretório de logs existe
os.makedirs("logs", exist_ok=True)

# Adicionar diretórios ao path
current_dir = Path(__file__).resolve().parent
if current_dir.name != "backend":
    sys.path.append(str(current_dir))
    backend_dir = current_dir / "backend"
    if backend_dir.exists():
        sys.path.append(str(backend_dir))
        
    utils_dir = backend_dir / "utils"
    if utils_dir.exists():
        sys.path.append(str(utils_dir))

# Importar o coletor avançado
try:
    from backend.utils.advanced_newrelic_collector import AdvancedNewRelicCollector
except ImportError:
    try:
        from utils.advanced_newrelic_collector import AdvancedNewRelicCollector
    except ImportError:
        logger.error("Não foi possível importar o AdvancedNewRelicCollector")
        sys.exit(1)

class NewRelicFullCollector:
    """
    Implementa a coleta completa e abrangente de dados do New Relic.
    """
    
    def __init__(self, cache_dir="backend"):
        """
        Inicializa o coletor completo.
        
        Args:
            cache_dir: Diretório onde o cache será armazenado
        """
        self.collector = AdvancedNewRelicCollector()
        self.cache_dir = Path(cache_dir)
        
        # Estrutura de cache avançada
        self.cache_file = self.cache_dir / "cache.json"
        self.cache_history_dir = self.cache_dir / "historico"
        self.cache_detailed_dir = self.cache_dir / "detailed_data"
        
        # Garantir que os diretórios de cache existam
        self.cache_history_dir.mkdir(exist_ok=True)
        self.cache_detailed_dir.mkdir(exist_ok=True)
        
        # Estrutura avançada do cache
        self.cache_structure = {
            # Domínios principais do New Relic
            "apm": [],
            "browser": [],
            "infra": [],
            "mobile": [],
            "synth": [],
            "db": [],
            "serverless": [],
            "iot": [],
            "ext": [],
            
            # Dados complementares
            "alertas": [],
            "dashboards": [],
            "workloads": [],
            "logs": {
                "summary": {},
                "recent": []
            },
            
            # Metadados da coleta
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "coverage": {},
                "collection_stats": {}
            }
        }
        
        # Contadores e estatísticas
        self.stats = {
            "entities_found": 0,
            "entities_collected": 0,
            "metrics_collected": 0,
            "alerts_collected": 0,
            "logs_collected": 0,
            "dashboards_collected": 0,
            "errors": 0
        }
        
        logger.info("Coletor completo New Relic inicializado")
    
    async def collect_all_data(self):
        """
        Realiza a coleta completa de todos os dados do New Relic.
        """
        start_time = time.time()
        logger.info("Iniciando coleta completa de dados do New Relic")
        
        try:
            # Passo 1: Coletar todas as entidades
            await self.collect_all_entities()
            
            # Passo 2: Coletar dashboards e workloads
            await self.collect_dashboards()
            
            # Passo 3: Coletar políticas de alerta
            await self.collect_alert_policies()
            
            # Passo 4: Coletar resumo de logs
            await self.collect_log_summary()
            
            # Passo 5: Salvar cache
            self.save_cache()
            
            # Passo 6: Gerar relatório de cobertura
            self.generate_coverage_report()
            
            # Finalizar com estatísticas
            elapsed = time.time() - start_time
            logger.info(f"Coleta completa finalizada em {elapsed:.2f} segundos")
            logger.info(f"Estatísticas: {json.dumps(self.stats, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro durante coleta completa: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def collect_all_entities(self):
        """
        Coleta todas as entidades de todos os domínios do New Relic.
        """
        logger.info("Coletando todas as entidades")
        
        # Lista de domínios a coletar
        domains = [
            "APM", "BROWSER", "INFRA", "MOBILE", "SYNTH", "DB", 
            "KUBERNETES", "SERVERLESS", "IOT", "EXT", "LAMBDA"
        ]
        
        for domain in domains:
            domain_lower = domain.lower()
            logger.info(f"Coletando entidades do domínio: {domain}")
            
            try:
                # Obter entidades do domínio
                entities = await self.collector.get_entities_by_domain(domain)
                self.stats["entities_found"] += len(entities)
                
                # Coletar dados completos para cada entidade
                complete_entities = []
                for entity in entities:
                    try:
                        complete_entity = await self.collector.collect_full_entity_data(entity)
                        complete_entities.append(complete_entity)
                        self.stats["entities_collected"] += 1
                        self.stats["metrics_collected"] += len(complete_entity.get("detailed_metrics", {}))
                        
                        # Incrementar alertas coletados
                        alerts = complete_entity.get("alerts", {})
                        if alerts:
                            self.stats["alerts_collected"] += len(alerts.get("violations", []))
                        
                        # Incrementar logs coletados
                        logs = complete_entity.get("logs", [])
                        self.stats["logs_collected"] += len(logs)
                        
                    except Exception as e:
                        logger.error(f"Erro ao coletar dados completos para entidade {entity.get('name')}: {e}")
                        self.stats["errors"] += 1
                
                # Armazenar entidades no cache
                if domain_lower in self.cache_structure:
                    self.cache_structure[domain_lower] = complete_entities
                    logger.info(f"✅ Coletadas {len(complete_entities)} entidades do domínio {domain}")
                else:
                    logger.warning(f"Domínio não previsto na estrutura do cache: {domain}")
                    
            except Exception as e:
                logger.error(f"Erro ao coletar entidades do domínio {domain}: {e}")
                logger.error(traceback.format_exc())
                self.stats["errors"] += 1
    
    async def collect_dashboards(self):
        """
        Coleta todos os dashboards e seus detalhes.
        """
        logger.info("Coletando dashboards")
        
        try:
            # Obter lista de dashboards
            dashboards_list = await self.collector.get_dashboards_list()
            logger.info(f"Encontrados {len(dashboards_list)} dashboards")
            
            # Coletar detalhes de cada dashboard
            complete_dashboards = []
            for dashboard in dashboards_list[:100]:  # Limitar para não sobrecarregar
                try:
                    dashboard_guid = dashboard.get("guid")
                    if dashboard_guid:
                        details = await self.collector.get_dashboard_details(dashboard_guid)
                        complete_dashboards.append({**dashboard, "details": details})
                        self.stats["dashboards_collected"] += 1
                except Exception as e:
                    logger.error(f"Erro ao coletar detalhes do dashboard {dashboard.get('name')}: {e}")
                    self.stats["errors"] += 1
            
            # Armazenar dashboards no cache
            self.cache_structure["dashboards"] = complete_dashboards
            logger.info(f"✅ Coletados detalhes de {len(complete_dashboards)} dashboards")
            
        except Exception as e:
            logger.error(f"Erro ao coletar dashboards: {e}")
            logger.error(traceback.format_exc())
            self.stats["errors"] += 1
    
    async def collect_alert_policies(self):
        """
        Coleta todas as políticas de alerta.
        """
        logger.info("Coletando políticas de alerta")
        
        try:
            # Obter políticas de alerta
            policies = await self.collector.get_all_alert_policies()
            logger.info(f"Encontradas {len(policies)} políticas de alerta")
            
            # Armazenar no cache
            self.cache_structure["alertas"] = policies
            
        except Exception as e:
            logger.error(f"Erro ao coletar políticas de alerta: {e}")
            logger.error(traceback.format_exc())
            self.stats["errors"] += 1
    
    async def collect_log_summary(self):
        """
        Coleta resumo de logs do sistema.
        """
        logger.info("Coletando resumo de logs")
        
        try:
            # Consultar resumo de logs via NRQL
            nrql = """
            SELECT count(*) FROM Log FACET level, service_name 
            SINCE 1 DAY AGO LIMIT 100
            """
            
            result = await self.collector.execute_nrql_query(nrql)
            
            if "error" not in result:
                self.cache_structure["logs"]["summary"] = result.get("results", [])
                logger.info("✅ Resumo de logs coletado com sucesso")
                
        except Exception as e:
            logger.error(f"Erro ao coletar resumo de logs: {e}")
            logger.error(traceback.format_exc())
            self.stats["errors"] += 1
    
    def save_cache(self):
        """
        Salva o cache completo nos formatos principal e histórico.
        """
        logger.info("Salvando cache completo")
        
        try:
            # Atualizar timestamp
            self.cache_structure["metadata"]["timestamp"] = datetime.now().isoformat()
            
            # Salvar cache principal
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache_structure, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ Cache principal salvo em: {self.cache_file}")
            
            # Salvar versão histórica no formato antigo (para compatibilidade)
            historical_cache = {
                "timestamp": self.cache_structure["metadata"]["timestamp"],
                "entidades": []
            }
            
            # Consolidar entidades de todos os domínios
            for domain, entities in self.cache_structure.items():
                if domain not in ["metadata", "logs", "dashboards", "alertas", "workloads"] and isinstance(entities, list):
                    for entity in entities:
                        # Converter para o formato histórico
                        historical_entity = {
                            "name": entity.get("name", "Unknown"),
                            "guid": entity.get("guid", ""),
                            "dominio": entity.get("domain", "").upper(),
                            "metricas": entity.get("detailed_metrics", {})
                        }
                        historical_cache["entidades"].append(historical_entity)
            
            # Salvar cache histórico
            historical_file = self.cache_history_dir / "cache_completo.json"
            with open(historical_file, "w", encoding="utf-8") as f:
                json.dump(historical_cache, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ Cache histórico salvo em: {historical_file}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
            logger.error(traceback.format_exc())
            self.stats["errors"] += 1
    
    def generate_coverage_report(self):
        """
        Gera relatório de cobertura da coleta.
        """
        logger.info("Gerando relatório de cobertura")
        
        try:
            # Calcular estatísticas de cobertura
            coverage = {}
            total_entities = 0
            
            for domain, entities in self.cache_structure.items():
                if domain not in ["metadata", "logs", "dashboards", "alertas", "workloads"] and isinstance(entities, list):
                    domain_entities = len(entities)
                    total_entities += domain_entities
                    
                    # Calcular completude das entidades
                    complete_entities = 0
                    metrics_coverage = 0
                    entities_with_alerts = 0
                    entities_with_logs = 0
                    
                    for entity in entities:
                        # Entidade completa se tiver métricas detalhadas
                        has_metrics = bool(entity.get("detailed_metrics", {}))
                        has_alerts = bool(entity.get("alerts", {}).get("violations", []))
                        has_logs = bool(entity.get("logs", []))
                        
                        if has_metrics:
                            complete_entities += 1
                            metrics_coverage += len(entity.get("detailed_metrics", {}))
                        
                        if has_alerts:
                            entities_with_alerts += 1
                        
                        if has_logs:
                            entities_with_logs += 1
                    
                    # Calcular percentuais
                    completeness = (complete_entities / domain_entities * 100) if domain_entities > 0 else 0
                    alert_coverage = (entities_with_alerts / domain_entities * 100) if domain_entities > 0 else 0
                    log_coverage = (entities_with_logs / domain_entities * 100) if domain_entities > 0 else 0
                    
                    # Registrar cobertura
                    coverage[domain] = {
                        "total_entities": domain_entities,
                        "complete_entities": complete_entities,
                        "completeness_percent": completeness,
                        "metrics_coverage": metrics_coverage,
                        "alert_coverage_percent": alert_coverage,
                        "log_coverage_percent": log_coverage
                    }
            
            # Adicionar cobertura de dashboards e alertas
            coverage["dashboards"] = {
                "total": len(self.cache_structure["dashboards"])
            }
            
            coverage["alertas"] = {
                "total": len(self.cache_structure["alertas"])
            }
            
            # Salvar relatório de cobertura
            self.cache_structure["metadata"]["coverage"] = coverage
            self.cache_structure["metadata"]["collection_stats"] = self.stats
            self.cache_structure["metadata"]["total_entities"] = total_entities
            
            # Salvar como arquivo separado também
            coverage_file = self.cache_dir / "coverage_report.json"
            coverage_report = {
                "timestamp": datetime.now().isoformat(),
                "total_entities": total_entities,
                "coverage": coverage,
                "stats": self.stats
            }
            
            with open(coverage_file, "w", encoding="utf-8") as f:
                json.dump(coverage_report, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ Relatório de cobertura salvo em: {coverage_file}")
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de cobertura: {e}")
            logger.error(traceback.format_exc())

async def main():
    """Função principal"""
    collector = NewRelicFullCollector()
    await collector.collect_all_data()

if __name__ == "__main__":
    asyncio.run(main())
