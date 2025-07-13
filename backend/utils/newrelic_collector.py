import os
import logging
from typing import Dict, List, Any, Optional
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio
import random
import time
import json
import traceback
# Importa utilitário centralizado
from utils.newrelic_common import (
    execute_nrql_query_common,
    execute_graphql_query_common,
    log_info, log_warning, log_error
)

load_dotenv()


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

NEW_RELIC_API_KEY = os.getenv("NEW_RELIC_API_KEY")
NEW_RELIC_QUERY_KEY = os.getenv("NEW_RELIC_QUERY_KEY")
NEW_RELIC_ACCOUNT_ID = os.getenv("NEW_RELIC_ACCOUNT_ID")

# Configurações de timeout ajustadas para prevenir bloqueios no frontend
# Valor em segundos (30 segundos é um bom equilíbrio entre tempo de espera e prevenção de erros)
DEFAULT_TIMEOUT = 30.0  # Timeout padrão de 30 segundos para requisições HTTP
MAX_RETRIES = 2  # Número máximo de tentativas
RETRY_DELAY = 1.0  # Tempo de espera entre tentativas (segundos)


if not NEW_RELIC_API_KEY or not NEW_RELIC_ACCOUNT_ID or not NEW_RELIC_QUERY_KEY:
    log_error("NEW_RELIC_API_KEY, NEW_RELIC_QUERY_KEY e NEW_RELIC_ACCOUNT_ID são obrigatórios!")
    raise RuntimeError("NEW_RELIC_API_KEY, NEW_RELIC_QUERY_KEY e NEW_RELIC_ACCOUNT_ID são obrigatórios!")

# Log para confirmar que as credenciais foram carregadas corretamente
logger.info(f"New Relic Account ID carregado: {NEW_RELIC_ACCOUNT_ID}")
logger.info(f"New Relic API Key carregada: {NEW_RELIC_API_KEY[:5]}...")

PERIODOS = {
    "30min": "SINCE 30 MINUTES AGO",
    "24h": "SINCE 24 HOURS AGO",
    "7d": "SINCE 7 DAYS AGO",
    "30d": "SINCE 30 DAYS AGO"
}

# Lista de todos os domínios conhecidos do New Relic (apenas os suportados)
DOMINIOS_NEWRELIC = [
    "APM", "BROWSER", "INFRA", "DB", "MOBILE", "IOT", "SERVERLESS", "SYNTH", "EXT"
]
# Domínios que DEVEM ser ignorados (não são entidades instrumentadas ou são dashboards/alertas)
DOMINIOS_IGNORADOS = [
    "AIOPS", "VIZ", "UNINSTRUMENTED", "UNKNOWN", "DASHBOARD", "ALERT", "WORKLOAD", "INSIGHTS"
]

# Controle de Rate Limiting Global
class RateLimitController:
    def __init__(self):
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_reset_time = 0
        self.consecutive_failures = 0
        self.max_failures = 10
        self.min_delay = 1.0  # 1 segundo mínimo entre requests
        self.max_delay = 300.0  # 5 minutos máximo
        self.base_backoff = 2.0
        
        # Circuit Breaker States
        self.circuit_state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.circuit_opened_at = 0
        self.circuit_timeout = 60  # 1 minuto para tentar novamente
        self.success_threshold = 3  # Sucessos necessários para fechar o circuito
        self.consecutive_successes = 0
        
    def is_circuit_open(self):
        """Verifica se o circuit breaker está aberto (bloqueando requests)"""
        if self.circuit_state == "OPEN":
            # Verifica se é hora de tentar novamente (HALF_OPEN)
            if time.time() - self.circuit_opened_at > self.circuit_timeout:
                logger.info("Circuit breaker: Transicionando de OPEN para HALF_OPEN")
                self.circuit_state = "HALF_OPEN"
                self.consecutive_successes = 0
                return False
            return True
        return False
        
    async def wait_if_needed(self):
        """Implementa rate limiting inteligente com circuit breaker e backoff adaptativo"""
        # Circuit breaker: se está aberto, bloqueia a requisição
        if self.is_circuit_open():
            logger.warning(f"Circuit breaker OPEN - Bloqueando requisição. Tempo restante: {self.circuit_timeout - (time.time() - self.circuit_opened_at):.1f}s")
            raise Exception("Circuit breaker OPEN - New Relic API temporariamente indisponível")
        
        current_time = time.time()
        
        # Se tivemos muitas falhas consecutivas, aumenta o delay base
        if self.consecutive_failures > 3:
            delay = min(self.base_backoff ** min(self.consecutive_failures, 8), self.max_delay)
            # Adiciona jitter para evitar thundering herd
            jitter = delay * 0.1 * random.random()
            logger.info(f"Backoff adaptativo: {delay:.2f}s + {jitter:.2f}s jitter ({self.consecutive_failures} falhas consecutivas)")
            await asyncio.sleep(delay + jitter)
        
        # Delay mínimo entre requests para evitar sobrecarga
        elif current_time - self.last_request_time < self.min_delay:
            wait_time = self.min_delay - (current_time - self.last_request_time)
            await asyncio.sleep(wait_time)
            
        self.last_request_time = time.time()
        self.request_count += 1
    
    def record_failure(self, is_rate_limit=False):
        """Registra uma falha no controlador, potencialmente ativando circuit breaker"""
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        
        if is_rate_limit:
            # Rate limits são críticos, ativamos o circuit breaker mais rapidamente
            logger.warning(f"Rate limit detectado! ({self.consecutive_failures} falhas consecutivas)")
            if self.consecutive_failures >= 3:
                logger.error("Circuit breaker ABERTO devido a múltiplos rate limits")
                self.circuit_state = "OPEN"
                self.circuit_opened_at = time.time()
                self.circuit_timeout = min(60 * (2 ** min(self.consecutive_failures - 3, 3)), 600)  # Máximo 10 min
        elif self.consecutive_failures >= self.max_failures:
            logger.error(f"Circuit breaker ABERTO devido a {self.consecutive_failures} falhas consecutivas")
            self.circuit_state = "OPEN"
            self.circuit_opened_at = time.time()
            self.circuit_timeout = min(30 * (2 ** min(self.consecutive_failures - self.max_failures, 3)), 600)  # Máximo 10 min
    
    def record_success(self):
        """Registra um sucesso, possivelmente fechando o circuit breaker"""
        if self.circuit_state == "HALF_OPEN":
            self.consecutive_successes += 1
            if self.consecutive_successes >= self.success_threshold:
                logger.info(f"Circuit breaker FECHADO após {self.consecutive_successes} sucessos")
                self.circuit_state = "CLOSED"
                self.consecutive_failures = 0
        
        self.consecutive_failures = 0
    
    def get_status(self):
        """Retorna status detalhado do rate controller"""
        return {
            "circuit_state": self.circuit_state,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "request_count": self.request_count,
            "last_request_time": self.last_request_time,
            "circuit_opened_at": self.circuit_opened_at if self.circuit_state == "OPEN" else None,
            "time_until_retry": max(0, self.circuit_timeout - (time.time() - self.circuit_opened_at)) if self.circuit_state == "OPEN" else 0
        }

# Instância global do controlador de rate limit
rate_controller = RateLimitController()

