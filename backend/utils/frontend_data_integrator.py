"""
Script para integração completa do New Relic com o Frontend.
Este script garante que todos os dados coletados do New Relic sejam disponibilizados
para o Frontend de forma otimizada.
"""

import os
import sys
import json
import logging
import asyncio
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import shutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/frontend_integration.log"),
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

class FrontendIntegrator:
    """
    Integra os dados coletados do New Relic com o Frontend.
    """
    
    def __init__(self, cache_dir="backend", frontend_data_dir=None):
        """
        Inicializa o integrador.
        
        Args:
            cache_dir: Diretório onde o cache está armazenado
            frontend_data_dir: Diretório para dados do frontend (padrão: backend/dados)
        """
        self.cache_dir = Path(cache_dir)
        
        if frontend_data_dir:
            self.frontend_data_dir = Path(frontend_data_dir)
        else:
            self.frontend_data_dir = self.cache_dir / "dados"
            
        # Garantir que o diretório de dados do frontend existe
        self.frontend_data_dir.mkdir(exist_ok=True)
        
        # Arquivo de cache principal
        self.cache_file = self.cache_dir / "cache.json"
        
        # Arquivo de status da integração
        self.status_file = self.frontend_data_dir / "integration_status.json"
        
        # Estatísticas de processamento
        self.stats = {
            "entities_processed": 0,
            "dashboards_processed": 0,
            "alerts_processed": 0,
            "files_generated": 0,
            "processing_time": 0
        }
        
        logger.info(f"Integrador Frontend inicializado. Diretório de dados: {self.frontend_data_dir}")
    
    async def process_all_data(self):
        """
        Processa todos os dados do cache para o formato do frontend.
        """
        start_time = datetime.now()
        logger.info("Iniciando processamento de dados para o frontend")
        
        try:
            # Verificar se o arquivo de cache existe
            if not self.cache_file.exists():
                logger.error(f"Arquivo de cache não encontrado: {self.cache_file}")
                return False
                
            # Carregar cache
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
                
            # Verificar timestamp do cache
            timestamp = cache.get("metadata", {}).get("timestamp", "Unknown")
            logger.info(f"Cache carregado. Timestamp: {timestamp}")
            
            # Processar diferentes tipos de dados
            await asyncio.gather(
                self.process_entities(cache),
                self.process_dashboards(cache),
                self.process_alerts(cache),
                self.generate_insights(cache),
                self.generate_coverage_data(cache),
                self.process_logs(cache)
            )
            
            # Gerar arquivo de índice para APIs
            self.generate_api_index()
            
            # Atualizar estatísticas
            elapsed = (datetime.now() - start_time).total_seconds()
            self.stats["processing_time"] = elapsed
            
            # Salvar status
            self.save_status()
            
            logger.info(f"Processamento completo em {elapsed:.2f} segundos")
            logger.info(f"Estatísticas: {json.dumps(self.stats, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar dados para o frontend: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def process_entities(self, cache):
        """
        Processa entidades do cache para o frontend.
        
        Args:
            cache: Dados do cache
        """
        logger.info("Processando entidades para o frontend")
        
        try:
            # Lista para todas as entidades
            all_entities = []
            
            # Processar entidades de cada domínio
            for domain, entities in cache.items():
                if domain in ["metadata", "logs", "dashboards", "alertas", "workloads"]:
                    continue
                    
                if not isinstance(entities, list):
                    continue
                    
                # Processar entidades do domínio
                domain_lower = domain.lower()
                domain_upper = domain.upper()
                domain_entities = []
                
                for entity in entities:
                    # Extrair dados relevantes para o frontend
                    frontend_entity = {
                        "id": entity.get("guid", ""),
                        "name": entity.get("name", "Unknown"),
                        "domain": domain_upper,
                        "reporting": entity.get("reporting", False),
                        "type": entity.get("type", ""),
                        "alertSeverity": entity.get("alertSeverity", "NONE"),
                        "metrics": {}
                    }
                    
                    # Adicionar métricas relevantes
                    metrics = {}
                    
                    # Obter métricas do domínio específico
                    domain_metrics = entity.get(domain_lower, {})
                    if domain_metrics:
                        metrics.update(domain_metrics)
                    
                    # Obter métricas detalhadas
                    detailed_metrics = entity.get("detailed_metrics", {})
                    if detailed_metrics:
                        for metric_name, metric_data in detailed_metrics.items():
                            # Simplificar dados métricos para o frontend
                            if isinstance(metric_data, list) and metric_data:
                                if len(metric_data) == 1:
                                    # Extrair valor único
                                    for key, value in metric_data[0].items():
                                        if key not in ["timestamp", "facet"]:
                                            metrics[metric_name] = value
                                            break
                                else:
                                    # Para múltiplos valores, manter a lista
                                    metrics[metric_name] = metric_data
                    
                    # Adicionar tags
                    tags = entity.get("tags", [])
                    if tags:
                        frontend_entity["tags"] = tags
                    
                    # Adicionar resumo de alertas
                    alerts = entity.get("alerts", {})
                    if alerts:
                        violations = alerts.get("violations", [])
                        if violations:
                            frontend_entity["alerts"] = {
                                "count": len(violations),
                                "severity": alerts.get("severity", "NONE")
                            }
                    
                    # Adicionar métricas ao objeto da entidade
                    frontend_entity["metrics"] = metrics
                    
                    # Adicionar à lista de entidades do domínio
                    domain_entities.append(frontend_entity)
                    all_entities.append(frontend_entity)
                    self.stats["entities_processed"] += 1
                
                # Salvar entidades do domínio
                if domain_entities:
                    domain_file = self.frontend_data_dir / f"entidades_{domain_lower}.json"
                    with open(domain_file, "w", encoding="utf-8") as f:
                        json.dump(domain_entities, f, indent=2, ensure_ascii=False)
                        
                    logger.info(f"✅ Salvas {len(domain_entities)} entidades do domínio {domain_upper}")
                    self.stats["files_generated"] += 1
            
            # Salvar todas as entidades
            all_entities_file = self.frontend_data_dir / "entidades.json"
            with open(all_entities_file, "w", encoding="utf-8") as f:
                json.dump(all_entities, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ Salvas {len(all_entities)} entidades no total")
            self.stats["files_generated"] += 1
            
        except Exception as e:
            logger.error(f"Erro ao processar entidades: {e}")
            logger.error(traceback.format_exc())
    
    async def process_dashboards(self, cache):
        """
        Processa dashboards para o frontend.
        
        Args:
            cache: Dados do cache
        """
        logger.info("Processando dashboards para o frontend")
        
        try:
            dashboards = cache.get("dashboards", [])
            
            if not dashboards:
                logger.info("Nenhum dashboard encontrado no cache")
                return
                
            # Simplificar dashboards para o frontend
            frontend_dashboards = []
            
            for dashboard in dashboards:
                # Extrair dados relevantes
                frontend_dashboard = {
                    "id": dashboard.get("guid", ""),
                    "name": dashboard.get("name", "Unknown"),
                    "description": dashboard.get("description", "")
                }
                
                # Extrair detalhes
                details = dashboard.get("details", {})
                
                if details:
                    # Extrair páginas e widgets
                    pages = details.get("pages", [])
                    if pages:
                        frontend_dashboard["pages"] = []
                        
                        for page in pages:
                            frontend_page = {
                                "name": page.get("name", ""),
                                "widgets": len(page.get("widgets", []))
                            }
                            frontend_dashboard["pages"].append(frontend_page)
                
                frontend_dashboards.append(frontend_dashboard)
                self.stats["dashboards_processed"] += 1
            
            # Salvar dashboards para o frontend
            dashboards_file = self.frontend_data_dir / "dashboards.json"
            with open(dashboards_file, "w", encoding="utf-8") as f:
                json.dump(frontend_dashboards, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ Salvos {len(frontend_dashboards)} dashboards")
            self.stats["files_generated"] += 1
            
        except Exception as e:
            logger.error(f"Erro ao processar dashboards: {e}")
            logger.error(traceback.format_exc())
    
    async def process_alerts(self, cache):
        """
        Processa alertas para o frontend.
        
        Args:
            cache: Dados do cache
        """
        logger.info("Processando alertas para o frontend")
        
        try:
            alert_policies = cache.get("alertas", [])
            
            if not alert_policies:
                logger.info("Nenhuma política de alerta encontrada no cache")
                return
                
            # Simplificar políticas para o frontend
            frontend_alerts = []
            
            for policy in alert_policies:
                frontend_alert = {
                    "id": policy.get("id", ""),
                    "name": policy.get("name", "Unknown"),
                    "accountId": policy.get("accountId", ""),
                    "incidentPreference": policy.get("incidentPreference", "")
                }
                
                frontend_alerts.append(frontend_alert)
                self.stats["alerts_processed"] += 1
            
            # Salvar alertas para o frontend
            alerts_file = self.frontend_data_dir / "alertas.json"
            with open(alerts_file, "w", encoding="utf-8") as f:
                json.dump(frontend_alerts, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ Salvas {len(frontend_alerts)} políticas de alerta")
            self.stats["files_generated"] += 1
            
        except Exception as e:
            logger.error(f"Erro ao processar alertas: {e}")
            logger.error(traceback.format_exc())
    
    async def process_logs(self, cache):
        """
        Processa logs para o frontend.
        
        Args:
            cache: Dados do cache
        """
        logger.info("Processando logs para o frontend")
        
        try:
            logs = cache.get("logs", {})
            
            if not logs:
                logger.info("Nenhum log encontrado no cache")
                return
                
            # Extrair resumo
            log_summary = logs.get("summary", [])
            
            if log_summary:
                # Salvar resumo de logs para o frontend
                logs_file = self.frontend_data_dir / "logs_summary.json"
                with open(logs_file, "w", encoding="utf-8") as f:
                    json.dump(log_summary, f, indent=2, ensure_ascii=False)
                    
                logger.info("✅ Resumo de logs salvo")
                self.stats["files_generated"] += 1
            
        except Exception as e:
            logger.error(f"Erro ao processar logs: {e}")
            logger.error(traceback.format_exc())
    
    async def generate_insights(self, cache):
        """
        Gera insights baseados nos dados do cache.
        
        Args:
            cache: Dados do cache
        """
        logger.info("Gerando insights para o frontend")
        
        try:
            insights = []
            
            # Analisar todos os domínios para encontrar insights
            for domain, entities in cache.items():
                if domain in ["metadata", "logs", "dashboards", "alertas", "workloads"]:
                    continue
                    
                if not isinstance(entities, list):
                    continue
                    
                # Verificar entidades com erros
                domain_upper = domain.upper()
                entities_with_errors = []
                
                for entity in entities:
                    detailed_metrics = entity.get("detailed_metrics", {})
                    
                    # Verificar taxa de erro
                    error_rate = None
                    
                    if "error_rate" in detailed_metrics:
                        error_data = detailed_metrics["error_rate"]
                        if isinstance(error_data, list) and error_data:
                            for item in error_data:
                                if "percentage" in item:
                                    error_rate = item["percentage"]
                                    break
                    
                    if error_rate is not None and error_rate > 1.0:  # Mais de 1% de erros
                        entities_with_errors.append({
                            "name": entity.get("name", "Unknown"),
                            "domain": domain_upper,
                            "errorRate": error_rate
                        })
            
                # Criar insight se houver entidades com erros
                if entities_with_errors:
                    insights.append({
                        "id": f"error_rates_{domain_upper}",
                        "title": f"Taxa de erro elevada - {domain_upper}",
                        "description": f"Detectadas {len(entities_with_errors)} entidades com taxas de erro acima do normal.",
                        "severity": "warning",
                        "domain": domain_upper,
                        "data": entities_with_errors
                    })
            
            # Verificar problemas de alertas
            alert_violations = []
            
            for domain, entities in cache.items():
                if domain in ["metadata", "logs", "dashboards", "alertas", "workloads"]:
                    continue
                    
                if not isinstance(entities, list):
                    continue
                    
                for entity in entities:
                    alerts = entity.get("alerts", {})
                    violations = alerts.get("violations", [])
                    
                    for violation in violations:
                        if violation.get("level") in ["CRITICAL", "WARNING"]:
                            alert_violations.append({
                                "entity": entity.get("name", "Unknown"),
                                "domain": domain.upper(),
                                "level": violation.get("level"),
                                "label": violation.get("label")
                            })
            
            # Criar insight de alertas se houver violações
            if alert_violations:
                insights.append({
                    "id": "alert_violations",
                    "title": "Alertas ativos",
                    "description": f"Existem {len(alert_violations)} alertas ativos que precisam de atenção.",
                    "severity": "critical",
                    "domain": "ALERT",
                    "data": alert_violations
                })
            
            # Salvar insights para o frontend
            if insights:
                insights_file = self.frontend_data_dir / "insights.json"
                with open(insights_file, "w", encoding="utf-8") as f:
                    json.dump(insights, f, indent=2, ensure_ascii=False)
                    
                logger.info(f"✅ Gerados {len(insights)} insights")
                self.stats["files_generated"] += 1
            else:
                logger.info("Nenhum insight gerado")
                
        except Exception as e:
            logger.error(f"Erro ao gerar insights: {e}")
            logger.error(traceback.format_exc())
    
    async def generate_coverage_data(self, cache):
        """
        Gera dados de cobertura para o frontend.
        
        Args:
            cache: Dados do cache
        """
        logger.info("Gerando dados de cobertura para o frontend")
        
        try:
            # Obter cobertura e estatísticas
            coverage = cache.get("metadata", {}).get("coverage", {})
            
            if not coverage:
                logger.info("Nenhum dado de cobertura encontrado no cache")
                return
                
            # Calcular cobertura geral
            total_entities = 0
            monitored_entities = 0
            
            for domain, stats in coverage.items():
                if domain not in ["dashboards", "alertas"]:
                    domain_entities = stats.get("total_entities", 0)
                    total_entities += domain_entities
                    monitored_entities += stats.get("complete_entities", 0)
            
            # Criar dados de cobertura para o frontend
            frontend_coverage = {
                "timestamp": datetime.now().isoformat(),
                "total_entidades": total_entities,
                "monitoradas": monitored_entities,
                "porcentagem": round((monitored_entities / total_entities * 100) if total_entities > 0 else 0, 1),
                "por_dominio": {}
            }
            
            # Adicionar dados por domínio
            for domain, stats in coverage.items():
                if domain not in ["dashboards", "alertas"]:
                    domain_upper = domain.upper()
                    domain_entities = stats.get("total_entities", 0)
                    complete_entities = stats.get("complete_entities", 0)
                    
                    # Estimar entidades críticas (20% do total)
                    critical_entities = max(1, int(domain_entities * 0.2))
                    
                    frontend_coverage["por_dominio"][domain_upper] = {
                        "total": domain_entities,
                        "monitoradas": complete_entities,
                        "criticas": critical_entities
                    }
            
            # Salvar cobertura para o frontend
            coverage_file = self.frontend_data_dir / "cobertura.json"
            with open(coverage_file, "w", encoding="utf-8") as f:
                json.dump(frontend_coverage, f, indent=2, ensure_ascii=False)
                
            logger.info("✅ Dados de cobertura gerados")
            self.stats["files_generated"] += 1
            
        except Exception as e:
            logger.error(f"Erro ao gerar dados de cobertura: {e}")
            logger.error(traceback.format_exc())
    
    def generate_api_index(self):
        """
        Gera um índice de todos os arquivos JSON disponíveis para API.
        """
        logger.info("Gerando índice de API")
        
        try:
            # Listar todos os arquivos JSON no diretório
            json_files = list(self.frontend_data_dir.glob("*.json"))
            
            api_index = {
                "timestamp": datetime.now().isoformat(),
                "availableEndpoints": []
            }
            
            for file in json_files:
                endpoint_name = file.stem
                api_index["availableEndpoints"].append({
                    "name": endpoint_name,
                    "url": f"/api/data/{endpoint_name}",
                    "description": f"Dados de {endpoint_name} do New Relic"
                })
            
            # Salvar índice
            index_file = self.frontend_data_dir / "api_index.json"
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(api_index, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ Índice de API gerado com {len(api_index['availableEndpoints'])} endpoints")
            self.stats["files_generated"] += 1
            
        except Exception as e:
            logger.error(f"Erro ao gerar índice de API: {e}")
            logger.error(traceback.format_exc())
    
    def save_status(self):
        """
        Salva o status da integração.
        """
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "stats": self.stats,
                "availableFiles": [f.name for f in self.frontend_data_dir.glob("*.json")]
            }
            
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao salvar status da integração: {e}")

async def main():
    """Função principal"""
    integrator = FrontendIntegrator()
    await integrator.process_all_data()

if __name__ == "__main__":
    asyncio.run(main())
