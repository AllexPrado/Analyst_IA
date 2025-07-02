"""
Coletor avançado de entidades e métricas do New Relic.
Este módulo implementa um coletor completo que obtém todas as entidades e métricas 
disponíveis no New Relic, conforme os requisitos de cobertura total.
"""

import os
import sys
import json
import logging
import asyncio
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import aiohttp
import time

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

# Constantes
DEFAULT_TIMEOUT = 30.0  # Timeout padrão para requisições (segundos)
MAX_RETRIES = 3  # Número máximo de tentativas para requisições
RETRY_DELAY = 1.0  # Tempo entre tentativas (segundos)
MAX_ENTITIES_PER_REQUEST = 500  # Máximo de entidades por requisição
RATE_LIMIT_PAUSE = 1.0  # Pausa entre requisições para evitar rate limiting (segundos)

# Lista completa de domínios do New Relic
DOMINIOS_NEWRELIC = [
    "APM", "BROWSER", "INFRA", "MOBILE", "SYNTH", "EXT", "DASHBOARD", 
    "WORKLOAD", "ALERT", "LOG", "DB", "KUBERNETES", "LAMBDA", "SERVICE",
    "IOT", "PIXIE", "NETWORK", "ML_MODEL", "SERVERLESS", "APPLIANCE"
]

# Mapeamento de tipos de entidades para categorias
ENTITY_TYPE_MAPPINGS = {
    "APPLICATION": "APM",
    "HOST": "INFRA",
    "SERVICE": "APM",
    "DASHBOARD": "DASHBOARD",
    "BROWSER_APPLICATION": "BROWSER",
    "MONITOR": "SYNTH",
    "WORKLOAD": "WORKLOAD",
    "ALERT_POLICY": "ALERT",
    "ALERT_CONDITION": "ALERT",
    "DATABASE": "DB",
    "KUBERNETES_CLUSTER": "KUBERNETES",
    "KUBERNETES_POD": "KUBERNETES",
    "KUBERNETES_CONTAINER": "KUBERNETES",
    "KUBERNETES_DEPLOYMENT": "KUBERNETES",
    "AWSLAMBDAFUNCTION": "LAMBDA",
    "MOBILE_APPLICATION": "MOBILE",
    "EXTERNAL": "EXT",
    "IOT_DEVICE": "IOT",
    "NETWORK_DEVICE": "NETWORK",
    "ML_MODEL": "ML_MODEL",
    "SERVERLESS_APPLICATION": "SERVERLESS",
}