class NewRelicCollector:
    # 1. Cobertura de Novos Domínios (Serverless, IOT, etc)
    async def collect_entity_serverless(self, guid):
        """
        Coleta dados de entidades Serverless (Funções Lambda, etc)
        """
        try:
            query = f"SELECT * FROM ServerlessSample WHERE entity.guid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
            result = await self.execute_nrql_query(query)
            return result if result else []
        except Exception as e:
            logger.warning(f"Erro ao coletar ServerlessSample para entidade {guid}: {e}")
            return []

    async def collect_entity_dependencies(self, guid):
        """
        Coleta dependências diretas da entidade (upstream e downstream)
        
        Args:
            guid (str): GUID da entidade
            
        Returns:
            dict: Dicionário com as dependências upstream e downstream categorizadas
                 (servicos_externos, bancos_dados, outros) em cada direção
        """
        try:
            logger.info(f"Coletando dependências para entidade com GUID: {guid}")
            
            # Estrutura para armazenar as dependências
            dependencies = {
                "upstream": {
                    "servicos_externos": [],
                    "bancos_dados": [],
                    "outros": []
                },
                "downstream": {
                    "servicos_externos": [],
                    "bancos_dados": [],
                    "outros": []
                },
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "entity_guid": guid,
                    "total_upstream": 0,
                    "total_downstream": 0
                }
            }
            
            # Buscar dependências upstream (que a entidade depende)
            upstream_query = f"""
            {{
              actor {{
                entity(guid: \"{guid}\") {{
                  upstreamRelationships {{
                    source {{ guid name entityType domain }}
                    target {{ guid name entityType domain }}
                    type
                  }}
                }}
              }}
            }}
            """
            
            # Buscar dependências downstream (que dependem da entidade)
            downstream_query = f"""
            {{
              actor {{
                entity(guid: \"{guid}\") {{
                  downstreamRelationships {{
                    source {{ guid name entityType domain }}
                    target {{ guid name entityType domain }}
                    type
                  }}
                }}
              }}
            }}
            """
            
            headers = {'Api-Key': self.api_key, 'Content-Type': 'application/json'}
            await self.rate_controller.wait_if_needed()
            
            # Função auxiliar para categorizar e processar dependências
            def process_entity_for_dependency(entity_data, direction):
                if not entity_data or not entity_data.get('guid'):
                    return None
                    
                dependency = {
                    "nome": entity_data.get('name', 'Desconhecido'),
                    "guid": entity_data.get('guid'),
                    "tipo": entity_data.get('entityType', 'UNKNOWN'),
                    "dominio": entity_data.get('domain', 'UNKNOWN')
                }
                
                # Categorizar dependência
                entity_type = entity_data.get('entityType', '').lower()
                if 'database' in entity_type or 'db' in entity_type or entity_data.get('domain') == 'DB':
                    dependencies[direction]['bancos_dados'].append(dependency)
                    return 'bancos_dados'
                elif ('service' in entity_type or 'api' in entity_type 
                      or 'application' in entity_type or entity_data.get('domain') in ['APM', 'BROWSER']):
                    dependencies[direction]['servicos_externos'].append(dependency)
                    return 'servicos_externos'
                else:
                    dependencies[direction]['outros'].append(dependency)
                    return 'outros'
            
            # Coletar dependências upstream
            try:
                upstream_count = 0
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                    async with session.post(self.base_url, headers=headers, json={"query": upstream_query}) as response:
                        if response.status == 200:
                            data = await response.json()
                            upstream_relationships = data.get("data", {}).get("actor", {}).get("entity", {}).get("upstreamRelationships", [])
                            
                            if upstream_relationships:
                                for rel in upstream_relationships:
                                    # Em upstream, olhamos para o source (quem fornece recursos para nossa entidade)
                                    source = rel.get('source', {})
                                    if source and process_entity_for_dependency(source, 'upstream'):
                                        upstream_count += 1
                                
                                logger.info(f"Encontradas {upstream_count} dependências upstream para entidade {guid}")
                                dependencies["metadata"]["total_upstream"] = upstream_count
                            else:
                                logger.info(f"Nenhuma dependência upstream encontrada para entidade {guid}")
                        else:
                            error_response = await response.text()
                            logger.warning(f"Erro ao coletar dependências upstream. Status: {response.status}. Resposta: {error_response[:200]}")
            except aiohttp.ClientError as e:
                logger.warning(f"Erro de conexão ao coletar dependências upstream para entidade {guid}: {e}")
            except Exception as e:
                logger.error(f"Erro ao processar dependências upstream: {e}")
            
            # Coletar dependências downstream
            try:
                downstream_count = 0
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                    async with session.post(self.base_url, headers=headers, json={"query": downstream_query}) as response:
                        if response.status == 200:
                            data = await response.json()
                            downstream_relationships = data.get("data", {}).get("actor", {}).get("entity", {}).get("downstreamRelationships", [])
                            
                            if downstream_relationships:
                                for rel in downstream_relationships:
                                    # Em downstream, olhamos para o target (quem consome recursos da nossa entidade)
                                    target = rel.get('target', {})
                                    if target and process_entity_for_dependency(target, 'downstream'):
                                        downstream_count += 1
                                
                                logger.info(f"Encontradas {downstream_count} dependências downstream para entidade {guid}")
                                dependencies["metadata"]["total_downstream"] = downstream_count
                            else:
                                logger.info(f"Nenhuma dependência downstream encontrada para entidade {guid}")
                        else:
                            error_response = await response.text()
                            logger.warning(f"Erro ao coletar dependências downstream. Status: {response.status}. Resposta: {error_response[:200]}")
            except aiohttp.ClientError as e:
                logger.warning(f"Erro de conexão ao coletar dependências downstream para entidade {guid}: {e}")
            except Exception as e:
                logger.error(f"Erro ao processar dependências downstream: {e}")
            
            # Limpar categorias vazias
            total_deps = 0
            for direction in ["upstream", "downstream"]:
                for category in list(dependencies[direction].keys()):
                    if not dependencies[direction][category]:
                        del dependencies[direction][category]
                    else:
                        total_deps += len(dependencies[direction][category])
            
            # Log final
            if total_deps > 0:
                logger.info(f"Total de {total_deps} dependências coletadas para entidade {guid}")
            else:
                logger.info(f"Nenhuma dependência encontrada para entidade {guid}")
            
            return dependencies
            
        except Exception as e:
            error_msg = f"Erro ao coletar dependências para entidade {guid}: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Sempre retorna uma estrutura válida mesmo em caso de erro
            return {
                "upstream": {}, 
                "downstream": {},
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "entity_guid": guid,
                    "total_upstream": 0,
                    "total_downstream": 0,
                    "error": str(e)
                }
            }

    async def collect_entity_iot(self, guid):
        """
        Coleta dados de entidades IoT (caso disponíveis)
        """
        try:
            query = f"SELECT * FROM IoTSample WHERE entity.guid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
            result = await self.execute_nrql_query(query)
            return result if result else []
        except Exception as e:
            logger.warning(f"Erro ao coletar IoTSample para entidade {guid}: {e}")
            return []

    # 2. Aprimorar Diagnóstico/Explainability
    async def explain_diagnosis(self, entity):
        """
        Explica o diagnóstico da entidade (explicabilidade) com análise mais detalhada.
        """
        try:
            explanations = []
            error_rate = None
            for period, metrics in entity.get('metricas', {}).items():
                if isinstance(metrics, dict) and 'error_rate' in metrics:
                    error_rate = metrics['error_rate']
            if error_rate and error_rate > 0.05:
                if entity.get('deployments'):
                    explanations.append("Aumento de erros após deploy recente. Verifique código e dependências.")
                else:
                    explanations.append("Taxa de erro elevada. Verifique logs e dependências.")
            if entity.get('health_status', {}).get('healthStatus') == 'CRITICAL':
                explanations.append("Entidade em estado crítico de saúde.")
            if entity.get('dependency_status'):
                for dep in entity['dependency_status']:
                    if dep.get('errorCount', 0) > 0:
                        explanations.append(f"Dependência {dep.get('externalServiceName')} com erros detectados.")
            if not explanations:
                explanations.append("Sem anomalias críticas detectadas.")
            return " \\n".join(explanations)
        except Exception as e:
            logger.warning(f"Erro ao explicar diagnóstico: {e}")
            return "Erro ao gerar explicação."

    # 3. Aprimorar Topologia
    async def build_entity_topology(self, guid):
        """
        Constrói grafo/topologia de dependências da entidade, incluindo upstream/downstream e pontos de falha.
        """
        try:
            rels = await self.collect_entity_related_entities(guid)
            nodes = set()
            edges = []
            critical_edges = []
            for rel in rels:
                src = rel.get('source', {}).get('guid')
                tgt = rel.get('target', {}).get('guid')
                if src and tgt:
                    nodes.add(src)
                    nodes.add(tgt)
                    edge = {'source': src, 'target': tgt, 'type': rel.get('type')}
                    edges.append(edge)
                    # Detecta ponto de falha se type for 'CRITICAL_DEPENDENCY'
                    if rel.get('type') == 'CRITICAL_DEPENDENCY':
                        critical_edges.append(edge)
            return {'nodes': list(nodes), 'edges': edges, 'critical_edges': critical_edges}
        except Exception as e:
            logger.warning(f"Erro ao construir topologia: {e}")
            return {}

    # 4. Aprimorar User Experience
    async def collect_entity_user_experience(self, guid):
        """
        Coleta dados de experiência do usuário (impacto, regiões, dispositivos, latência, erros por device/region)
        """
        try:
            queries = {
                "affected_users": f"SELECT uniqueCount(userId) as users FROM TransactionError WHERE entity.guid = '{guid}' SINCE 24 HOURS AGO",
                "regions": f"SELECT count(*) FROM Transaction FACET countryCode WHERE entity.guid = '{guid}' SINCE 24 HOURS AGO LIMIT 10",
                "devices": f"SELECT count(*) FROM MobileSession FACET deviceType WHERE entityGuid = '{guid}' SINCE 24 HOURS AGO LIMIT 10",
                "latency_by_region": f"SELECT average(duration) FROM Transaction FACET countryCode WHERE entity.guid = '{guid}' SINCE 24 HOURS AGO LIMIT 10",
                "errors_by_device": f"SELECT count(*) FROM TransactionError FACET deviceType WHERE entityGuid = '{guid}' SINCE 24 HOURS AGO LIMIT 10"
            }
            results = {}
            for key, q in queries.items():
                res = await self.execute_nrql_query(q)
                if res:
                    results[key] = res
            return results
        except Exception as e:
            logger.warning(f"Erro ao coletar user experience para entidade {guid}: {e}")
            return {}

    # 5. Aprimorar Performance (ajuste de limites e paralelismo)
    async def collect_entities_with_metrics(self):
        """
        Coleta entidades e suas respectivas métricas com ajuste dinâmico de paralelismo para ambientes grandes.
        """
        try:
            entities = await self.collect_entities()
            logger.info(f"Coletadas {len(entities)} entidades base. Coletando métricas...")
            # Ajuste dinâmico: reduz paralelismo se > 50 entidades
            MAX_CONCURRENT = 10 if len(entities) < 50 else 3
            semaphore = asyncio.Semaphore(MAX_CONCURRENT)
            async def process_entity_with_semaphore(entity):
                async with semaphore:
                    return await self.collect_entity_metrics(entity)
            processed_entities = await asyncio.gather(
                *[process_entity_with_semaphore(entity) for entity in entities],
                return_exceptions=True
            )
            valid_entities = []
            errors = 0
            for result in processed_entities:
                if isinstance(result, Exception):
                    errors += 1
                    logger.error(f"Erro ao processar entidade: {result}")
                elif result.get('metricas') and any(
                        isinstance(v, dict) and v for k, v in result['metricas'].items() if k != 'timestamp'):
                    valid_entities.append(result)
            logger.info(f"Coleta concluída: {len(valid_entities)} entidades válidas com métricas, {errors} erros")
            return valid_entities
        except Exception as e:
            logger.error(f"Erro na coleta de entidades com métricas: {e}")
            logger.error(traceback.format_exc())
            return []

    # 6. Aprimorar Error Handling
    async def execute_nrql_query(self, query: str, timeout: int = None) -> Dict:
        """
        Executa query NRQL usando utilitário centralizado, com logging detalhado de erros e tentativas.
        """
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        graphql_query = f"""
        {{
          actor {{
            account(id: {self.account_id}) {{
              nrql(query: \"\"\"{query}\"\"\") {{
                results
              }}
            }}
          }}
        }}
        """
        try:
            return await execute_nrql_query_common(
                graphql_query,
                headers={'Api-Key': self.api_key, 'Content-Type': 'application/json'},
                url=self.base_url,
                timeout=timeout,
                max_retries=MAX_RETRIES,
                retry_delay=RETRY_DELAY
            )
        except Exception as e:
            logger.error(f"Erro ao executar NRQL: {query[:80]}... | Erro: {e}")
            raise

    # 7. Aprimorar Integração com Chat (estruturação de saída)
    def format_entity_for_chat(self, entity: dict) -> dict:
        """
        Estrutura os dados da entidade para integração direta com chat/diagnóstico.
        """
        return {
            "nome": entity.get('name'),
            "dominio": entity.get('domain'),
            "tipo": entity.get('entityType'),
            "saude": entity.get('health_status', {}).get('healthStatus'),
            "metricas": entity.get('metricas'),
            "explicacao": entity.get('diagnosis_explanation'),
            "alertas": entity.get('alertas'),
            "deployments": entity.get('deployments'),
            "dependencias": entity.get('dependencias'),
            "topologia": entity.get('topology'),
            "user_experience": entity.get('user_experience'),
            "owners": entity.get('owners'),
            "logs": entity.get('logs'),
            "crashes_mobile": entity.get('mobile_crashes'),
            "db_queries": entity.get('db_queries'),
            "traces": entity.get('traces'),
            "workloads": entity.get('workloads'),
            "custom_events": entity.get('custom_events'),
            "synthetics": entity.get('synthetics'),
            "dashboards": entity.get('dashboards'),
            "infra_events": entity.get('infra_events'),
            "integration_events": entity.get('integration_events'),
            "alert_deployment_correlation": entity.get('alert_deployment_correlation'),
            "log_patterns": entity.get('log_patterns'),
            "detalhe": entity.get('detalhe'),
            "timestamp": entity.get('metricas', {}).get('timestamp')
        }
    async def collect_entity_health_status(self, guid):
        """
        Coleta status de saúde da entidade (health status)
        """
        try:
            query = f"""
            {{
              actor {{
                entity(guid: \"{guid}\") {{
                  healthStatus
                  reporting
                  alertSeverity
                }}
              }}
            }}
            """
            headers = {'Api-Key': self.api_key, 'Content-Type': 'application/json'}
            await self.rate_controller.wait_if_needed()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(self.base_url, headers=headers, json={"query": query}) as response:
                    if response.status == 200:
                        data = await response.json()
                        entity = data.get("data", {}).get("actor", {}).get("entity", {})
                        return entity
                    else:
                        return {}
        except Exception as e:
            logger.warning(f"Erro ao coletar health status para entidade {guid}: {e}")
            return {}

    async def collect_entity_time_series(self, guid):
        """
        Coleta séries temporais das principais métricas para análise de tendências/anomalias
        """
        try:
            queries = {
                "apdex": f"SELECT apdexScore FROM Metric WHERE entity.guid = '{guid}' TIMESERIES 5 minutes SINCE 24 HOURS AGO",
                "error_rate": f"SELECT errorRate FROM Metric WHERE entity.guid = '{guid}' TIMESERIES 5 minutes SINCE 24 HOURS AGO",
                "throughput": f"SELECT newRelic.throughput FROM Metric WHERE entity.guid = '{guid}' TIMESERIES 5 minutes SINCE 24 HOURS AGO",
                "response_time": f"SELECT average(duration) FROM Transaction WHERE entity.guid = '{guid}' TIMESERIES 5 minutes SINCE 24 HOURS AGO"
            }
            results = {}
            for key, q in queries.items():
                res = await self.execute_nrql_query(q)
                if res:
                    results[key] = res
            return results
        except Exception as e:
            logger.warning(f"Erro ao coletar time series para entidade {guid}: {e}")
            return {}

    async def correlate_alerts_with_deployments(self, entity):
        """
        Correlaciona alertas/violations com deployments recentes
        """
        try:
            alerts = entity.get('alertas', [])
            deployments = entity.get('deployments', [])
            if not alerts or not deployments:
                return []
            correlations = []
            for alert in alerts:
                for dep in deployments:
                    if dep.get('timestamp') and alert.get('openedAt') and abs(dep['timestamp'] - alert['openedAt']) < 3600*2:
                        correlations.append({"alert": alert, "deployment": dep})
            return correlations
        except Exception as e:
            logger.warning(f"Erro ao correlacionar alertas e deployments: {e}")
            return []

    async def collect_entity_dependency_status(self, guid):
        """
        Coleta status/latência/erros de dependências externas
        """
        try:
            query = f"SELECT * FROM ExternalService WHERE entity.guid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
            result = await self.execute_nrql_query(query)
            if result and isinstance(result, list) and len(result) > 0:
                return result
            return []
        except Exception as e:
            logger.warning(f"Erro ao coletar dependências externas para entidade {guid}: {e}")
            return []

    async def collect_entity_user_experience(self, guid):
        """
        Coleta dados de experiência do usuário (impacto, regiões, dispositivos)
        """
        try:
            queries = {
                "affected_users": f"SELECT uniqueCount(userId) as users FROM TransactionError WHERE entity.guid = '{guid}' SINCE 24 HOURS AGO",
                "regions": f"SELECT count(*) FROM Transaction FACET countryCode WHERE entity.guid = '{guid}' SINCE 24 HOURS AGO LIMIT 10",
                "devices": f"SELECT count(*) FROM MobileSession FACET deviceType WHERE entityGuid = '{guid}' SINCE 24 HOURS AGO LIMIT 10"
            }
            results = {}
            for key, q in queries.items():
                res = await self.execute_nrql_query(q)
                if res:
                    results[key] = res
            return results
        except Exception as e:
            logger.warning(f"Erro ao coletar user experience para entidade {guid}: {e}")
            return {}

    async def analyze_logs_for_patterns(self, guid):
        """
        Analisa logs/eventos customizados para padrões, clusters, sentimentos
        """
        try:
            logs = await self.collect_entity_logs(guid)
            # Exemplo simples: clusterizar por mensagem de erro
            clusters = {}
            for log in logs:
                msg = log.get('message', 'unknown')
                clusters.setdefault(msg, []).append(log)
            return clusters
        except Exception as e:
            logger.warning(f"Erro ao analisar logs para padrões: {e}")
            return {}

    async def collect_entity_owners(self, entity):
        """
        Coleta informações organizacionais (owner, squad, team) via tags
        """
        try:
            tags = entity.get('tags', [])
            owners = {}
            for tag in tags:
                if tag['key'].lower() in ['owner', 'squad', 'team', 'responsavel']:
                    owners[tag['key']] = tag['values']
            return owners
        except Exception as e:
            logger.warning(f"Erro ao coletar owners/squad/team: {e}")
            return {}

    async def build_entity_topology(self, guid):
        """
        Constrói grafo/topologia de dependências da entidade
        """
        try:
            rels = await self.collect_entity_related_entities(guid)
            nodes = set()
            edges = []
            for rel in rels:
                src = rel.get('source', {}).get('guid')
                tgt = rel.get('target', {}).get('guid')
                if src and tgt:
                    nodes.add(src)
                    nodes.add(tgt)
                    edges.append({'source': src, 'target': tgt, 'type': rel.get('type')})
            return {'nodes': list(nodes), 'edges': edges}
        except Exception as e:
            logger.warning(f"Erro ao construir topologia: {e}")
            return {}

    async def explain_diagnosis(self, entity):
        """
        Explica o diagnóstico da entidade (explicabilidade)
        """
        try:
            # Exemplo: se error_rate alto após deploy, explique
            error_rate = None
            for period, metrics in entity.get('metricas', {}).items():
                if isinstance(metrics, dict) and 'error_rate' in metrics:
                    error_rate = metrics['error_rate']
            if error_rate and error_rate > 0.05:
                if entity.get('deployments'):
                    return f"Aumento de erros após deploy recente. Verifique código e dependências."
                else:
                    return f"Taxa de erro elevada. Verifique logs e dependências."
            return "Sem anomalias críticas detectadas."
        except Exception as e:
            logger.warning(f"Erro ao explicar diagnóstico: {e}")
            return "Erro ao gerar explicação."
    async def collect_entity_mobile_crashes(self, guid):
        """
        Coleta eventos de crash mobile (MobileCrash, MobileHandledException) incluindo stacktrace/backtrace, device info, app version, e contexto de sessão.
        """
        try:
            crash_query = f"SELECT * FROM MobileCrash WHERE entityGuid = '{guid}' SINCE 30 MINUTES AGO LIMIT 20"
            crash_result = await self.execute_nrql_query(crash_query)
            handled_query = f"SELECT * FROM MobileHandledException WHERE entityGuid = '{guid}' SINCE 30 MINUTES AGO LIMIT 20"
            handled_result = await self.execute_nrql_query(handled_query)
            # Enriquecimento: busca contexto de sessão para cada crash
            crashes = []
            for crash in (crash_result or []) + (handled_result or []):
                session_id = crash.get('sessionId')
                if session_id:
                    session_query = f"SELECT * FROM MobileSession WHERE sessionId = '{session_id}' LIMIT 1"
                    session_info = await self.execute_nrql_query(session_query)
                    if session_info and isinstance(session_info, list):
                        crash['session_context'] = session_info[0]
                crashes.append(crash)
            return crashes
        except Exception as e:
            logger.warning(f"Erro ao coletar MobileCrash/MobileHandledException para entidade {guid}: {e}")
            return []

    async def collect_entity_db_queries(self, guid):
        """
        Coleta queries SQL recentes (DatastoreSample) para a entidade
        """
        try:
            query = f"SELECT * FROM DatastoreSample WHERE entity.guid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
            result = await self.execute_nrql_query(query)
            if result and isinstance(result, list) and len(result) > 0:
                return result
            return []
        except Exception as e:
            logger.warning(f"Erro ao coletar DatastoreSample para entidade {guid}: {e}")
            return []

    async def collect_entity_transaction_attributes(self, guid):
        """
        Coleta atributos detalhados de transações (Transaction, TransactionError) para a entidade
        """
        try:
            tx_query = f"SELECT * FROM Transaction WHERE entity.guid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
            tx_result = await self.execute_nrql_query(tx_query)
            err_query = f"SELECT * FROM TransactionError WHERE entity.guid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
            err_result = await self.execute_nrql_query(err_query)
            attributes = []
            if tx_result and isinstance(tx_result, list):
                attributes.extend(tx_result)
            if err_result and isinstance(err_result, list):
                attributes.extend(err_result)
            return attributes
        except Exception as e:
            logger.warning(f"Erro ao coletar atributos de transação para entidade {guid}: {e}")
            return []
    async def collect_entity_related_entities(self, guid):
        """
        Coleta entidades relacionadas (dependências, upstream/downstream, etc)
        """
        try:
            query = f"""
            {{
              actor {{
                entity(guid: \"{guid}\") {{
                  relationships {{
                    source {{ guid name entityType domain }}
                    target {{ guid name entityType domain }}
                    type
                  }}
                }}
              }}
            }}
            """
            headers = {'Api-Key': self.api_key, 'Content-Type': 'application/json'}
            await self.rate_controller.wait_if_needed()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(self.base_url, headers=headers, json={"query": query}) as response:
                    if response.status == 200:
                        data = await response.json()
                        rels = data.get("data", {}).get("actor", {}).get("entity", {}).get("relationships", [])
                        return rels or []
                    else:
                        return []
        except Exception as e:
            logger.warning(f"Erro ao coletar entidades relacionadas para {guid}: {e}")
            return []

    async def collect_entity_integration_events(self, guid):
        """
        Coleta eventos de integração (IntegrationEvent) para a entidade
        """
        try:
            query = f"SELECT * FROM IntegrationEvent WHERE entity.guid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
            result = await self.execute_nrql_query(query)
            if result and isinstance(result, list) and len(result) > 0:
                return result
            return []
        except Exception as e:
            logger.warning(f"Erro ao coletar IntegrationEvents para entidade {guid}: {e}")
            return []

    async def collect_entity_infrastructure_events(self, guid):
        """
        Coleta eventos de infraestrutura (InfrastructureEvent) para a entidade
        """
        try:
            query = f"SELECT * FROM InfrastructureEvent WHERE entity.guid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
            result = await self.execute_nrql_query(query)
            if result and isinstance(result, list) and len(result) > 0:
                return result
            return []
        except Exception as e:
            logger.warning(f"Erro ao coletar InfrastructureEvents para entidade {guid}: {e}")
            return []

    async def collect_entity_logs(self, guid):
        """
        Coleta logs recentes para a entidade (se disponíveis)
        """
        try:
            query = f"SELECT * FROM Log WHERE entity.guid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
            result = await self.execute_nrql_query(query)
            if result and isinstance(result, list) and len(result) > 0:
                return result
            return []
        except Exception as e:
            logger.warning(f"Erro ao coletar logs para entidade {guid}: {e}")
            return []

    async def collect_entity_alert_policies(self, guid):
        """
        Coleta alert policies e conditions associadas à entidade
        """
        try:
            query = f"""
            {{
              actor {{
                entity(guid: \"{guid}\") {{
                  alertSeverity
                  alertViolationsOpen: alertViolations(state: OPEN) {{ id label level openedAt policyName conditionName }}
                  alertViolationsClosed: alertViolations(state: CLOSED) {{ id label level closedAt policyName conditionName }}
                }}
              }}
            }}
            """
            headers = {'Api-Key': self.api_key, 'Content-Type': 'application/json'}
            await self.rate_controller.wait_if_needed()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(self.base_url, headers=headers, json={"query": query}) as response:
                    if response.status == 200:
                        data = await response.json()
                        entity = data.get("data", {}).get("actor", {}).get("entity", {})
                        return {
                            "alertSeverity": entity.get("alertSeverity"),
                            "alertViolationsOpen": entity.get("alertViolationsOpen", []),
                            "alertViolationsClosed": entity.get("alertViolationsClosed", [])
                        }
                    else:
                        return {}
        except Exception as e:
            logger.warning(f"Erro ao coletar alert policies para entidade {guid}: {e}")
            return {}
    async def collect_entity_dashboards(self, guid):
        """
        Coleta dashboards relacionados à entidade (se disponíveis)
        """
        try:
            # Busca dashboards que referenciam a entidade pelo guid
            query = f"""
            {{
              actor {{
                dashboardsSearch(query: \"{guid}\") {{
                  dashboards {{
                    id
                    title
                    permissions
                    owner {{ email name }}
                    createdAt
                    updatedAt
                    pages {{ name widgets {{ ... on DashboardWidget {{ title visualization }} }} }}
                  }}
                }}
              }}
            }}
            """
            headers = {'Api-Key': self.api_key, 'Content-Type': 'application/json'}
            await self.rate_controller.wait_if_needed()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(self.base_url, headers=headers, json={"query": query}) as response:
                    if response.status == 200:
                        data = await response.json()
                        dashboards = data.get("data", {}).get("actor", {}).get("dashboardsSearch", {}).get("dashboards", [])
                        return dashboards or []
                    else:
                        return []
        except Exception as e:
            logger.warning(f"Erro ao coletar dashboards para entidade {guid}: {e}")
            return []

    async def collect_entity_synthetics(self, guid):
        """
        Coleta monitores sintéticos relacionados à entidade (se disponíveis)
        """
        try:
            # Busca monitores sintéticos que referenciam a entidade pelo guid
            query = f"SELECT * FROM SyntheticCheck WHERE entityGuid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
            result = await self.execute_nrql_query(query)
            if result and isinstance(result, list) and len(result) > 0:
                return result
            return []
        except Exception as e:
            logger.warning(f"Erro ao coletar synthetics para entidade {guid}: {e}")
            return []

    async def collect_entity_custom_events(self, guid):
        """
        Coleta eventos customizados relacionados à entidade (se disponíveis)
        """
        try:
            # Busca eventos customizados que referenciam a entidade pelo guid
            query = f"SELECT * FROM CustomEvent WHERE entity.guid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
            result = await self.execute_nrql_query(query)
            if result and isinstance(result, list) and len(result) > 0:
                return result
            return []
        except Exception as e:
            logger.warning(f"Erro ao coletar eventos customizados para entidade {guid}: {e}")
            return []
    async def collect_entity_traces(self, guid):
        """
        Coleta traces/recent transactions para uma entidade específica
        """
        try:
            query = f"SELECT * FROM Transaction WHERE entity.guid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
            result = await self.execute_nrql_query(query)
            if result and isinstance(result, list) and len(result) > 0:
                return result
            return []
        except Exception as e:
            logger.warning(f"Erro ao coletar traces para entidade {guid}: {e}")
            return []

    async def collect_entity_workloads(self, guid):
        """
        Coleta workloads relacionados à entidade (se disponíveis)
        """
        try:
            query = f"""
            {{
              actor {{
                entity(guid: \"{guid}\") {{
                  workloads {{
                    entities {{
                      guid
                      name
                      entityType
                    }}
                  }}
                }}
              }}
            }}
            """
            headers = {'Api-Key': self.api_key, 'Content-Type': 'application/json'}
            await self.rate_controller.wait_if_needed()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(self.base_url, headers=headers, json={"query": query}) as response:
                    if response.status == 200:
                        data = await response.json()
                        workloads = data.get("data", {}).get("actor", {}).get("entity", {}).get("workloads", {}).get("entities", [])
                        return workloads or []
                    else:
                        return []
        except Exception as e:
            logger.warning(f"Erro ao coletar workloads para entidade {guid}: {e}")
            return []
    async def collect_entity_alerts(self, guid):
        """
        Coleta alertas ativos (violations) para uma entidade específica
        """
        try:
            query = f"""
            {{
              actor {{
                entity(guid: \"{guid}\") {{
                  alerts {{
                    violations(filter: {state: OPEN}) {{
                      id
                      label
                      level
                      openedAt
                      closedAt
                      policyName
                      conditionName
                      priority
                      url
                    }}
                  }}
                }}
              }}
            }}
            """
            headers = {'Api-Key': self.api_key, 'Content-Type': 'application/json'}
            await self.rate_controller.wait_if_needed()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(self.base_url, headers=headers, json={"query": query}) as response:
                    if response.status == 200:
                        data = await response.json()
                        violations = data.get("data", {}).get("actor", {}).get("entity", {}).get("alerts", {}).get("violations", [])
                        return violations or []
                    else:
                        return []
        except Exception as e:
            logger.warning(f"Erro ao coletar alertas para entidade {guid}: {e}")
            return []

    async def collect_entity_deployments(self, guid):
        """
        Coleta deployments recentes para uma entidade específica
        """
        try:
            query = f"""
            {{
              actor {{
                entity(guid: \"{guid}\") {{
                  deployments {{
                    deployments(limit: 5) {{
                      deploymentId
                      timestamp
                      user
                      revision
                      changelog
                      description
                      url
                    }}
                  }}
                }}
              }}
            }}
            """
            headers = {'Api-Key': self.api_key, 'Content-Type': 'application/json'}
            await self.rate_controller.wait_if_needed()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(self.base_url, headers=headers, json={"query": query}) as response:
                    if response.status == 200:
                        data = await response.json()
                        deployments = data.get("data", {}).get("actor", {}).get("entity", {}).get("deployments", {}).get("deployments", [])
                        return deployments or []
                    else:
                        return []
        except Exception as e:
            logger.warning(f"Erro ao coletar deployments para entidade {guid}: {e}")
            return []
    """
    Coletor principal do New Relic com circuit breaker, rate limiting e fallback
    """
    
    def __init__(self, api_key: str, account_id: str, query_key: str = None):
        self.api_key = api_key
        self.query_key = query_key or NEW_RELIC_QUERY_KEY
        self.account_id = account_id
        self.base_url = "https://api.newrelic.com/graphql"
        self.rate_controller = RateLimitController()
        self.last_successful_request = None
        
        if not api_key or not account_id or not self.query_key:
            raise ValueError("API Key, Query Key e Account ID são obrigatórios")
    
    async def execute_nrql_query(self, query: str, timeout: int = None) -> Dict:
        """
        Executa query NRQL usando utilitário centralizado.
        """
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        graphql_query = f"""
        {{
          actor {{
            account(id: {self.account_id}) {{
              nrql(query: \"\"\"{query}\"\"\") {{
                results
              }}
            }}
          }}
        }}
        """
        return await execute_nrql_query_common(
            graphql_query,
            headers={'Api-Key': self.api_key, 'Content-Type': 'application/json'},
            url=self.base_url,
            timeout=timeout,
            max_retries=MAX_RETRIES,
            retry_delay=RETRY_DELAY
        )
    
    async def collect_entities(self) -> List[Dict]:
        """
        Coleta entidades do New Relic usando GraphQL
        """
        try:
            # Query GraphQL para buscar entidades
            graphql_query = f"""
            {{
              actor {{
                entitySearch(query: "accountId = {self.account_id} AND domain IN ('APM','BROWSER','INFRA','DB','MOBILE','IOT','SERVERLESS','SYNTH','EXT')") {{
                  results {{
                    entities {{
                      guid
                      name
                      domain
                      entityType
                      tags {{
                        key
                        values
                      }}
                      reporting
                    }}
                  }}
                  count
                }}
              }}
            }}
            """
            
            headers = {
                'Api-Key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            await self.rate_controller.wait_if_needed()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                async with session.post(self.base_url, headers=headers, json={"query": graphql_query}) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "errors" in data:
                            errors = data["errors"]
                            logger.error(f"Erro GraphQL ao coletar entidades: {errors}")
                            self.rate_controller.record_failure()
                            raise Exception(f"Erro GraphQL: {errors}")
                        
                        # Extrai entidades
                        entities_data = data.get("data", {}).get("actor", {}).get("entitySearch", {})
                        entities = entities_data.get("results", {}).get("entities", [])
                        count = entities_data.get("count", 0)
                        # Filtra entidades que não estão reportando
                        entities = [e for e in entities if e.get("reporting")]
                        logger.info(f"Coletadas {len(entities)} entidades reportando de {count} total")
                        self.rate_controller.record_success()
                        self.last_successful_request = datetime.now().isoformat()
                        return entities
                    
                    elif response.status == 429:
                        logger.error("Rate limit atingido ao coletar entidades")
                        self.rate_controller.record_failure(is_rate_limit=True)
                        raise Exception("Rate limit atingido")
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"Erro HTTP {response.status} ao coletar entidades: {error_text[:500]}")
                        self.rate_controller.record_failure()
                        raise Exception(f"Erro HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"Erro ao coletar entidades: {e}")
            raise e
    
    async def collect_entity_metrics(self, entity):
        """
        Coleta métricas para uma entidade específica com base no seu tipo
        Implementa estratégias específicas por domínio/tipo para maximizar dados úteis
        Ajustado para extrair o valor real das métricas essenciais.
        """
        try:
            guid = entity.get('guid')
            name = entity.get('name', 'Desconhecido')
            domain = entity.get('domain', '').upper()
            entity_type = entity.get('entityType', '')

            if not guid:
                logger.warning(f"Entidade sem GUID não pode ter métricas coletadas: {name}")
                return {}

            logger.info(f"Coletando métricas para entidade: {name} ({domain}/{entity_type})")

            # Coleta dashboards relacionados
            dashboards = await self.collect_entity_dashboards(guid)
            if dashboards:
                entity['dashboards'] = dashboards
            # Coleta monitores sintéticos
            synthetics = await self.collect_entity_synthetics(guid)
            if synthetics:
                entity['synthetics'] = synthetics
            # Coleta eventos customizados
            custom_events = await self.collect_entity_custom_events(guid)
            if custom_events:
                entity['custom_events'] = custom_events
            # Coleta eventos de integração
            integration_events = await self.collect_entity_integration_events(guid)
            if integration_events:
                entity['integration_events'] = integration_events
            # Coleta eventos de infraestrutura
            infra_events = await self.collect_entity_infrastructure_events(guid)
            if infra_events:
                entity['infra_events'] = infra_events
            # Coleta logs recentes
            logs = await self.collect_entity_logs(guid)
            if logs:
                entity['logs'] = logs
            # Coleta entidades relacionadas
            related_entities = await self.collect_entity_related_entities(guid)
            if related_entities:
                entity['related_entities'] = related_entities
            # Coleta dependências diretas
            dependencies = await self.collect_entity_dependencies(guid)
            if dependencies:
                entity['dependencies'] = dependencies
            # Coleta alert policies/conditions
            alert_policies = await self.collect_entity_alert_policies(guid)
            if alert_policies:
                entity['alert_policies'] = alert_policies
            # Coleta crashes mobile (Swift/iOS/Android)
            mobile_crashes = await self.collect_entity_mobile_crashes(guid)
            if mobile_crashes:
                entity['mobile_crashes'] = mobile_crashes
            # Coleta queries SQL recentes
            db_queries = await self.collect_entity_db_queries(guid)
            if db_queries:
                entity['db_queries'] = db_queries
            # Coleta atributos detalhados de transações
            tx_attributes = await self.collect_entity_transaction_attributes(guid)
            if tx_attributes:
                entity['transaction_attributes'] = tx_attributes
            # Coleta status de saúde
            health_status = await self.collect_entity_health_status(guid)
            if health_status:
                entity['health_status'] = health_status
            # Coleta séries temporais
            time_series = await self.collect_entity_time_series(guid)
            if time_series:
                entity['time_series'] = time_series
            # Coleta status de dependências externas
            dependency_status = await self.collect_entity_dependency_status(guid)
            if dependency_status:
                entity['dependency_status'] = dependency_status
            # Coleta experiência do usuário
            user_experience = await self.collect_entity_user_experience(guid)
            if user_experience:
                entity['user_experience'] = user_experience
            # Analisa logs para padrões
            log_patterns = await self.analyze_logs_for_patterns(guid)
            if log_patterns:
                entity['log_patterns'] = log_patterns
            # Coleta owners/squad/team
            owners = await self.collect_entity_owners(entity)
            if owners:
                entity['owners'] = owners
            # Constrói topologia/grafo
            topology = await self.build_entity_topology(guid)
            if topology:
                entity['topologia'] = topology
            # Correlaciona alertas e deployments
            alert_deploy_corr = await self.correlate_alerts_with_deployments(entity)
            if alert_deploy_corr:
                entity['alert_deployment_correlation'] = alert_deploy_corr
            # Explicabilidade
            explanation = await self.explain_diagnosis(entity)
            if explanation:
                entity['diagnosis_explanation'] = explanation

            metrics = {}

            # Coleta métricas para cada período temporal
            for period_key, period_query in PERIODOS.items():
                period_metrics = {}
                # Estratégia baseada no domínio da entidade
                if domain == 'APM':
                    # Coleta Apdex
                    try:
                        apdex_query = f"SELECT apdexScore as score FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        apdex_result = await self.execute_nrql_query(apdex_query)
                        if apdex_result and isinstance(apdex_result, list) and len(apdex_result) > 0:
                            value = apdex_result[0].get('score')
                            if value is not None:
                                period_metrics['apdex'] = value
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Apdex para {name}: {e}")

                    # Coleta Response Time
                    try:
                        response_time_query = f"SELECT max(duration) as 'max.duration' FROM Transaction WHERE entity.guid = '{guid}' {period_query}"
                        response_time_result = await self.execute_nrql_query(response_time_query)
                        if response_time_result and isinstance(response_time_result, list) and len(response_time_result) > 0:
                            value = response_time_result[0].get('max.duration')
                            if value is not None:
                                period_metrics['response_time_max'] = value
                                period_metrics['response_time'] = value
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Response Time para {name}: {e}")

                    # Coleta Error Rate
                    try:
                        error_query = f"SELECT latest(errorRate) as 'error_rate' FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        error_result = await self.execute_nrql_query(error_query)
                        if error_result and isinstance(error_result, list) and len(error_result) > 0:
                            value = error_result[0].get('error_rate')
                            if value is not None:
                                period_metrics['error_rate'] = value
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Error Rate para {name}: {e}")

                    # Coleta erros recentes
                    try:
                        recent_errors_query = f"SELECT count(*), error.message, error.class, httpResponseCode FROM TransactionError WHERE entity.guid = '{guid}' {period_query} LIMIT 10"
                        recent_errors_result = await self.execute_nrql_query(recent_errors_query)
                        if recent_errors_result and isinstance(recent_errors_result, list) and len(recent_errors_result) > 0:
                            period_metrics['recent_error'] = recent_errors_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar erros recentes para {name}: {e}")

                    # Coleta Throughput
                    try:
                        throughput_query = f"SELECT average(newRelic.throughput) as 'avg.qps' FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        throughput_result = await self.execute_nrql_query(throughput_query)
                        if throughput_result and isinstance(throughput_result, list) and len(throughput_result) > 0:
                            value = throughput_result[0].get('avg.qps')
                            if value is not None:
                                period_metrics['throughput'] = value
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Throughput para {name}: {e}")

                elif domain == 'BROWSER':
                    # Coleta Apdex para Browser
                    try:
                        apdex_query = f"SELECT apdexScore as score FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        apdex_result = await self.execute_nrql_query(apdex_query)
                        if apdex_result and isinstance(apdex_result, list) and len(apdex_result) > 0:
                            value = apdex_result[0].get('score')
                            if value is not None:
                                period_metrics['apdex'] = value
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Apdex para Browser {name}: {e}")

                    # Coleta Page Load Time
                    try:
                        load_time_query = f"SELECT average(pageLoadTime) as 'avg.loadTime' FROM PageView WHERE entity.guid = '{guid}' {period_query}"
                        load_time_result = await self.execute_nrql_query(load_time_query)
                        if load_time_result and isinstance(load_time_result, list) and len(load_time_result) > 0:
                            value = load_time_result[0].get('avg.loadTime')
                            if value is not None:
                                period_metrics['page_load_time'] = value
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Page Load Time para Browser {name}: {e}")

                    # Coleta JavaScript Errors
                    try:
                        js_error_query = f"SELECT count(*) as 'error_count', errorMessage FROM JavaScriptError WHERE entity.guid = '{guid}' {period_query} LIMIT 10"
                        js_error_result = await self.execute_nrql_query(js_error_query)
                        if js_error_result and isinstance(js_error_result, list) and len(js_error_result) > 0:
                            period_metrics['js_errors'] = js_error_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar JavaScript Errors para Browser {name}: {e}")

                elif domain == 'INFRA':
                    # Coleta CPU Usage
                    try:
                        cpu_query = f"SELECT average(cpuPercent) as 'avg.cpu' FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        cpu_result = await self.execute_nrql_query(cpu_query)
                        if cpu_result and isinstance(cpu_result, list) and len(cpu_result) > 0:
                            value = cpu_result[0].get('avg.cpu')
                            if value is not None:
                                period_metrics['cpu_usage'] = value
                    except Exception as e:
                        logger.warning(f"Erro ao coletar CPU Usage para {name}: {e}")

                    # Coleta Memory Usage
                    try:
                        memory_query = f"SELECT average(memoryUsedBytes)/average(memoryTotalBytes)*100 as 'memory_percent' FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        memory_result = await self.execute_nrql_query(memory_query)
                        if memory_result and isinstance(memory_result, list) and len(memory_result) > 0:
                            value = memory_result[0].get('memory_percent')
                            if value is not None:
                                period_metrics['memory_usage'] = value
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Memory Usage para {name}: {e}")

                    # Coleta Disk Usage
                    try:
                        disk_query = f"SELECT average(diskUsedPercent) as 'disk_percent' FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        disk_result = await self.execute_nrql_query(disk_query)
                        if disk_result and isinstance(disk_result, list) and len(disk_result) > 0:
                            value = disk_result[0].get('disk_percent')
                            if value is not None:
                                period_metrics['disk_usage'] = value
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Disk Usage para {name}: {e}")

                else:
                    # Para outros tipos de entidades, tenta métricas genéricas
                    try:
                        generic_query = f"SELECT * FROM Metric WHERE entity.guid = '{guid}' {period_query} LIMIT 10"
                        generic_result = await self.execute_nrql_query(generic_query)
                        if generic_result and isinstance(generic_result, list) and len(generic_result) > 0:
                            period_metrics['generic'] = generic_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar métricas genéricas para {name}: {e}")

                # Remove métricas nulas, vazias ou default
                period_metrics = {k: v for k, v in period_metrics.items() if v not in (None, [], {}, "", 0)}
                if period_metrics:
                    metrics[period_key] = period_metrics

            # Coleta alertas ativos e deployments recentes
            alerts = await self.collect_entity_alerts(guid)
            if alerts:
                entity['alertas'] = alerts
            deployments = await self.collect_entity_deployments(guid)
            if deployments:
                entity['deployments'] = deployments
            # Coleta dependências (serviços externos, databases)
            dependencies = await self.collect_entity_dependencies(guid)
            if dependencies:
                entity['dependencies'] = dependencies
            # Coleta logs recentes (se disponíveis)
            logs = await self.collect_entity_logs(guid)
            if logs:
                entity['logs'] = logs
            # Coleta traces/recent transactions
            traces = await self.collect_entity_traces(guid)
            if traces:
                entity['traces'] = traces
            # Coleta workloads relacionados
            workloads = await self.collect_entity_workloads(guid)
            if workloads:
                entity['workloads'] = workloads
            # Adiciona timestamp da coleta
            metrics['timestamp'] = datetime.now().isoformat()
            # Só adiciona métricas se houver pelo menos um período com dados
            if any(isinstance(v, dict) and v for k, v in metrics.items() if k != 'timestamp'):
                entity['metricas'] = metrics
                entity['detalhe'] = json.dumps(metrics)
                metrics_count = sum(1 for period in metrics.values() if isinstance(period, dict) 
                                   for metric in period.values() if metric)
                logger.info(f"Coletadas {metrics_count} métricas para {name}")
            else:
                entity['metricas'] = {}
                entity['detalhe'] = "{}"
                logger.info(f"Nenhuma métrica relevante coletada para {name}")
            return entity

        except Exception as e:
            logger.error(f"Erro ao coletar métricas para entidade {entity.get('name', 'Desconhecida')}: {e}")
            logger.error(traceback.format_exc())
            return entity
    
    async def collect_entities_with_metrics(self):
        """
        Coleta entidades e suas respectivas métricas
        """
        try:
            # Coleta entidades base
            entities = await self.collect_entities()
            logger.info(f"Coletadas {len(entities)} entidades base. Coletando métricas...")
            
            # Limita processamento para não sobrecarregar API
            MAX_CONCURRENT = 5
            semaphore = asyncio.Semaphore(MAX_CONCURRENT)
            
            async def process_entity_with_semaphore(entity):
                async with semaphore:
                    return await self.collect_entity_metrics(entity)
            
            # Processa entidades em paralelo, mas limitado
            processed_entities = await asyncio.gather(
                *[process_entity_with_semaphore(entity) for entity in entities],
                return_exceptions=True
            )
            
            # Filtra entidades com erro
            valid_entities = []
            errors = 0
            for result in processed_entities:
                if isinstance(result, Exception):
                    errors += 1
                    logger.error(f"Erro ao processar entidade: {result}")
                elif result.get('metricas') and any(
                        isinstance(v, dict) and v for k, v in result['metricas'].items() if k != 'timestamp'):
                    valid_entities.append(result)
            logger.info(f"Coleta concluída: {len(valid_entities)} entidades válidas com métricas, {errors} erros")
            return valid_entities
            
        except Exception as e:
            logger.error(f"Erro na coleta de entidades com métricas: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def get_health_status(self) -> Dict:
        """
        Retorna status de saúde completo do coletor
        """
        rate_status = self.rate_controller.get_status()
        
        return {
            "status": "healthy" if rate_status["circuit_state"] == "CLOSED" else "degraded" if rate_status["circuit_state"] == "HALF_OPEN" else "unhealthy",
            "circuit_breaker": rate_status,
            "api_key_configured": bool(self.api_key),
            "account_id_configured": bool(self.account_id),
            "base_url": self.base_url,
            "last_successful_request": self.last_successful_request
        }

    async def collect_entity_dependencies(self, guid):
        """
        Coleta informações sobre dependências da entidade (serviços externos, bancos de dados, etc.)
        Busca tanto dependências upstream (serviços que nossa entidade depende) quanto
        downstream (serviços que dependem da nossa entidade)
        
        Args:
            guid (str): GUID da entidade
            
        Returns:
            dict: Informações sobre as dependências ou None com a seguinte estrutura:
                {
                    "upstream": {
                        "servicos_externos": [...],
                        "bancos_dados": [...],
                        "outros": [...]
                    },
                    "downstream": {
                        "servicos_externos": [...],
                        "bancos_dados": [...],
                        "outros": [...]
                    }
                }
        """
        try:
            # Estrutura para armazenar as dependências
            dependencies = {
                "upstream": {
                    "servicos_externos": [],
                    "bancos_dados": [],
                    "outros": []
                },
                "downstream": {
                    "servicos_externos": [],
                    "bancos_dados": [],
                    "outros": []
                }
            }
            
            # 1. Buscar dependências upstream (serviços dos quais nossa entidade depende)
            upstream_query = f"""
            {{
              actor {{
                entity(guid: "{guid}") {{
                  ... on AlertableEntity {{
                    serviceMap: relatedEntities(filter: {{direction: UPSTREAM}}) {{
                      source {{
                        entity {{
                          name
                          guid
                          entityType
                          account {{
                            id
                            name
                          }}
                        }}
                      }}
                      target {{
                        entity {{
                          name
                          guid
                          entityType
                          account {{
                            id
                            name
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
            """
            
            # 2. Buscar dependências downstream (serviços que dependem da nossa entidade)
            downstream_query = f"""
            {{
              actor {{
                entity(guid: "{guid}") {{
                  ... on AlertableEntity {{
                    serviceMap: relatedEntities(filter: {{direction: DOWNSTREAM}}) {{
                      source {{
                        entity {{
                          name
                          guid
                          entityType
                          account {{
                            id
                            name
                          }}
                        }}
                      }}
                      target {{
                        entity {{
                          name
                          guid
                          entityType
                          account {{
                            id
                            name
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
            """
            
            # Função auxiliar para processar as relações e categorizá-las
            def process_relations(relations, direction_key):
                if not relations:
                    return
                
                for relation in relations:
                    # Upstream: observamos o SOURCE (quem fornece para nossa entidade)
                    # Downstream: observamos o TARGET (quem recebe da nossa entidade)
                    entity_data = relation.get('source' if direction_key == "upstream" else 'target', {}).get('entity', {})
                    
                    if not entity_data or not entity_data.get('guid'):
                        continue
                    
                    dependency = {
                        "nome": entity_data.get('name', 'Desconhecido'),
                        "guid": entity_data.get('guid'),
                        "tipo": entity_data.get('entityType')
                    }
                    
                    # Categorizar dependência
                    entity_type = entity_data.get('entityType', '').lower()
                    if 'database' in entity_type or 'db' in entity_type:
                        dependencies[direction_key]["bancos_dados"].append(dependency)
                    elif 'service' in entity_type or 'api' in entity_type or 'application' in entity_type:
                        dependencies[direction_key]["servicos_externos"].append(dependency)
                    else:
                        dependencies[direction_key]["outros"].append(dependency)
            
            # Executar consultas em paralelo para melhor performance
            upstream_response = await self.make_graphql_request(upstream_query)
            downstream_response = await self.make_graphql_request(downstream_query)
            
            # Processar dependências upstream
            if (upstream_response and 'data' in upstream_response and 
                upstream_response['data'].get('actor', {}).get('entity', {}).get('serviceMap')):
                upstream_service_map = upstream_response['data']['actor']['entity']['serviceMap']
                process_relations(upstream_service_map, "upstream")
                logger.info(f"Coletado {len(upstream_service_map)} dependências upstream para entidade {guid}")
            else:
                logger.debug(f"Nenhuma dependência upstream encontrada para entidade {guid}")
            
            # Processar dependências downstream
            if (downstream_response and 'data' in downstream_response and 
                downstream_response['data'].get('actor', {}).get('entity', {}).get('serviceMap')):
                downstream_service_map = downstream_response['data']['actor']['entity']['serviceMap']
                process_relations(downstream_service_map, "downstream")
                logger.info(f"Coletado {len(downstream_service_map)} dependências downstream para entidade {guid}")
            else:
                logger.debug(f"Nenhuma dependência downstream encontrada para entidade {guid}")
            
            # Remover categorias vazias
            for direction in ["upstream", "downstream"]:
                for key in list(dependencies[direction].keys()):
                    if not dependencies[direction][key]:
                        del dependencies[direction][key]
                
                # Se não há dependências nessa direção, remover a direção inteira
                if not dependencies[direction]:
                    del dependencies[direction]
            
            return dependencies if dependencies else None
            
        except Exception as e:
            logger.error(f"Erro ao coletar dependências para entidade {guid}: {str(e)}")
            return None

def registrar_entidade_sem_metricas(entidade, motivo):
    logger.warning(f"Entidade sem métricas: {entidade.get('name', entidade.get('guid'))} | Domínio: {entidade.get('domain')} | Motivo: {motivo}")
    entidade['motivo_sem_metricas'] = motivo

def safe_first(lst, default=None):
    """Retorna o primeiro item da lista ou um valor padrão se a lista estiver vazia ou não for lista."""
    if isinstance(lst, list) and lst:
        return lst[0]
    return default

# Função principal para teste independente
async def main():
    """
    Função de teste para validar o comportamento do NewRelicCollector
    """
    import os
    from dotenv import load_dotenv
    
    # Carrega variáveis de ambiente
    load_dotenv()
    
    api_key = os.getenv('NEW_RELIC_API_KEY')
    query_key = os.getenv('NEW_RELIC_QUERY_KEY')
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
    
    if not api_key or not account_id or not query_key:
        logger.error("NEW_RELIC_API_KEY, NEW_RELIC_QUERY_KEY e NEW_RELIC_ACCOUNT_ID devem estar configurados no .env")
        return
    
    collector = NewRelicCollector(api_key=api_key, account_id=account_id, query_key=query_key)
    
    print("=== TESTE DO NEW RELIC COLLECTOR ===")
    
    # Status inicial
    health = collector.get_health_status()
    print(f"Status inicial: {health}")
    
    # Teste 1: Query simples para testar conectividade
    print("\n--- Teste 1: Query de conectividade ---")
    try:
        test_query = f"SELECT count(*) FROM Transaction WHERE appName IS NOT NULL SINCE 1 hour ago LIMIT 1"
        result = await collector.execute_nrql_query(test_query)
        print(f"✅ Conectividade OK: {result}")
    except Exception as e:
        print(f"❌ Erro de conectividade: {e}")
    
    # Teste 2: Coleta de entidades
    print("\n--- Teste 2: Coleta de entidades ---")
    try:
        entities = await collector.collect_entities()
        print(f"✅ Entidades coletadas: {len(entities)}")
        
        # Mostra algumas entidades para debug
        for i, entity in enumerate(entities[:3]):
            print(f"  Entidade {i+1}: {entity.get('name', 'N/A')} ({entity.get('entityType', 'N/A')})")
            
        # Teste de coleta de métricas
        if entities:
            print("\n--- Teste 3: Coleta de métricas ---")
            entity_with_metrics = await collector.collect_entity_metrics(entities[0])
            
            if entity_with_metrics and entity_with_metrics.get('metricas'):
                print(f"✅ Métricas coletadas para {entity_with_metrics.get('name')}")
                metrics = entity_with_metrics.get('metricas', {})
                for period, data in metrics.items():
                    if period != 'timestamp' and isinstance(data, dict):
                        print(f"  Período {period}: {len(data)} tipos de métricas")
            else:
                print("❌ Falha ao coletar métricas")
    except Exception as e:
        print(f"❌ Erro na coleta de entidades: {e}")
    
    # Teste 3: Status final
    print("\n--- Status final ---")
    final_health = collector.get_health_status()
    print(f"Status final: {final_health}")

# Função principal para coleta completa
async def coletar_contexto_completo():
    """
    Coleta o contexto completo do New Relic incluindo entidades e suas métricas
    """
    collector = NewRelicCollector(NEW_RELIC_API_KEY, NEW_RELIC_ACCOUNT_ID, NEW_RELIC_QUERY_KEY)
    try:
        # Coleta entidades com métricas
        entities = await collector.collect_entities_with_metrics()
        return {"entidades": entities, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Erro na coleta de contexto: {e}")
        logger.error(traceback.format_exc())
        return {"entidades": [], "timestamp": datetime.now().isoformat(), "error": str(e)}

if __name__ == "__main__":
    asyncio.run(main())
