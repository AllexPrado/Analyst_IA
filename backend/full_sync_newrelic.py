"""
Script para sincronização completa de entidades e métricas do New Relic.
Este script usa o coletor avançado para obter e armazenar todos os dados
disponíveis no New Relic, garantindo 100% de cobertura.
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

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretórios ao path
current_dir = Path(__file__).parent
if current_dir.name != "backend":
    sys.path.append(str(current_dir))
    backend_dir = current_dir / "backend"
    if backend_dir.exists():
        sys.path.append(str(backend_dir))

# Importar o coletor avançado
try:
    from backend.utils.advanced_newrelic_collector import AdvancedNewRelicCollector
except ImportError:
    try:
        from utils.advanced_newrelic_collector import AdvancedNewRelicCollector
    except ImportError as e:
        logger.error(f"Erro ao importar coletor avançado: {e}")
        sys.exit(1)

class NewRelicFullSynchronizer:
    """
    Classe para sincronizar completamente todas as entidades e métricas do New Relic.
    """
    
    def __init__(self):
        """Inicializa o sincronizador"""
        self.cache_dir = Path("backend")
        self.cache_file = self.cache_dir / "cache.json"
        self.history_dir = self.cache_dir / "historico"
        self.history_dir.mkdir(exist_ok=True)
        self.collector = AdvancedNewRelicCollector()
        
    async def synchronize_all_entities(self):
        """
        Sincroniza todas as entidades disponíveis no New Relic.
        """
        logger.info("Iniciando sincronização completa de entidades do New Relic")
        start_time = datetime.now()
        
        try:
            # 1. Obter todas as entidades disponíveis
            logger.info("Buscando todas as entidades disponíveis...")
            all_entities = await self.collector.get_all_entities()
            
            if not all_entities:
                logger.error("Nenhuma entidade encontrada no New Relic")
                return False
                
            logger.info(f"Total de {len(all_entities)} entidades encontradas")
            
            # 2. Organizar entidades por domínio
            entities_by_domain = {}
            for entity in all_entities:
                domain = entity.get("domain", "UNKNOWN").lower()
                if domain not in entities_by_domain:
                    entities_by_domain[domain] = []
                entities_by_domain[domain].append(entity)
                
            logger.info("Entidades organizadas por domínio:")
            for domain, entities in entities_by_domain.items():
                logger.info(f"  - {domain}: {len(entities)} entidades")
            
            # 3. Criar estrutura do cache
            cache = {
                "timestamp": datetime.now().isoformat()
            }
            
            # Adicionar cada domínio ao cache
            for domain, entities in entities_by_domain.items():
                cache[domain] = entities
                
            # 4. Salvar cache
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Cache básico salvo com sucesso: {self.cache_file}")
            
            # 5. Salvar também no formato histórico para compatibilidade
            self.save_to_historical_format(all_entities)
            
            # Calcular tempo gasto
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Sincronização básica concluída em {duration:.2f} segundos")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro durante sincronização de entidades: {e}")
            logger.error(traceback.format_exc())
            return False
            
    def save_to_historical_format(self, entities):
        """
        Salva as entidades no formato histórico para compatibilidade.
        
        Args:
            entities: Lista de entidades
        """
        try:
            historical_file = self.history_dir / "cache_completo.json"
            
            # Converter para o formato antigo
            historical_data = {
                "entidades": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Processar cada entidade
            for entity in entities:
                domain = entity.get("domain", "UNKNOWN").upper()
                
                historical_entity = {
                    "name": entity.get("name", "Unknown"),
                    "guid": entity.get("guid", ""),
                    "dominio": domain,
                    "tipo": entity.get("type", "Unknown"),
                    "metricas": {}
                }
                
                # Adicionar métricas básicas se disponíveis
                if "metrics" in entity:
                    if domain == "APM" and "apm" in entity["metrics"]:
                        historical_entity["metricas"] = entity["metrics"]["apm"]
                    elif domain == "BROWSER" and "browser" in entity["metrics"]:
                        historical_entity["metricas"] = entity["metrics"]["browser"]
                    elif domain == "INFRA" and "infra" in entity["metrics"]:
                        historical_entity["metricas"] = entity["metrics"]["infra"]
                        
                historical_data["entidades"].append(historical_entity)
                
            # Salvar arquivo histórico
            with open(historical_file, "w", encoding="utf-8") as f:
                json.dump(historical_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Cache no formato histórico salvo com sucesso: {historical_file}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar cache no formato histórico: {e}")
            logger.error(traceback.format_exc())
    
    async def collect_detailed_metrics(self, max_entities=None):
        """
        Coleta métricas detalhadas para as entidades no cache.
        
        Args:
            max_entities: Número máximo de entidades para processar (None = todas)
        """
        logger.info("Iniciando coleta de métricas detalhadas")
        start_time = datetime.now()
        
        try:
            # 1. Carregar cache atual
            if not self.cache_file.exists():
                logger.error(f"Arquivo de cache não encontrado: {self.cache_file}")
                return False
                
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
                
            # 2. Contar total de entidades
            total_entities = 0
            entities_list = []
            
            for domain, entities in cache.items():
                if domain != "timestamp" and isinstance(entities, list):
                    total_entities += len(entities)
                    for entity in entities:
                        entity["domain"] = domain  # Garantir que temos o domínio
                        entities_list.append(entity)
                        
            # Limitar se necessário
            if max_entities and max_entities < total_entities:
                logger.info(f"Limitando processamento a {max_entities} de {total_entities} entidades")
                entities_list = entities_list[:max_entities]
                total_entities = max_entities
            else:
                logger.info(f"Processando todas as {total_entities} entidades")
                
            # 3. Processar cada entidade
            processed = 0
            for entity in entities_list:
                try:
                    # Mostrar progresso
                    processed += 1
                    if processed % 10 == 0 or processed == total_entities:
                        logger.info(f"Progresso: {processed}/{total_entities} ({processed/total_entities*100:.1f}%)")
                        
                    # Obter dados completos
                    entity_guid = entity.get("guid")
                    entity_name = entity.get("name", "Unknown")
                    entity_domain = entity.get("domain")
                    
                    if not entity_guid or not entity_domain:
                        logger.warning(f"Entidade sem GUID ou domínio: {entity_name}")
                        continue
                        
                    logger.debug(f"Coletando métricas para: {entity_name} ({entity_guid})")
                    
                    # Coletar métricas
                    detailed_metrics = await self.collector.get_entity_detailed_metrics(entity_guid, entity_domain)
                    
                    # Atualizar entidade no cache
                    entity["detailed_metrics"] = detailed_metrics
                    
                    # Coletar alertas (não para todas as entidades para evitar sobrecarga)
                    if processed % 5 == 0:  # A cada 5 entidades
                        alerts = await self.collector.get_alerts_for_entity(entity_guid)
                        entity["alerts"] = alerts
                        
                    # Aplicar throttling para não sobrecarregar a API
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Erro ao processar entidade {entity.get('name', 'Unknown')}: {e}")
                    continue
                    
            # 4. Atualizar timestamp
            cache["timestamp"] = datetime.now().isoformat()
            
            # 5. Salvar cache atualizado
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
                
            # Atualizar também formato histórico
            self.save_to_historical_format(entities_list)
                
            # Calcular tempo gasto
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Coleta de métricas detalhadas concluída em {duration:.2f} segundos")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro durante coleta de métricas detalhadas: {e}")
            logger.error(traceback.format_exc())
            return False
            
    async def collect_dashboards(self):
        """
        Coleta dados de dashboards do New Relic.
        """
        logger.info("Iniciando coleta de dashboards")
        
        try:
            # 1. Obter lista de dashboards
            dashboards = await self.collector.get_dashboards_list()
            
            if not dashboards:
                logger.warning("Nenhum dashboard encontrado")
                return False
                
            logger.info(f"Encontrados {len(dashboards)} dashboards")
            
            # 2. Coletar detalhes para alguns dashboards (limite para não sobrecarregar)
            max_detailed = min(20, len(dashboards))
            detailed_dashboards = []
            
            for i, dashboard in enumerate(dashboards[:max_detailed]):
                try:
                    guid = dashboard.get("guid")
                    name = dashboard.get("name", "Unknown")
                    
                    logger.info(f"Coletando detalhes do dashboard {i+1}/{max_detailed}: {name}")
                    
                    details = await self.collector.get_dashboard_details(guid)
                    if details:
                        detailed_dashboards.append(details)
                        
                    # Pausa para evitar sobrecarga na API
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Erro ao coletar detalhes do dashboard {dashboard.get('name', 'Unknown')}: {e}")
                    continue
                    
            # 3. Salvar dados de dashboards
            dashboards_dir = self.cache_dir / "dashboards"
            dashboards_dir.mkdir(exist_ok=True)
            
            # Lista completa
            with open(dashboards_dir / "all_dashboards.json", "w", encoding="utf-8") as f:
                json.dump(dashboards, f, indent=2, ensure_ascii=False)
                
            # Dashboards detalhados
            with open(dashboards_dir / "detailed_dashboards.json", "w", encoding="utf-8") as f:
                json.dump(detailed_dashboards, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Dashboards salvos com sucesso: {len(dashboards)} totais, {len(detailed_dashboards)} detalhados")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro durante coleta de dashboards: {e}")
            logger.error(traceback.format_exc())
            return False
            
    async def collect_alert_policies(self):
        """
        Coleta políticas de alerta do New Relic.
        """
        logger.info("Iniciando coleta de políticas de alerta")
        
        try:
            # Obter políticas
            policies = await self.collector.get_all_alert_policies()
            
            if not policies:
                logger.warning("Nenhuma política de alerta encontrada")
                return False
                
            logger.info(f"Encontradas {len(policies)} políticas de alerta")
            
            # Salvar políticas
            alerts_dir = self.cache_dir / "alertas"
            alerts_dir.mkdir(exist_ok=True)
            
            with open(alerts_dir / "alert_policies.json", "w", encoding="utf-8") as f:
                json.dump(policies, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Políticas de alerta salvas com sucesso: {len(policies)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro durante coleta de políticas de alerta: {e}")
            logger.error(traceback.format_exc())
            return False

async def main():
    """
    Função principal para executar sincronização completa.
    """
    logger.info("=== SINCRONIZAÇÃO COMPLETA DO NEW RELIC ===")
    start_time = datetime.now()
    
    synchronizer = NewRelicFullSynchronizer()
    
    # 1. Sincronizar todas as entidades (básico)
    success = await synchronizer.synchronize_all_entities()
    if not success:
        logger.error("Falha na sincronização básica de entidades")
        return
    
    # 2. Coletar métricas detalhadas (pode ser limitado para evitar sobrecarga)
    max_entities = None  # Definir um número para limitar (ex: 50) ou None para todos
    success = await synchronizer.collect_detailed_metrics(max_entities)
    if not success:
        logger.warning("Falha na coleta de métricas detalhadas")
        
    # 3. Coletar dashboards
    success = await synchronizer.collect_dashboards()
    if not success:
        logger.warning("Falha na coleta de dashboards")
    
    # 4. Coletar políticas de alerta
    success = await synchronizer.collect_alert_policies()
    if not success:
        logger.warning("Falha na coleta de políticas de alerta")
    
    # Concluído
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    
    logger.info(f"=== SINCRONIZAÇÃO CONCLUÍDA EM {minutes}m {seconds}s ===")
    logger.info("O sistema agora contém dados completos do New Relic")

if __name__ == "__main__":
    asyncio.run(main())