class AdvancedNewRelicCollector:
    """
    Coletor avançado que obtém todos os tipos de dados do New Relic.
    """
    
    def __init__(self, api_key: Optional[str] = None, query_key: Optional[str] = None, account_id: Optional[str] = None):
        """
        Inicializa o coletor com as chaves necessárias.
        
        Args:
            api_key: API Key do New Relic (Admin)
            query_key: Query Key para consultas NRQL
            account_id: ID da conta do New Relic
        """
        # Carregar de variáveis de ambiente se não fornecidas
        self.api_key = api_key or os.environ.get("NEW_RELIC_API_KEY")
        self.query_key = query_key or os.environ.get("NEW_RELIC_QUERY_KEY")
        self.account_id = account_id or os.environ.get("NEW_RELIC_ACCOUNT_ID")
        
        # Validar configurações
        if not self.api_key:
            raise ValueError("New Relic API Key não fornecida")
        if not self.query_key:
            logger.warning("New Relic Query Key não fornecida. Algumas funcionalidades de NRQL podem não estar disponíveis.")
        if not self.account_id:
            raise ValueError("New Relic Account ID não fornecido")
            
        # Headers comuns
        self.graphql_headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        self.rest_headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        self.insights_headers = {
            "X-Query-Key": self.query_key,
            "Content-Type": "application/json"
        }
        
        # URLs base
        self.graphql_url = "https://api.newrelic.com/graphql"
        self.rest_api_url = f"https://api.newrelic.com/v2"
        self.insights_url = f"https://insights-api.newrelic.com/v1/accounts/{self.account_id}/query"
        
        # Controle de requisições
        self.last_request_time = 0
        self.request_count = 0
        self.max_requests_per_minute = 100  # Ajustar conforme limites da API
        
        logger.info(f"Coletor avançado New Relic inicializado. Account ID: {self.account_id}")
        
    async def rate_limit_control(self):
        """Controla o rate limit das chamadas de API."""
        self.request_count += 1
        
        # Aplicar controle de taxa se necessário
        now = time.time()
        elapsed = now - self.last_request_time
        
        # Se já fizemos muitas requisições em um minuto
        if self.request_count > self.max_requests_per_minute and elapsed < 60:
            pause_time = max(60 - elapsed, RATE_LIMIT_PAUSE)
            logger.debug(f"Rate limit: pausando por {pause_time:.2f} segundos...")
            await asyncio.sleep(pause_time)
            self.request_count = 0
            self.last_request_time = time.time()
        elif elapsed >= 60:
            # Reset se passou um minuto
            self.request_count = 1
            self.last_request_time = now
        
        # Pausa mínima entre requisições para não sobrecarregar
        await asyncio.sleep(RATE_LIMIT_PAUSE)
    
    async def make_request(self, url, headers, method="GET", data=None, params=None) -> Dict:
        """
        Faz uma requisição HTTP com retry automático.
        
        Args:
            url: URL da requisição
            headers: Headers HTTP
            method: Método HTTP (GET, POST, etc)
            data: Dados para enviar (para POST, PUT)
            params: Parâmetros de query string (para GET)
            
        Returns:
            Dict contendo a resposta JSON ou erro
        """
        await self.rate_limit_control()
        
        for attempt in range(MAX_RETRIES):
            try:
                # Configurações para evitar problemas de SSL e timeouts
                timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT * 2)  # Aumentar timeout
                ssl_context = None  # Usar o SSL padrão do sistema
                
                # Usar context manager com tcp_nodelay para reduzir latência
                conn = aiohttp.TCPConnector(ssl=ssl_context, force_close=True)
                
                async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
                    if method.upper() == "GET":
                        async with session.get(url, headers=headers, params=params) as response:
                            if response.status == 200:
                                return await response.json()
                            elif response.status == 429:  # Rate limiting
                                retry_after = int(response.headers.get("Retry-After", "60"))
                                logger.warning(f"Rate limit atingido. Aguardando {retry_after} segundos...")
                                await asyncio.sleep(retry_after)
                                continue
                            else:
                                error_text = await response.text()
                                logger.error(f"Erro na requisição: {response.status} - {error_text}")
                                if attempt == MAX_RETRIES - 1:
                                    return {"error": f"HTTP {response.status}", "message": error_text}
                    elif method.upper() == "POST":
                        async with session.post(url, headers=headers, json=data) as response:
                            if response.status == 200:
                                return await response.json()
                            elif response.status == 429:  # Rate limiting
                                retry_after = int(response.headers.get("Retry-After", "60"))
                                logger.warning(f"Rate limit atingido. Aguardando {retry_after} segundos...")
                                await asyncio.sleep(retry_after)
                                continue
                            else:
                                error_text = await response.text()
                                logger.error(f"Erro na requisição: {response.status} - {error_text}")
                                if attempt == MAX_RETRIES - 1:
                                    return {"error": f"HTTP {response.status}", "message": error_text}
            except aiohttp.ClientError as e:
                logger.error(f"Erro de cliente na tentativa {attempt+1}/{MAX_RETRIES}: {e}")
                if "SSL" in str(e):
                    logger.warning("Detectado erro de SSL. Tentando abordagem alternativa...")
                    # Se for erro de SSL, podemos tentar uma abordagem diferente na próxima iteração
                    if attempt == MAX_RETRIES - 1:
                        return {"error": "SSL Error", "message": str(e)}
                else:
                    if attempt == MAX_RETRIES - 1:
                        return {"error": "ClientError", "message": str(e)}
            except asyncio.TimeoutError:
                logger.error(f"Timeout na tentativa {attempt+1}/{MAX_RETRIES}")
                # Aumentar o timeout para a próxima tentativa
                DEFAULT_TIMEOUT *= 1.5
                if attempt == MAX_RETRIES - 1:
                    return {"error": "TimeoutError", "message": "A requisição excedeu o timeout"}
            except Exception as e:
                logger.error(f"Erro inesperado na tentativa {attempt+1}/{MAX_RETRIES}: {e}")
                logger.error(traceback.format_exc())
                if attempt == MAX_RETRIES - 1:
                    return {"error": "UnexpectedError", "message": str(e)}
                
            # Esperar antes de tentar novamente (com backoff exponencial)
            backoff_time = RETRY_DELAY * (2 ** attempt)
            logger.info(f"Aguardando {backoff_time:.1f} segundos antes da próxima tentativa...")
            await asyncio.sleep(backoff_time)
        
        return {"error": "MaxRetriesExceeded", "message": f"Falha após {MAX_RETRIES} tentativas"}
    
    async def execute_graphql_query(self, query, variables=None) -> Dict:
        """
        Executa uma consulta GraphQL na API do New Relic.
        
        Args:
            query: Consulta GraphQL
            variables: Variáveis para a consulta
            
        Returns:
            Dict com resultado da consulta
        """
        payload = {
            "query": query,
        }
        
        if variables:
            payload["variables"] = variables
            
        return await self.make_request(
            url=self.graphql_url,
            headers=self.graphql_headers,
            method="POST",
            data=payload
        )
    
    async def execute_nrql_query(self, nrql, timeout=60) -> Dict:
        """
        Executa uma consulta NRQL.
        
        Args:
            nrql: Consulta NRQL
            timeout: Timeout em segundos
            
        Returns:
            Dict com resultados da consulta
        """
        if not self.query_key:
            logger.error("Query Key não disponível para consulta NRQL")
            return {"error": "MissingQueryKey", "message": "Query Key é necessária para consultas NRQL"}
            
        payload = {
            "nrql": nrql,
            "timeout": timeout
        }
        
        return await self.make_request(
            url=self.insights_url,
            headers=self.insights_headers,
            method="POST",
            data=payload
        )

    async def get_all_entities(self, cursor=None, entities_collected=None) -> List[Dict]:
        """
        Obtém todas as entidades disponíveis no New Relic usando paginação.
        
        Args:
            cursor: Cursor para paginação
            entities_collected: Lista de entidades já coletadas
            
        Returns:
            Lista de todas as entidades
        """
        if entities_collected is None:
            entities_collected = []
            
        query = """
        query EntitiesQuery($cursor: String) {
            actor {
                entitySearch(queryBuilder: {}) {
                    results(cursor: $cursor) {
                        entities {
                            guid
                            name
                            type
                            domain
                            entityType
                            reporting
                            account {
                                id
                                name
                            }
                            tags {
                                key
                                values
                            }
                        }
                        nextCursor
                    }
                }
            }
        }
        """
        
        variables = {}
        if cursor:
            variables["cursor"] = cursor
            
        result = await self.execute_graphql_query(query, variables)
        
        if "error" in result:
            logger.error(f"Erro ao obter entidades: {result}")
            return entities_collected
            
        try:
            search_results = result.get("data", {}).get("actor", {}).get("entitySearch", {}).get("results", {})
            entities = search_results.get("entities", [])
            next_cursor = search_results.get("nextCursor")
            
            # Adicionar entidades à lista
            entities_collected.extend(entities)
            logger.info(f"Coletadas {len(entities)} entidades. Total até agora: {len(entities_collected)}")
            
            # Se tem próxima página, continuar a busca
            if next_cursor:
                logger.debug(f"Buscando próxima página com cursor: {next_cursor}")
                return await self.get_all_entities(cursor=next_cursor, entities_collected=entities_collected)
                
            return entities_collected
            
        except Exception as e:
            logger.error(f"Erro ao processar resultados de entidades: {e}")
            logger.error(traceback.format_exc())
            return entities_collected
            
    async def get_entities_by_domain(self, domain) -> List[Dict]:
        """
        Obtém entidades de um domínio específico.
        
        Args:
            domain: Domínio do New Relic (APM, BROWSER, etc)
            
        Returns:
            Lista de entidades do domínio
        """
        query = """
        query EntitiesByDomainQuery($domain: EntityDomainType!, $cursor: String) {
            actor {
                entitySearch(queryBuilder: {domain: $domain}) {
                    results(cursor: $cursor) {
                        entities {
                            guid
                            name
                            type
                            domain
                            entityType
                            reporting
                            account {
                                id
                                name
                            }
                            tags {
                                key
                                values
                            }
                        }
                        nextCursor
                    }
                }
            }
        }
        """
        
        entities_collected = []
        cursor = None
        
        while True:
            variables = {
                "domain": domain
            }
            
            if cursor:
                variables["cursor"] = cursor
                
            result = await self.execute_graphql_query(query, variables)
            
            if "error" in result:
                logger.error(f"Erro ao obter entidades do domínio {domain}: {result}")
                break
                
            try:
                search_results = result.get("data", {}).get("actor", {}).get("entitySearch", {}).get("results", {})
                entities = search_results.get("entities", [])
                next_cursor = search_results.get("nextCursor")
                
                # Adicionar entidades à lista
                entities_collected.extend(entities)
                logger.info(f"Coletadas {len(entities)} entidades do domínio {domain}. Total: {len(entities_collected)}")
                
                # Se não tem próxima página, terminar
                if not next_cursor:
                    break
                    
                cursor = next_cursor
                    
            except Exception as e:
                logger.error(f"Erro ao processar resultados de entidades do domínio {domain}: {e}")
                logger.error(traceback.format_exc())
                break
                
        return entities_collected
    
    async def get_entity_metrics(self, entity_guid) -> Dict:
        """
        Obtém todas as métricas disponíveis para uma entidade.
        
        Args:
            entity_guid: GUID da entidade
            
        Returns:
            Dict com métricas da entidade
        """
        query = """
        query EntityMetricsQuery($guid: EntityGuid!) {
            actor {
                entity(guid: $guid) {
                    guid
                    name
                    domain
                    type
                    ... on ApmApplicationEntity {
                        apmSummary {
                            apdexScore
                            errorRate
                            hostCount
                            instanceCount
                            nonWebResponseTimeAverage
                            nonWebThroughput
                            responseTimeAverage
                            throughput
                            webResponseTimeAverage
                            webThroughput
                        }
                    }
                    ... on BrowserApplicationEntity {
                        browserSummary {
                            ajaxRequestThroughput
                            ajaxResponseTimeAverage
                            jsErrorRate
                            pageLoadThroughput
                            pageLoadTimeAverage
                            pageLoadTimeMedian
                            sessionCount
                            pageViewThroughput
                        }
                    }
                    ... on InfrastructureHostEntity {
                        infrastructureSummary {
                            cpuUtilizationPercent
                            diskUtilizationPercent
                            memoryUtilizationPercent
                            networkReceiveRate
                            networkTransmitRate
                            servicesCount
                        }
                    }
                    ... on MobileApplicationEntity {
                        mobileSummary {
                            appLaunchCount
                            crashCount
                            crashRate
                            httpRequestCount
                            httpResponseTimeAverage
                            httpErrorRate
                            networkFailureRate
                            sessionCount
                        }
                    }
                    reporting
                    alertSeverity
                    tags {
                        key
                        values
                    }
                }
            }
        }
        """
        
        variables = {
            "guid": entity_guid
        }
        
        result = await self.execute_graphql_query(query, variables)
        
        if "error" in result:
            logger.error(f"Erro ao obter métricas da entidade {entity_guid}: {result}")
            return {}
            
        try:
            entity_data = result.get("data", {}).get("actor", {}).get("entity", {})
            
            # Extrair dados básicos
            metrics = {
                "reporting": entity_data.get("reporting", False),
                "alertSeverity": entity_data.get("alertSeverity", "NONE"),
                "tags": entity_data.get("tags", [])
            }
            
            # Adicionar métricas específicas do domínio
            domain = entity_data.get("domain")
            if domain == "APM" and "apmSummary" in entity_data:
                metrics["apm"] = entity_data.get("apmSummary", {})
            elif domain == "BROWSER" and "browserSummary" in entity_data:
                metrics["browser"] = entity_data.get("browserSummary", {})
            elif domain == "INFRA" and "infrastructureSummary" in entity_data:
                metrics["infra"] = entity_data.get("infrastructureSummary", {})
            elif domain == "MOBILE" and "mobileSummary" in entity_data:
                metrics["mobile"] = entity_data.get("mobileSummary", {})
                
            return metrics
            
        except Exception as e:
            logger.error(f"Erro ao processar métricas da entidade {entity_guid}: {e}")
            logger.error(traceback.format_exc())
            return {}
    
    async def get_entity_detailed_metrics(self, entity_guid, entity_domain) -> Dict:
        """
        Coleta métricas detalhadas para uma entidade específica usando NRQL.
        
        Args:
            entity_guid: GUID da entidade
            entity_domain: Domínio da entidade (APM, BROWSER, etc)
            
        Returns:
            Dict com métricas detalhadas
        """
        if not self.query_key:
            logger.warning("Query Key não disponível para consultas NRQL detalhadas")
            return {}
            
        detailed_metrics = {}
        domain = entity_domain.upper()
        
        # Definir período para consultas
        period = "SINCE 30 MINUTES AGO"
        
        # Métricas específicas por domínio
        if domain == "APM":
            queries = {
                "apdex": f"SELECT latest(apdex) FROM Metric WHERE entity.guid = '{entity_guid}' {period}",
                "response_time": f"SELECT average(duration) FROM Transaction WHERE entityGuid = '{entity_guid}' {period}",
                "error_rate": f"SELECT percentage(count(*), WHERE error is true) FROM Transaction WHERE entityGuid = '{entity_guid}' {period}",
                "throughput": f"SELECT rate(count(*), 1 minute) FROM Transaction WHERE entityGuid = '{entity_guid}' {period}",
                "database_time": f"SELECT average(databaseDuration) FROM Transaction WHERE entityGuid = '{entity_guid}' {period}",
                "top_endpoints": f"SELECT count(*) FROM Transaction WHERE entityGuid = '{entity_guid}' {period} FACET name LIMIT 10",
                "recent_errors": f"SELECT * FROM TransactionError WHERE entityGuid = '{entity_guid}' {period} LIMIT 10"
            }
        elif domain == "BROWSER":
            queries = {
                "page_load_time": f"SELECT average(duration) FROM PageView WHERE entityGuid = '{entity_guid}' {period}",
                "ajax_response_time": f"SELECT average(duration) FROM Ajax WHERE entityGuid = '{entity_guid}' {period}",
                "js_errors": f"SELECT count(*) FROM JavaScriptError WHERE entityGuid = '{entity_guid}' {period}",
                "top_pages": f"SELECT count(*) FROM PageView WHERE entityGuid = '{entity_guid}' {period} FACET pageUrl LIMIT 10",
                "core_web_vitals": f"SELECT average(largestContentfulPaint), average(firstInputDelay), average(cumulativeLayoutShift) FROM PageViewTiming WHERE entityGuid = '{entity_guid}' {period}"
            }
        elif domain == "INFRA":
            queries = {
                "cpu_usage": f"SELECT average(cpuPercent) FROM SystemSample WHERE entityGuid = '{entity_guid}' {period}",
                "memory_usage": f"SELECT average(memoryUsedPercent) FROM SystemSample WHERE entityGuid = '{entity_guid}' {period}",
                "disk_usage": f"SELECT average(diskUsedPercent) FROM SystemSample WHERE entityGuid = '{entity_guid}' {period}",
                "network_io": f"SELECT average(transmitBytesPerSecond), average(receiveBytesPerSecond) FROM SystemSample WHERE entityGuid = '{entity_guid}' {period}"
            }
        elif domain == "MOBILE":
            queries = {
                "crash_rate": f"SELECT count(*) FROM Mobile WHERE entityGuid = '{entity_guid}' AND crashCount > 0 {period}",
                "http_errors": f"SELECT count(*) FROM MobileRequestError WHERE entityGuid = '{entity_guid}' {period}",
                "network_errors": f"SELECT count(*) FROM MobileRequest WHERE entityGuid = '{entity_guid}' AND error = true {period}",
                "session_count": f"SELECT count(*) FROM MobileSession WHERE entityGuid = '{entity_guid}' {period}"
            }
        elif domain == "DB":
            queries = {
                "queries_per_second": f"SELECT average(queriesPerSecond) FROM DatastoreSample WHERE entityGuid = '{entity_guid}' {period}",
                "slow_queries": f"SELECT count(*) FROM SlowQuery WHERE entityGuid = '{entity_guid}' {period}",
                "connection_count": f"SELECT average(connectionCount) FROM DatastoreSample WHERE entityGuid = '{entity_guid}' {period}"
            }
        elif domain == "KUBERNETES":
            queries = {
                "pod_status": f"SELECT count(*) FROM K8sPodSample WHERE entityGuid = '{entity_guid}' {period} FACET status",
                "container_cpu": f"SELECT average(containerCpuUsedCores) FROM K8sContainerSample WHERE entityGuid = '{entity_guid}' {period}",
                "container_memory": f"SELECT average(containerMemoryUsedBytes) FROM K8sContainerSample WHERE entityGuid = '{entity_guid}' {period}",
                "pod_restarts": f"SELECT sum(podRestartCount) FROM K8sPodSample WHERE entityGuid = '{entity_guid}' {period}",
                "deployment_status": f"SELECT latest(deploymentStatus) FROM K8sDeploymentSample WHERE entityGuid = '{entity_guid}' {period}"
            }
        elif domain == "SERVERLESS" or domain == "LAMBDA":
            queries = {
                "invocations": f"SELECT count(*) FROM ServerlessSample WHERE entityGuid = '{entity_guid}' {period}",
                "duration": f"SELECT average(duration) FROM ServerlessSample WHERE entityGuid = '{entity_guid}' {period}",
                "errors": f"SELECT count(*) FROM ServerlessSample WHERE entityGuid = '{entity_guid}' AND error IS TRUE {period}",
                "cold_starts": f"SELECT count(*) FROM ServerlessSample WHERE entityGuid = '{entity_guid}' AND coldStart IS TRUE {period}"
            }
        else:
            # Para outros domínios, tentar métricas genéricas
            queries = {
                "status": f"SELECT latest(timestamp) FROM Metric WHERE entity.guid = '{entity_guid}' {period}"
            }
            
        # Executar queries e coletar resultados
        for metric_name, nrql in queries.items():
            try:
                result = await self.execute_nrql_query(nrql)
                
                if "error" not in result and "results" in result:
                    detailed_metrics[metric_name] = result["results"]
                    
            except Exception as e:
                logger.error(f"Erro ao executar query NRQL para {metric_name}: {e}")
                
        return detailed_metrics
    
    async def get_alerts_for_entity(self, entity_guid) -> List[Dict]:
        """
        Obtém alertas associados a uma entidade.
        
        Args:
            entity_guid: GUID da entidade
            
        Returns:
            Lista de alertas
        """
        query = """
        query EntityAlertsQuery($guid: EntityGuid!) {
            actor {
                entity(guid: $guid) {
                    alertViolations(timeWindow: {duration: 24, unit: HOURS}) {
                        violations {
                            violationId
                            label
                            level
                            openedAt
                            closedAt
                            violationUrl
                        }
                    }
                    alertSeverity
                    alertConditions {
                        name
                        enabled
                        id
                        type
                    }
                }
            }
        }
        """
        
        variables = {
            "guid": entity_guid
        }
        
        result = await self.execute_graphql_query(query, variables)
        
        if "error" in result:
            logger.error(f"Erro ao obter alertas da entidade {entity_guid}: {result}")
            return []
            
        try:
            entity_data = result.get("data", {}).get("actor", {}).get("entity", {})
            violations = entity_data.get("alertViolations", {}).get("violations", [])
            alert_conditions = entity_data.get("alertConditions", [])
            
            return {
                "violations": violations,
                "conditions": alert_conditions,
                "severity": entity_data.get("alertSeverity")
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar alertas da entidade {entity_guid}: {e}")
            logger.error(traceback.format_exc())
            return []
            
    async def get_dashboards_list(self) -> List[Dict]:
        """
        Obtém a lista de dashboards disponíveis.
        
        Returns:
            Lista de dashboards
        """
        query = """
        query DashboardsQuery($cursor: String) {
            actor {
                entitySearch(queryBuilder: {type: DASHBOARD}) {
                    results(cursor: $cursor) {
                        entities {
                            guid
                            name
                            ... on DashboardEntity {
                                dashboardParentGuid
                                owner {
                                    email
                                }
                                permissions
                            }
                        }
                        nextCursor
                    }
                }
            }
        }
        """
        
        dashboards = []
        cursor = None
        
        while True:
            variables = {}
            if cursor:
                variables["cursor"] = cursor
                
            result = await self.execute_graphql_query(query, variables)
            
            if "error" in result:
                logger.error(f"Erro ao obter dashboards: {result}")
                break
                
            try:
                search_results = result.get("data", {}).get("actor", {}).get("entitySearch", {}).get("results", {})
                dashboard_entities = search_results.get("entities", [])
                next_cursor = search_results.get("nextCursor")
                
                dashboards.extend(dashboard_entities)
                
                if not next_cursor:
                    break
                    
                cursor = next_cursor
                
            except Exception as e:
                logger.error(f"Erro ao processar resultados de dashboards: {e}")
                logger.error(traceback.format_exc())
                break
                
        return dashboards
        
    async def get_dashboard_details(self, dashboard_guid) -> Dict:
        """
        Obtém detalhes de um dashboard específico.
        
        Args:
            dashboard_guid: GUID do dashboard
            
        Returns:
            Dict com detalhes do dashboard
        """
        query = """
        query DashboardDetailsQuery($guid: EntityGuid!) {
            actor {
                entity(guid: $guid) {
                    ... on DashboardEntity {
                        guid
                        name
                        description
                        owner {
                            email
                            userId
                        }
                        pages {
                            name
                            description
                            widgets {
                                id
                                title
                                visualization {
                                    id
                                }
                                rawConfiguration
                                linkedEntities {
                                    guid
                                    name
                                    type
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "guid": dashboard_guid
        }
        
        result = await self.execute_graphql_query(query, variables)
        
        if "error" in result:
            logger.error(f"Erro ao obter detalhes do dashboard {dashboard_guid}: {result}")
            return {}
            
        try:
            dashboard_data = result.get("data", {}).get("actor", {}).get("entity", {})
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Erro ao processar detalhes do dashboard {dashboard_guid}: {e}")
            logger.error(traceback.format_exc())
            return {}
            
    async def get_logs_for_entity(self, entity_guid, limit=100) -> List[Dict]:
        """
        Obtém logs associados a uma entidade.
        
        Args:
            entity_guid: GUID da entidade
            limit: Número máximo de logs a retornar
            
        Returns:
            Lista de logs
        """
        nrql = f"""
        SELECT * FROM Log WHERE entity.guid = '{entity_guid}' 
        SINCE 1 hour ago LIMIT {limit}
        """
        
        result = await self.execute_nrql_query(nrql)
        
        if "error" in result:
            logger.error(f"Erro ao obter logs da entidade {entity_guid}: {result}")
            return []
            
        try:
            return result.get("results", [])
            
        except Exception as e:
            logger.error(f"Erro ao processar logs da entidade {entity_guid}: {e}")
            logger.error(traceback.format_exc())
            return []
            
    async def collect_distributed_tracing_data(self, entity_guid) -> List[Dict]:
        """
        Coleta dados de Distributed Tracing para uma entidade.
        
        Args:
            entity_guid: GUID da entidade
            
        Returns:
            Lista de traces
        """
        nrql = f"""
        SELECT * FROM DistributedTracingSpanEvent 
        WHERE entity.guid = '{entity_guid}' 
        SINCE 30 MINUTES AGO LIMIT 100
        """
        
        result = await self.execute_nrql_query(nrql)
        
        if "error" in result:
            logger.error(f"Erro ao obter traces da entidade {entity_guid}: {result}")
            return []
            
        try:
            return result.get("results", [])
            
        except Exception as e:
            logger.error(f"Erro ao processar traces da entidade {entity_guid}: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def get_all_alert_policies(self) -> List[Dict]:
        """
        Obtém todas as políticas de alerta.
        
        Returns:
            Lista de políticas de alerta
        """
        query = """
        query AlertPoliciesQuery($cursor: String) {
            actor {
                alertPolicies(cursor: $cursor) {
                    policies {
                        id
                        name
                        incidentPreference
                        accountId
                    }
                    nextCursor
                }
            }
        }
        """
        
        policies = []
        cursor = None
        
        while True:
            variables = {}
            if cursor:
                variables["cursor"] = cursor
                
            result = await self.execute_graphql_query(query, variables)
            
            if "error" in result:
                logger.error(f"Erro ao obter políticas de alerta: {result}")
                break
                
            try:
                policies_data = result.get("data", {}).get("actor", {}).get("alertPolicies", {})
                policy_list = policies_data.get("policies", [])
                next_cursor = policies_data.get("nextCursor")
                
                policies.extend(policy_list)
                
                if not next_cursor:
                    break
                    
                cursor = next_cursor
                
            except Exception as e:
                logger.error(f"Erro ao processar políticas de alerta: {e}")
                logger.error(traceback.format_exc())
                break
                
        return policies
    
    async def fetch_alerts(self) -> Dict:
        """
        Obtém dados de alertas da conta do New Relic
        
        Returns:
            Dict com alertas agrupados por política
        """
        logger.info("Obtendo alertas do New Relic")
        
        alerts_data = {
            "policies": [],
            "violations": [],
            "active_violations_count": 0
        }
        
        try:
            # Obter políticas de alerta
            policies = await self.get_all_alert_policies()
            alerts_data["policies"] = policies
            
            # Obter violações ativas
            violations_query = """
            query AlertViolations {
                actor {
                    account(id: %s) {
                        violations(includeAcknowledgedViolations: false, onlyOpen: true) {
                            policyName
                            conditionName
                            label
                            level
                            openedAt
                            entityId
                            entityName
                            entityType
                            violationId
                            violationUrl
                        }
                    }
                }
            }
            """ % self.account_id
            
            result = await self.execute_graphql_query(violations_query)
            
            if "data" in result and "actor" in result["data"]:
                violations = result["data"]["actor"]["account"]["violations"]
                alerts_data["violations"] = violations
                alerts_data["active_violations_count"] = len(violations)
                
        except Exception as e:
            logger.error(f"Erro ao obter alertas: {e}")
            logger.error(traceback.format_exc())
            alerts_data["error"] = str(e)
            
        return alerts_data
    
    async def collect_full_entity_data(self) -> Dict:
        """
        Coleta todos os dados disponíveis do New Relic, incluindo entidades, métricas, logs,
        dashboards, alertas, rastreamento distribuído e dados avançados de infraestrutura.
        
        Returns:
            Dict com todos os dados coletados
        """
        logger.info("Iniciando coleta completa de dados do New Relic")
        
        result = {
            "collected_at": datetime.now().isoformat(),
            "entities": {},
            "metrics": {},
            "logs": {},
            "alerts": {},
            "dashboards": {},
            "distributed_tracing": {},
            "kubernetes_data": {},
            "serverless_data": {},
            "infrastructure_details": {},
            "capacity_report": {},
            "dashboard_nrql": {},
            "coverage_report": {}
        }
        
        try:
            # 1. Coletar entidades por domínio
            logger.info("Coletando todas as entidades por domínio")
            domains = ["APM", "BROWSER", "MOBILE", "INFRA", "SYNTH"]
            entity_count = 0
            
            for domain in domains:
                domain_entities = await self.fetch_entities_by_domain(domain)
                result["entities"][domain] = domain_entities
                entity_count += len(domain_entities)
                
            logger.info(f"Total de entidades coletadas: {entity_count}")
            
            # 2. Coletar métricas para cada entidade (amostragem)
            logger.info("Coletando métricas para uma amostra de entidades")
            sampled_entities = self._sample_entities(result["entities"], max_per_domain=5)
            
            for domain, entities in sampled_entities.items():
                result["metrics"][domain] = {}
                
                for entity in entities:
                    entity_guid = entity.get("guid")
                    entity_name = entity.get("name", "Unknown")
                    
                    if entity_guid:
                        logger.info(f"Coletando métricas para entidade {entity_name} ({entity_guid})")
                        metrics = await self.get_entity_metrics(entity_guid)
                        result["metrics"][domain][entity_guid] = metrics
            
            # 3. Coletar logs (amostragem)
            logger.info("Coletando amostra de logs")
            logs_sample = await self.fetch_logs_sample(limit=100)
            result["logs"]["sample"] = logs_sample
            
            # 4. Coletar alertas
            logger.info("Coletando alertas")
            alerts = await self.fetch_alerts()
            result["alerts"] = alerts
            
            # 5. Coletar dashboards
            logger.info("Coletando dashboards")
            dashboards = await self.fetch_entities(entity_type="DASHBOARD")
            result["dashboards"]["list"] = dashboards
            
            # Se houver dashboards, analisar uma amostra deles
            if dashboards:
                # Analisar até 5 dashboards
                sampled_dashboards = dashboards[:min(5, len(dashboards))]
                result["dashboards"]["analyzed"] = {}
                
                for dashboard in sampled_dashboards:
                    dashboard_guid = dashboard.get("guid")
                    if dashboard_guid:
                        dashboard_analysis = await self.analyze_dashboard(dashboard_guid)
                        result["dashboards"]["analyzed"][dashboard_guid] = dashboard_analysis
                        
                # Extrair todas as consultas NRQL de todos os dashboards
                result["dashboard_nrql"] = await self.extract_all_dashboard_nrql()
            
            # 6. Coletar dados de rastreamento distribuído (amostragem)
            logger.info("Coletando amostra de dados de rastreamento distribuído")
            distributed_tracing_sample = await self.fetch_distributed_tracing_sample()
            result["distributed_tracing"]["sample"] = distributed_tracing_sample
            
            # 7. Coletar dados de Kubernetes (se disponível)
            logger.info("Verificando clusters Kubernetes")
            k8s_entities = await self.fetch_entities(entity_type="KUBERNETES_CLUSTER")
            
            if k8s_entities:
                result["kubernetes_data"]["clusters"] = {}
                # Analisar até 3 clusters
                sampled_clusters = k8s_entities[:min(3, len(k8s_entities))]
                
                for cluster in sampled_clusters:
                    cluster_guid = cluster.get("guid")
                    if cluster_guid:
                        cluster_metrics = await self.collect_kubernetes_metrics(cluster_guid)
                        result["kubernetes_data"]["clusters"][cluster_guid] = {
                            "details": cluster,
                            "metrics": cluster_metrics
                        }
            
            # 8. Coletar dados de funções serverless (se disponível)
            logger.info("Verificando funções serverless")
            serverless_entities = await self.fetch_entities(entity_type="AWSLAMBDAFUNCTION")
            
            if serverless_entities:
                result["serverless_data"]["functions"] = {}
                # Analisar até 5 funções
                sampled_functions = serverless_entities[:min(5, len(serverless_entities))]
                
                for function in sampled_functions:
                    function_guid = function.get("guid")
                    if function_guid:
                        function_metrics = await self.collect_serverless_metrics(function_guid)
                        result["serverless_data"]["functions"][function_guid] = {
                            "details": function,
                            "metrics": function_metrics
                        }
            
            # 9. Coletar dados avançados de infraestrutura
            logger.info("Coletando dados avançados de infraestrutura")
            infra_details = await self.collect_infrastructure_details()
            result["infrastructure_details"] = infra_details
            
            # 10. Gerar relatório de capacidade
            logger.info("Gerando relatório de capacidade e uso de recursos")
            capacity_report = await self.generate_capacity_report()
            result["capacity_report"] = capacity_report
            
            # 11. Gerar relatório de cobertura
            coverage = {
                "total_entities": entity_count,
                "entities_by_domain": {domain: len(entities) for domain, entities in result["entities"].items()},
                "metrics_sample_count": sum(len(domain_metrics) for domain_metrics in result["metrics"].values()),
                "logs_sample_count": len(result["logs"].get("sample", [])),
                "alerts_count": len(result["alerts"]),
                "dashboards_count": len(result["dashboards"].get("list", [])),
                "dashboards_analyzed": len(result["dashboards"].get("analyzed", {})),
                "nrql_queries_extracted": sum(len(dashboard.get("queries", [])) for dashboard in result["dashboard_nrql"].values() if isinstance(dashboard, dict)),
                "kubernetes_clusters_analyzed": len(result["kubernetes_data"].get("clusters", {})),
                "serverless_functions_analyzed": len(result["serverless_data"].get("functions", {})),
                "infrastructure_hosts_analyzed": len(result["infrastructure_details"].get("hosts", {})),
                "infrastructure_containers_analyzed": len(result["infrastructure_details"].get("containers", {})),
                "service_topology_entities": len(result["infrastructure_details"].get("services_topology", {}))
            }
            
            result["coverage_report"] = coverage
            
            logger.info("Coleta completa de dados do New Relic concluída com sucesso")
            
        except Exception as e:
            logger.error(f"Erro na coleta completa de dados do New Relic: {e}")
            logger.error(traceback.format_exc())
            result["error"] = str(e)
            
        return result

    async def generate_capacity_report(self) -> Dict:
        """
        Gera relatório de capacidade e uso de recursos
        
        Returns:
            Dict com relatório de capacidade
        """
        logger.info("Gerando relatório de capacidade e uso de recursos")
        
        capacity_report = {
            "cpu_usage": {},
            "memory_usage": {},
            "disk_usage": {},
            "network_usage": {},
            "service_health": {},
            "scaling_recommendations": {}
        }
        
        try:
            # CPU usage por host
            cpu_query = """
            SELECT average(cpuPercent) FROM SystemSample FACET hostname 
            SINCE 1 day ago TIMESERIES 1 hour
            """
            cpu_result = await self.execute_nrql_query(cpu_query)
            capacity_report["cpu_usage"]["timeseries"] = cpu_result.get("results", [])
            
            # CPU média/máxima por host
            cpu_stats_query = """
            SELECT average(cpuPercent) as 'avg_cpu', max(cpuPercent) as 'max_cpu' 
            FROM SystemSample FACET hostname 
            SINCE 1 day ago
            """
            cpu_stats_result = await self.execute_nrql_query(cpu_stats_query)
            capacity_report["cpu_usage"]["stats"] = cpu_stats_result.get("results", [])
            
            # Memória
            memory_query = """
            SELECT average(memoryUsedBytes/memoryTotalBytes)*100 as 'memory_percent' 
            FROM SystemSample FACET hostname 
            SINCE 1 day ago TIMESERIES 1 hour
            """
            memory_result = await self.execute_nrql_query(memory_query)
            capacity_report["memory_usage"]["timeseries"] = memory_result.get("results", [])
            
            memory_stats_query = """
            SELECT average(memoryUsedBytes/memoryTotalBytes)*100 as 'avg_memory', 
            max(memoryUsedBytes/memoryTotalBytes)*100 as 'max_memory' 
            FROM SystemSample FACET hostname 
            SINCE 1 day ago
            """
            memory_stats_result = await self.execute_nrql_query(memory_stats_query)
            capacity_report["memory_usage"]["stats"] = memory_stats_result.get("results", [])
            
            # Disco
            disk_query = """
            SELECT average(diskUsedPercent) FROM SystemSample 
            FACET hostname, mountPoint 
            WHERE mountPoint NOT LIKE '/snap%' 
            SINCE 1 day ago
            """
            disk_result = await self.execute_nrql_query(disk_query)
            capacity_report["disk_usage"]["by_mount"] = disk_result.get("results", [])
            
            # Rede
            network_query = """
            SELECT rate(sum(networkReceiveBytes), 1 minute) as 'receiveBytes', 
            rate(sum(networkTransmitBytes), 1 minute) as 'transmitBytes' 
            FROM SystemSample FACET hostname 
            SINCE 1 day ago TIMESERIES 1 hour
            """
            network_result = await self.execute_nrql_query(network_query)
            capacity_report["network_usage"]["timeseries"] = network_result.get("results", [])
            
            # Saúde dos serviços
            service_health_query = """
            SELECT filter(count(*), WHERE error IS true)/count(*)*100 as 'error_rate', 
            average(duration) as 'avg_duration',
            percentile(duration, 99) as 'p99_duration'
            FROM Transaction FACET appName 
            SINCE 1 day ago
            """
            service_result = await self.execute_nrql_query(service_health_query)
            capacity_report["service_health"]["metrics"] = service_result.get("results", [])
            
            # Gerar recomendações de escala
            # Para cada host com alta CPU ou memória
            high_usage_hosts = []
            for host_stat in capacity_report["cpu_usage"]["stats"]:
                if host_stat.get("avg_cpu", 0) > 70 or host_stat.get("max_cpu", 0) > 90:
                    high_usage_hosts.append({
                        "hostname": host_stat.get("hostname"),
                        "resource_type": "CPU",
                        "avg_usage": host_stat.get("avg_cpu", 0),
                        "max_usage": host_stat.get("max_cpu", 0),
                        "recommendation": "Consider scaling up CPU resources or distributing workload"
                    })
                    
            for host_stat in capacity_report["memory_usage"]["stats"]:
                if host_stat.get("avg_memory", 0) > 80 or host_stat.get("max_memory", 0) > 95:
                    high_usage_hosts.append({
                        "hostname": host_stat.get("hostname"),
                        "resource_type": "Memory",
                        "avg_usage": host_stat.get("avg_memory", 0),
                        "max_usage": host_stat.get("max_memory", 0),
                        "recommendation": "Consider adding more memory or optimizing memory usage"
                    })
                    
            capacity_report["scaling_recommendations"]["high_usage_hosts"] = high_usage_hosts
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de capacidade: {e}")
            logger.error(traceback.format_exc())
            capacity_report["error"] = str(e)
            
        return capacity_report
    
    async def collect_infrastructure_details(self) -> Dict:
        """
        Coleta dados detalhados de infraestrutura, incluindo hosts, containers, kubernetes e topologia de serviços
        
        Returns:
            Dict com detalhes da infraestrutura
        """
        logger.info("Coletando dados avançados de infraestrutura")
        
        infra_data = {
            "hosts": {},
            "containers": {},
            "kubernetes": {},
            "services_topology": {},
            "cloud_resources": {}
        }
        
        try:
            # Coletar dados de hosts
            host_entities = await self.fetch_entities(entity_type="HOST")
            for host in host_entities:
                host_guid = host.get("guid")
                if host_guid:
                    # Obter métricas básicas de host
                    host_metrics_nrql = f"""
                    SELECT latest(cpuPercent), latest(memoryUsedBytes/memoryTotalBytes)*100 as 'memoryUsedPercent', 
                    latest(diskUsedPercent), latest(loadAverageOneMinute), latest(fullHostname) 
                    FROM SystemSample 
                    WHERE entityGuid = '{host_guid}'
                    SINCE 5 MINUTES AGO
                    """
                    metrics_result = await self.execute_nrql_query(host_metrics_nrql)
                    
                    # Obter processos em execução
                    processes_nrql = f"""
                    SELECT latest(processDisplayName) as 'process', latest(commandLine), latest(cpuPercent), 
                    latest(memoryResidentSizeBytes) FROM ProcessSample 
                    WHERE entityGuid = '{host_guid}' 
                    FACET processId 
                    ORDER BY latest(cpuPercent) DESC 
                    LIMIT 10 
                    SINCE 5 MINUTES AGO
                    """
                    processes_result = await self.execute_nrql_query(processes_nrql)
                    
                    # Armazenar dados do host
                    infra_data["hosts"][host_guid] = {
                        "details": host,
                        "metrics": metrics_result.get("results", []),
                        "top_processes": processes_result.get("results", [])
                    }
            
            # Coletar dados de containers
            container_entities = await self.fetch_entities(entity_type="CONTAINER")
            for container in container_entities:
                container_guid = container.get("guid")
                if container_guid:
                    # Obter métricas de container
                    container_metrics_nrql = f"""
                    SELECT latest(cpuPercent), latest(memoryUsageBytes), latest(status), 
                    latest(containerName), latest(imageName)
                    FROM ContainerSample
                    WHERE entityGuid = '{container_guid}'
                    SINCE 5 MINUTES AGO
                    """
                    container_metrics = await self.execute_nrql_query(container_metrics_nrql)
                    
                    infra_data["containers"][container_guid] = {
                        "details": container,
                        "metrics": container_metrics.get("results", [])
                    }
            
            # Coletar dados de Kubernetes
            k8s_clusters = await self.fetch_entities(entity_type="KUBERNETES_CLUSTER")
            for cluster in k8s_clusters:
                cluster_guid = cluster.get("guid")
                if cluster_guid:
                    # Coletar métricas de Kubernetes
                    kubernetes_metrics = await self.collect_kubernetes_metrics(cluster_guid)
                    
                    infra_data["kubernetes"][cluster_guid] = {
                        "details": cluster,
                        "metrics": kubernetes_metrics
                    }
                    
            # Coletar topologia de serviços
            service_map_query = """
            {
              actor {
                entitySearch(query: "domain IN ('APM', 'BROWSER', 'MOBILE') AND type IN ('APPLICATION', 'SERVICE')") {
                  results {
                    entities {
                      guid
                      name
                      domain
                      entityType
                    }
                  }
                }
              }
            }
            """
            
            service_map_result = await self.execute_graphql_query(service_map_query)
            if "data" in service_map_result and "actor" in service_map_result["data"]:
                entities = service_map_result["data"]["actor"]["entitySearch"]["results"]["entities"]
                
                # Construir mapa de topologia
                service_topology = {}
                
                # Para cada serviço, obter sua topologia
                for entity in entities[:10]:  # Limitar para os 10 primeiros para não sobrecarregar
                    entity_guid = entity.get("guid")
                    if entity_guid:
                        topology = await self.get_service_topology(entity_guid)
                        service_topology[entity_guid] = {
                            "entity": entity,
                            "topologia": topology
                        }
                        
                infra_data["services_topology"] = service_topology
            
            # Coletar recursos cloud (AWS, Azure, GCP)
            cloud_entities_query = """
            {
              actor {
                entitySearch(query: "domain = 'INFRA' AND type LIKE 'CLOUD%'") {
                  results {
                    entities {
                      guid
                      name
                      entityType
                      domain
                    }
                  }
                }
              }
            }
            """
            
            cloud_result = await self.execute_graphql_query(cloud_entities_query)
            if "data" in cloud_result and "actor" in cloud_result["data"]:
                cloud_entities = cloud_result["data"]["actor"]["entitySearch"]["results"]["entities"]
                
                # Organizar por provedor cloud
                for entity in cloud_entities:
                    entity_type = entity.get("entityType", "")
                    provider = "other"
                    
                    if "AWS" in entity_type:
                        provider = "aws"
                    elif "AZURE" in entity_type:
                        provider = "azure"
                    elif "GCP" in entity_type:
                        provider = "gcp"
                        
                    if provider not in infra_data["cloud_resources"]:
                        infra_data["cloud_resources"][provider] = []
                        
                    infra_data["cloud_resources"][provider].append(entity)
            
        except Exception as e:
            logger.error(f"Erro ao coletar dados de infraestrutura: {e}")
            logger.error(traceback.format_exc())
            infra_data["error"] = str(e)
            
        return infra_data
    
    async def get_service_topology(self, entity_guid) -> Dict:
        """
        Obtém topologia de serviço e dados de dependências.
        
        Args:
            entity_guid: GUID da entidade de serviço
            
        Returns:
            Dict com dados de topologia
        """
        try:
            query = """
            query ServiceTopologyQuery($guid: EntityGuid!) {
                actor {
                    entity(guid: $guid) {
                        ... on ApmApplicationEntity {
                            name
                            guid
                            relatedEntities {
                                source {
                                    entity {
                                        name
                                        guid
                                        entityType
                                    }
                                    relationships {
                                        type
                                        source {
                                            entity {
                                                name
                                                guid
                                                entityType
                                            }
                                        }
                                        target {
                                            entity {
                                                name
                                                guid
                                                entityType
                                            }
                                        }
                                    }
                                }
                                target {
                                    entity {
                                        name
                                        guid
                                        entityType
                                    }
                                    relationships {
                                        type
                                        source {
                                            entity {
                                                name
                                                guid
                                                entityType
                                            }
                                        }
                                        target {
                                            entity {
                                                name
                                                guid
                                                entityType
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """
            
            variables = {
                "guid": entity_guid
            }
            
            result = await self.execute_graphql_query(query, variables)
            
            if "error" in result:
                logger.error(f"Erro ao obter topologia de serviço para {entity_guid}: {result}")
                return {"error": result["error"]}
                
            topology_data = result.get("data", {}).get("actor", {}).get("entity", {}).get("relatedEntities", {})
            
            # Obter métricas de dependências via NRQL
            dependencies_query = f"""
            SELECT count(*) as callCount, 
                   average(duration) as avgDuration, 
                   percentage(count(*), WHERE error is true) as errorRate
            FROM Span 
            WHERE entity.guid = '{entity_guid}' AND (spanCategory = 'http' OR spanCategory = 'datastore')
            SINCE 30 minutes ago 
            FACET name, spanCategory
            """
            
            dependencies_result = await self.execute_nrql_query(dependencies_query)
            dependencies_metrics = dependencies_result.get("results", []) if "error" not in dependencies_result else []
            
            return {
                "topologia": topology_data,
                "dependencies_metrics": dependencies_metrics
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter topologia de serviço para {entity_guid}: {e}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    async def collect_kubernetes_metrics(self, cluster_guid) -> Dict:
        """
        Coleta métricas detalhadas de um cluster Kubernetes
        
        Args:
            cluster_guid: GUID do cluster Kubernetes
            
        Returns:
            Dict com métricas do cluster
        """
        logger.info(f"Coletando métricas do cluster Kubernetes {cluster_guid}")
        
        metrics = {
            "cluster": {},
            "pods": [],
            "deployments": [],
            "nodes": []
        }
        
        try:
            # Métricas do cluster
            cluster_metrics_nrql = f"""
            SELECT latest(clusterName), latest(podCount), latest(deploymentCount), latest(nodeCount)
            FROM K8sClusterSample
            WHERE entityGuid = '{cluster_guid}'
            SINCE 5 MINUTES AGO
            """
            cluster_result = await self.execute_nrql_query(cluster_metrics_nrql)
            metrics["cluster"]["overview"] = cluster_result.get("results", [])
            
            # Utilização de recursos no cluster
            resources_nrql = f"""
            SELECT average(cpuUsedCores), average(cpuRequestedCores), average(cpuLimitCores),
            average(memoryUsedBytes), average(memoryRequestedBytes), average(memoryLimitBytes)
            FROM K8sClusterSample
            WHERE entityGuid = '{cluster_guid}'
            TIMESERIES 5 minutes
            SINCE 30 MINUTES AGO
            """
            resources_result = await self.execute_nrql_query(resources_nrql)
            metrics["cluster"]["resources"] = resources_result.get("results", [])
            
            # Top pods por uso de CPU
            pods_cpu_nrql = f"""
            SELECT average(cpuUsedCores), average(cpuRequestedCores)
            FROM K8sContainerSample
            WHERE clusterName IN (SELECT latest(clusterName) FROM K8sClusterSample WHERE entityGuid = '{cluster_guid}')
            FACET podName
            ORDER BY average(cpuUsedCores) DESC
            LIMIT 10
            SINCE 5 MINUTES AGO
            """
            pods_cpu_result = await self.execute_nrql_query(pods_cpu_nrql)
            metrics["pods"].append({
                "metric": "cpu_usage",
                "data": pods_cpu_result.get("results", [])
            })
            
            # Top pods por uso de memória
            pods_memory_nrql = f"""
            SELECT average(memoryUsageBytes), average(memoryLimitBytes)
            FROM K8sContainerSample
            WHERE clusterName IN (SELECT latest(clusterName) FROM K8sClusterSample WHERE entityGuid = '{cluster_guid}')
            FACET podName
            ORDER BY average(memoryUsageBytes) DESC
            LIMIT 10
            SINCE 5 MINUTES AGO
            """
            pods_memory_result = await self.execute_nrql_query(pods_memory_nrql)
            metrics["pods"].append({
                "metric": "memory_usage",
                "data": pods_memory_result.get("results", [])
            })
            
            # Status dos pods
            pod_status_nrql = f"""
            SELECT count(*) 
            FROM K8sPodSample 
            WHERE clusterName IN (SELECT latest(clusterName) FROM K8sClusterSample WHERE entityGuid = '{cluster_guid}')
            FACET status
            """
            pod_status_result = await self.execute_nrql_query(pod_status_nrql)
            metrics["pods"].append({
                "metric": "pod_status",
                "data": pod_status_result.get("results", [])
            })
            
            # Top deployments por uso de CPU
            deployments_cpu_nrql = f"""
            SELECT average(cpuUsedCores), average(cpuRequestedCores)
            FROM K8sContainerSample
            WHERE clusterName IN (SELECT latest(clusterName) FROM K8sClusterSample WHERE entityGuid = '{cluster_guid}')
            FACET deploymentName
            ORDER BY average(cpuUsedCores) DESC
            LIMIT 10
            SINCE 5 MINUTES AGO
            """
            deployments_cpu_result = await self.execute_nrql_query(deployments_cpu_nrql)
            metrics["deployments"].append({
                "metric": "cpu_usage",
                "data": deployments_cpu_result.get("results", [])
            })
            
            # Top deployments por uso de memória
            deployments_memory_nrql = f"""
            SELECT average(memoryUsageBytes), average(memoryLimitBytes)
            FROM K8sContainerSample
            WHERE clusterName IN (SELECT latest(clusterName) FROM K8sClusterSample WHERE entityGuid = '{cluster_guid}')
            FACET deploymentName
            ORDER BY average(memoryUsageBytes) DESC
            LIMIT 10
            SINCE 5 MINUTES AGO
            """
            deployments_memory_result = await self.execute_nrql_query(deployments_memory_nrql)
            metrics["deployments"].append({
                "metric": "memory_usage",
                "data": deployments_memory_result.get("results", [])
            })
            
            # Status dos deployments
            deployment_status_nrql = f"""
            SELECT latest(deploymentStatus) 
            FROM K8sDeploymentSample 
            WHERE clusterName IN (SELECT latest(clusterName) FROM K8sClusterSample WHERE entityGuid = '{cluster_guid}')
            FACET deploymentName
            """
            deployment_status_result = await self.execute_nrql_query(deployment_status_nrql)
            metrics["deployments"].append({
                "metric": "status",
                "data": deployment_status_result.get("results", [])
            })
            
            # Nós do cluster
            nodes_nrql = f"""
            SELECT average(cpuUsedCores), average(memoryUsedBytes), average(diskUsedBytes)
            FROM K8sNodeSample
            WHERE clusterName IN (SELECT latest(clusterName) FROM K8sClusterSample WHERE entityGuid = '{cluster_guid}')
            FACET nodeName
            SINCE 5 MINUTES AGO
            """
            nodes_result = await self.execute_nrql_query(nodes_nrql)
            metrics["nodes"] = nodes_result.get("results", [])
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas do cluster Kubernetes {cluster_guid}: {e}")
            logger.error(traceback.format_exc())
            metrics["error"] = str(e)
            
        return metrics

    async def analyze_dashboard(self, dashboard_guid) -> Dict:
        """
        Analisa um dashboard e extrai informações detalhadas
        
        Args:
            dashboard_guid: GUID do dashboard
            
        Returns:
            Dict com análise do dashboard
        """
        logger.info(f"Analisando dashboard {dashboard_guid}")
        
        try:
            # Obter detalhes do dashboard
            dashboard_details = await self.get_dashboard_details(dashboard_guid)
            
            if not dashboard_details:
                return {"error": "Dashboard não encontrado"}
                
            # Analisar widgets
            widgets_analysis = await self.analyze_dashboard_widgets(dashboard_guid)
            
            return {
                "details": dashboard_details,
                "widgets_analysis": widgets_analysis
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar dashboard {dashboard_guid}: {e}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}
            
    async def analyze_dashboard_widgets(self, dashboard_guid) -> List[Dict]:
        """
        Analisa os widgets de um dashboard e extrai informações detalhadas.
        
        Args:
            dashboard_guid: GUID do dashboard
            
        Returns:
            Lista com análise de cada widget
        """
        logger.info(f"Analisando widgets do dashboard {dashboard_guid}")
        
        try:
            # Obter detalhes do dashboard
            dashboard_details = await self.get_dashboard_details(dashboard_guid)
            
            if not dashboard_details:
                return []
                
            widgets_analysis = []
            all_nrql_queries = []
            
            # Para cada página no dashboard
            pages = dashboard_details.get("pages", [])
            for page in pages:
                # Para cada widget na página
                widgets = page.get("widgets", [])
                for widget in widgets:
                    widget_id = widget.get("id")
                    widget_title = widget.get("title", "Widget sem título")
                    widget_type = widget.get("visualization", {}).get("id", "desconhecido")
                    raw_config = widget.get("rawConfiguration", {})
                    
                    # Extrair NRQL do widget se disponível
                    nrql = None
                    if "nrqlQueries" in raw_config:
                        nrql_queries = raw_config.get("nrqlQueries", [])
                        if nrql_queries and len(nrql_queries) > 0:
                            nrql = nrql_queries[0].get("query", "")
                            all_nrql_queries.append(nrql)
                    elif "query" in raw_config:
                        nrql = raw_config.get("query", "")
                        all_nrql_queries.append(nrql)
                        
                    widget_analysis = {
                        "id": widget_id,
                        "title": widget_title,
                        "type": widget_type,
                        "nrql": nrql
                    }
                    
                    widgets_analysis.append(widget_analysis)
            
            return {
                "widgets": widgets_analysis,
                "all_nrql_queries": all_nrql_queries,
                "pages": [{"name": page.get("name", ""), "widgets": len(page.get("widgets", []))} for page in pages]
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar widgets do dashboard {dashboard_guid}: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def extract_all_dashboard_nrql(self) -> Dict:
        """
        Extrai todas as consultas NRQL de todos os dashboards
        
        Returns:
            Dict com consultas NRQL por dashboard
        """
        logger.info("Extraindo todas as consultas NRQL de todos os dashboards")
        
        dashboard_queries = {}
        
        try:
            # Obter lista de dashboards
            dashboards = await self.fetch_entities(entity_type="DASHBOARD")
            
            # Para cada dashboard, analisar widgets e extrair NRQL
            for dashboard in dashboards[:20]:  # Limitar para 20 dashboards para não sobrecarregar
                dashboard_guid = dashboard.get("guid")
                dashboard_name = dashboard.get("name", "Unknown Dashboard")
                
                if not dashboard_guid:
                    continue
                
                logger.info(f"Extraindo NRQL do dashboard {dashboard_name}")
                
                # Obter detalhes do dashboard
                details = await self.get_dashboard_details(dashboard_guid)
                
                if not details:
                    continue
                    
                # Extrair consultas de cada widget
                queries = []
                
                for page in details.get("pages", []):
                    for widget in page.get("widgets", []):
                        raw_config = widget.get("rawConfiguration", {})
                        nrql_info = await self.extract_nrql_from_dashboard_widget(raw_config)
                        
                        if nrql_info and "query" in nrql_info:
                            queries.append({
                                "widget_id": widget.get("id"),
                                "widget_title": widget.get("title", "Sem título"),
                                "query": nrql_info["query"],
                                "query_type": nrql_info["type"]
                            })
                
                dashboard_queries[dashboard_guid] = {
                    "nome": dashboard_name,
                    "consultas": queries,
                    "total_consultas": len(queries)
                }
                
        except Exception as e:
            logger.error(f"Erro ao extrair NRQL de dashboards: {e}")
            logger.error(traceback.format_exc())
            dashboard_queries["erro"] = str(e)
            
        return dashboard_queries
    
    async def extract_nrql_from_dashboard_widget(self, widget_config) -> Dict:
        """
        Extrai consultas NRQL de configurações de widgets de dashboard.
        
        Args:
            widget_config: Configuração do widget obtida do dashboard
            
        Returns:
            Dict com informações da consulta NRQL
        """
        try:
            if not widget_config:
                return {}
                
            # A configuração pode estar em diferentes formatos dependendo do tipo de widget
            nrql_info = {}
            
            # Tentar extrair de diferentes localizações na configuração
            if isinstance(widget_config, dict):
                # Para widgets baseados em NRQL
                if "nrqlQueries" in widget_config:
                    queries = widget_config.get("nrqlQueries", [])
                    if queries and len(queries) > 0:
                        first_query = queries[0]
                        query = first_query.get("query", "")
                        if query:
                            return {
                                "type": "nrql_multi",
                                "query": query,
                                "total_queries": len(queries)
                            }
                
                # Para widgets simples com uma consulta única
                if "query" in widget_config:
                    query = widget_config.get("query")
                    if query and isinstance(query, str):
                        return {
                            "type": "nrql_single",
                            "query": query
                        }
                    
                # Para widgets com fonte de dados específica
                if "source" in widget_config and isinstance(widget_config["source"], dict):
                    source = widget_config["source"]
                    if "nrql" in source and isinstance(source["nrql"], str):
                        return {
                            "type": "nrql_source",
                            "query": source["nrql"]
                        }
            
            # Se o widget não for baseado em NRQL ou não for possível extrair
            return {"tipo": "não_nrql", "configuração": widget_config}
                
        except Exception as e:
            logger.error(f"Erro ao extrair NRQL do widget: {e}")
            return {"erro": str(e), "configuração": widget_config}
    
    async def fetch_entities(self, entity_type: str = None) -> List[Dict]:
        """
        Busca entidades por tipo.
        
        Args:
            entity_type: Tipo específico de entidade a ser buscado
            
        Returns:
            Lista de entidades
        """
        logger.info(f"Buscando entidades do tipo: {entity_type or 'todos'}")
        
        query = """
        {
          actor {
            entitySearch(query: "%s") {
              results {
                entities {
                  guid
                  name
                  domain
                  type
                  entityType
                  reporting
                  account {
                    id
                    name
                  }
                }
              }
            }
          }
        }
        """
        
        # Construir query de busca
        search_query = ""
        if entity_type:
            search_query = f"type = '{entity_type}'"
        
        try:
            result = await self.execute_graphql_query(query % search_query)
            
            if "error" in result:
                logger.error(f"Erro ao buscar entidades: {result['error']}")
                return []
                
            entities = result.get("data", {}).get("actor", {}).get("entitySearch", {}).get("results", {}).get("entities", [])
            return entities
            
        except Exception as e:
            logger.error(f"Erro ao buscar entidades: {e}")
            logger.error(traceback.format_exc())
            return []