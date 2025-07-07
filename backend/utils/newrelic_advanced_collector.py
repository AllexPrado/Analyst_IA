"""
Módulo de coleta de dados avançados do New Relic.
Este coletor utiliza a API NRQL e GraphQL do New Relic para obter todos os dados possíveis:
- Métricas padrão (Apdex, Response Time, Error Rate, Throughput)
- Logs detalhados
- Traces detalhados
- Backtraces de erros
- Queries SQL
- Informações de execução (módulo, linha de código, tempo)
- Dados de distribuição
- Relacionamentos entre entidades

Esta coleta avançada permite que a IA tenha acesso a 100% dos dados do New Relic.
"""


import os
import logging
import json
import asyncio
import aiohttp
from aiohttp import ClientConnectionError, TCPConnector
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
# Importa utilitário centralizado
from utils.newrelic_common import (
    execute_nrql_query_common,
    execute_graphql_query_common,
    log_info, log_warning, log_error
)



# Centralização do filtro de logging pode ser feita no utilitário, mas mantido aqui por compatibilidade
class IgnoreClientConnectionErrorFilter(logging.Filter):
    def filter(self, record):
        if record.exc_info:
            exc_type = record.exc_info[0]
            if exc_type is not None and issubclass(exc_type, ClientConnectionError):
                return False
        if 'ClientConnectionError' in record.getMessage() and 'shutdown' in record.getMessage():
            return False
        return True



logger = logging.getLogger(__name__)
logger.addFilter(IgnoreClientConnectionErrorFilter())
# Adiciona o filtro ao logger root para silenciar erros globais de shutdown de conexão
logging.getLogger().addFilter(IgnoreClientConnectionErrorFilter())

load_dotenv()

NEW_RELIC_API_KEY = os.getenv("NEW_RELIC_API_KEY")
NEW_RELIC_QUERY_KEY = os.getenv("NEW_RELIC_QUERY_KEY")
NEW_RELIC_ACCOUNT_ID = os.getenv("NEW_RELIC_ACCOUNT_ID")

if not NEW_RELIC_API_KEY or not NEW_RELIC_ACCOUNT_ID or not NEW_RELIC_QUERY_KEY:
    log_error("NEW_RELIC_API_KEY, NEW_RELIC_QUERY_KEY e NEW_RELIC_ACCOUNT_ID são obrigatórios!")
    raise RuntimeError("NEW_RELIC_API_KEY, NEW_RELIC_QUERY_KEY e NEW_RELIC_ACCOUNT_ID são obrigatórios!")

# Configurações
TIMEOUT = 60.0  # Timeout maior para consultas complexas
MAX_RETRIES = 3
RETRY_DELAY = 10.0  # Delay maior para evitar bloqueio
BATCH_SIZE = 1  # Reduzido ao mínimo para evitar rate limit e problemas de conexão

NR_GRAPHQL_URL = "https://api.newrelic.com/graphql"
NR_API_URL = f"https://api.newrelic.com/v2"
# Endpoint NRQL atualizado conforme documentação oficial
NR_NRDB_URL = f"https://api.newrelic.com/v1/accounts/{NEW_RELIC_ACCOUNT_ID}/query"

# Headers separados para cada tipo de requisição
NRQL_HEADERS = {
    "X-Query-Key": NEW_RELIC_QUERY_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}
GRAPHQL_HEADERS = {
    "Api-Key": NEW_RELIC_API_KEY,
    "Content-Type": "application/json"
}

# Períodos de consulta para dados históricos
PERIODOS = {
    "30min": "SINCE 30 MINUTES AGO",
    "3h": "SINCE 3 HOURS AGO",
    "24h": "SINCE 24 HOURS AGO",
    "7d": "SINCE 7 DAYS AGO",
    "30d": "SINCE 30 DAYS AGO"
}

async def execute_nrql_query(nrql: str, timeout: float = TIMEOUT, session: Optional[aiohttp.ClientSession] = None) -> Dict:
    """
    Executa consulta NRQL e retorna resultados. (Centralizado via utilitário)
    """
    graphql_query = f'''
    {{
      actor {{
        account(id: {NEW_RELIC_ACCOUNT_ID}) {{
          nrql(query: "{nrql}") {{
            results
            metadata {{
              eventTypes
              facets
            }}
          }}
        }}
      }}
    }}
    '''
    # Utiliza função centralizada
    return await execute_nrql_query_common(
        graphql_query,
        headers=GRAPHQL_HEADERS,
        url=NR_GRAPHQL_URL,
        timeout=timeout,
        session=session,
        max_retries=MAX_RETRIES,
        retry_delay=RETRY_DELAY
    )

async def execute_graphql_query(query: str, variables: Optional[Dict] = None, timeout: float = TIMEOUT, session: Optional[aiohttp.ClientSession] = None) -> Dict:
    """
    Executa consulta GraphQL na API do New Relic. (Centralizado via utilitário)
    """
    return await execute_graphql_query_common(
        query,
        headers=GRAPHQL_HEADERS,
        url=NR_GRAPHQL_URL,
        variables=variables,
        timeout=timeout,
        session=session,
        max_retries=MAX_RETRIES,
        retry_delay=RETRY_DELAY
    )

async def fetch_logs_sample(limit=100, session: Optional[aiohttp.ClientSession] = None):
    """
    Coleta uma amostra global de logs do New Relic via NRQL.
    """
    try:
        query = f"SELECT * FROM Log SINCE 30 MINUTES AGO LIMIT {limit}"
        result = await execute_nrql_query(query, session=session)
        logs = result.get("results", [])
        if not logs:
            log_warning("No logs found in the sample.")
        return logs
    except Exception as e:
        log_error(f"Error fetching logs sample: {e}")
        return []



async def fetch_dashboards_sample(limit=20, session: Optional[aiohttp.ClientSession] = None):
    """Coleta uma amostra de dashboards do New Relic via GraphQL."""
    try:
        query = f'''
        {{
          actor {{
            entitySearch(query: "type='DASHBOARD' AND accountId = {NEW_RELIC_ACCOUNT_ID}") {{
              results {{
                entities {{
                  guid
                  name
                  accountId
                  permalink
                }}
              }}
            }}
          }}
        }}
        '''
        result = await execute_graphql_query(query, session=session)
        entities = result.get("data", {}).get("actor", {}).get("entitySearch", {}).get("results", {}).get("entities", [])
        if not entities:
            log_warning(f"Nenhum dashboard retornado pela query GraphQL. Resposta bruta: {result}")
        return entities[:limit]
    except Exception as e:
        log_error(f"Erro ao coletar dashboards globais: {e}")
        return []



async def get_all_entities(session: aiohttp.ClientSession) -> List[Dict]:
    """
    Recupera todas as entidades do New Relic via GraphQL.
    
    Returns:
        Lista de entidades com seus detalhes básicos
    """
    # Novo padrão: busca por todos os domínios relevantes usando o campo 'query'
    query = """
    query EntitiesQuery($cursor: String) {
      actor {
        entitySearch(query: \"domain IN ('APM','BROWSER','INFRA','MOBILE','SYNTH','EXT')\") {
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
    }
    """

    entities = []
    cursor = None
    while True:
        variables = {"cursor": cursor} if cursor else {}
        result = await execute_graphql_query(query, variables, session=session)
        if not (result and "data" in result and "actor" in result["data"]):
            break
        search_results = result["data"]["actor"]["entitySearch"]["results"]
        entities.extend(search_results["entities"])
        cursor = search_results.get("nextCursor")
        if not cursor:
            break

    log_info(f"Coletadas {len(entities)} entidades do New Relic")
    return entities

async def get_entity_metrics(entity_guid: str, metrics_list: List[str], period_key: str = "30min", session: Optional[aiohttp.ClientSession] = None) -> Dict:
    """
    Recupera métricas específicas para uma entidade.
    
    Args:
        entity_guid: GUID da entidade
        metrics_list: Lista de métricas desejadas
        period_key: Período de tempo para consulta
        
    Returns:
        Dicionário com os resultados das métricas
    """
    # NÃO usar period_clause nos campos GraphQL! Só em NRQL.
    # O período para GraphQL é definido por default no backend da New Relic (normalmente 30min/1h). Para períodos customizados, use NRQL.
    metric_results = {}
    # Corrigido conforme documentação GraphQL New Relic (2025):
    # Removidos campos inválidos: pageLoadTimeStdDev, pageLoadTimeWithFrustration, pageLoadTimeWithTolerating, pageLoadTimeWithSatisfied,
    # diskFreePercent, memoryFreePercent, responseTimeAverage (SyntheticMonitorSummaryData), durationAverage, locationCount, summary (GenericInfrastructureEntity)
    entity_query = f"""
    {{
      actor {{
        entity(guid: \"{entity_guid}\") {{
          ... on ApmApplicationEntity {{
            name
            domain
            entityType
            applicationId
            apmSummary {{
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
            }}
          }}
          ... on BrowserApplicationEntity {{
            name
            domain
            entityType
            browserSummary {{
              ajaxRequestThroughput
              ajaxResponseTimeAverage
              jsErrorRate
              pageLoadThroughput
              pageLoadTimeAverage
              pageLoadTimeMedian
            }}
          }}
          ... on InfrastructureHostEntity {{
            name
            domain
            entityType
            infrastructureSummary: hostSummary {{
              cpuUtilizationPercent
              diskUsedPercent
              memoryUsedPercent
              networkReceiveRate
              networkTransmitRate
            }}
          }}
          ... on MobileApplicationEntity {{
            name
            domain
            entityType
            mobileSummary {{
              appLaunchCount
              crashCount
              crashRate
              httpErrorRate
              httpRequestCount
              httpRequestRate
              httpResponseTimeAverage
              mobileSessionCount
              networkFailureRate
            }}
          }}
          ... on SyntheticMonitorEntity {{
            name
            domain
            entityType
            monitorId
            monitorType
            monitorSummary {{
              locationsFailing
              successRate
            }}
          }}
          ... on GenericInfrastructureEntity {{
            name
            domain
            entityType
          }}
        }}
      }}
    }}
    """

    result = await execute_graphql_query(entity_query, session=session)

    if result and "data" in result and "actor" in result["data"] and "entity" in result["data"]["actor"]:
        entity = result["data"]["actor"]["entity"]
        domain = entity.get("domain", "UNKNOWN")

        if domain == "APM" and "apmSummary" in entity:
            metric_results = entity["apmSummary"]
        elif domain == "BROWSER" and "browserSummary" in entity:
            metric_results = entity["browserSummary"]
        elif domain == "INFRA" and "infrastructureSummary" in entity:
            metric_results = entity["infrastructureSummary"]
        elif domain == "MOBILE" and "mobileSummary" in entity:
            metric_results = entity["mobileSummary"]
        elif domain == "SYNTH" and "monitorSummary" in entity:
            metric_results = entity["monitorSummary"]

    return metric_results

async def get_entity_advanced_data(entity: Dict, period_key: str = "7d", session: Optional[aiohttp.ClientSession] = None) -> Dict:
    """
    Coleta dados avançados para uma entidade usando NRQL.
    Inclui logs, traces, backtraces, queries SQL, etc.
    
    Args:
        entity: Entidade para coleta (com guid e domain)
        period_key: Período de tempo para consulta
        
    Returns:
        Dicionário com dados avançados
    """
    guid = entity.get("guid")
    domain = entity.get("domain", "UNKNOWN")
    entity_name = entity.get("name", "")
    log_info(f"[DEBUG] Coletando dados avançados para entidade: name={entity_name}, guid={guid}, domain={domain}")
    
    if not guid:
        log_warning(f"Entidade sem GUID, pulando coleta avançada")
        return {}
    
    # Período de tempo para consultas
    period_clause = PERIODOS.get(period_key, "SINCE 30 MINUTES AGO")
    
    # Resultado que será retornado
    advanced_data = {
        "logs": [],
        "errors": [],
        "traces": [],
        "queries": [],
        "distributed_trace": [],
        "relationships": []
    }
    # Tarefas em paralelo para APM
    if domain == "APM":
        tasks = []
        # 1. Query para erros e backtraces
        error_query = f"SELECT * FROM TransactionError WHERE entityGuid = '{guid}' {period_clause} LIMIT 100"
        log_info(f"[DEBUG] period_clause: {period_clause}")
        log_info(f"[DEBUG] NRQL TransactionError: {error_query}")
        tasks.append(execute_nrql_query(error_query, session=session))
        # 2. Query para traces detalhados
        trace_query = f"SELECT * FROM Span WHERE entityGuid = '{guid}' {period_clause} LIMIT 1000"
        log_info(f"[DEBUG] period_clause: {period_clause}")
        log_info(f"[DEBUG] NRQL Span: {trace_query}")
        tasks.append(execute_nrql_query(trace_query, session=session))
        # 3. Query para SQL queries lentas (corrigido: remove databaseCallCount do SELECT, usa sum(databaseCallCount) se necessário)
        # Corrigido: remove FACET query/request.uri e campos não facetáveis
        sql_query = (
            f"SELECT count(*), average(duration), max(duration), sum(databaseCallCount) as totalDatabaseCalls, min(timestamp) "
            f"FROM Transaction WHERE entityGuid = '{guid}' AND databaseCallCount > 0 {period_clause} LIMIT 50"
        )
        log_info(f"[DEBUG] period_clause: {period_clause}")
        log_info(f"[DEBUG] NRQL Transaction (corrigido): {sql_query}")
        tasks.append(execute_nrql_query(sql_query, session=session))
        # 4. Query para tempos de execução por linha de código
        code_execution_query = f"SELECT codeExecutionCount, codeExecutionTime, codeExecutionTimePercentage, method, name, packageName, className, lineNumber, timestamp FROM CodeExecution WHERE entityGuid = '{guid}' {period_clause} LIMIT 200"
        log_info(f"[DEBUG] period_clause: {period_clause}")
        log_info(f"[DEBUG] NRQL CodeExecution: {code_execution_query}")
        tasks.append(execute_nrql_query(code_execution_query, session=session))
        # Executa todas as queries em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Processa os resultados
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                log_warning(f"Erro na coleta avançada de {entity_name}: {str(result)}")
                continue

            if "error" in result:
                log_warning(f"Erro na API para {entity_name}: {result['error']}")
                continue

            if "results" not in result:
                log_warning(f"[DEBUG] Resposta NRQL sem campo 'results' para {entity_name}, query index {i}: {result}")
                continue

            # Adiciona resultados aos dados avançados
            if i == 0:  # Erros e backtraces
                advanced_data["errors"] = result["results"]
            elif i == 1:  # Traces detalhados
                advanced_data["traces"] = result["results"]
            elif i == 2:  # SQL queries
                advanced_data["queries"] = result["results"]
            elif i == 3:  # Execução de código
                advanced_data["code_execution"] = result["results"]
    
    # Coleta dados específicos para servidores de infraestrutura
    elif domain == "INFRA":
        tasks = []
        # 1. Query para logs do servidor
        logs_query = f"SELECT message, hostname, level, timestamp, component, entity.name FROM Log WHERE entityGuid = '{guid}' {period_clause} LIMIT 1000"
        log_info(f"[DEBUG] period_clause: {period_clause}")
        log_info(f"[DEBUG] NRQL Log: {logs_query}")
        tasks.append(execute_nrql_query(logs_query, session=session))
        # 2. Query para métricas de sistema
        system_query = f"SELECT average(cpuSystemPercent), average(cpuUserPercent), average(cpuIOWaitPercent), average(memoryUsedBytes), average(memoryTotalBytes), average(diskUtilizationPercent), average(diskUsedPercent), average(networkReceiveBytes), average(networkTransmitBytes) FROM SystemSample WHERE entityGuid = '{guid}' {period_clause} TIMESERIES"
        log_info(f"[DEBUG] period_clause: {period_clause}")
        log_info(f"[DEBUG] NRQL SystemSample: {system_query}")
        tasks.append(execute_nrql_query(system_query, session=session))
        # 3. Query para dados de processos
        process_query = f"SELECT average(cpuPercent), average(memoryResidentSizeBytes), processDisplayName, commandLine, processId FROM ProcessSample WHERE entityGuid = '{guid}' {period_clause} FACET processDisplayName LIMIT 50"
        log_info(f"[DEBUG] period_clause: {period_clause}")
        log_info(f"[DEBUG] NRQL ProcessSample: {process_query}")
        tasks.append(execute_nrql_query(process_query, session=session))
        # Executa todas as queries em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa os resultados
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Erro na coleta avançada de {entity_name}: {str(result)}")
                continue
                
            if "error" in result:
                logger.warning(f"Erro na API para {entity_name}: {result['error']}")
                continue
                
            if "results" not in result:
                continue
                
            # Adiciona resultados aos dados avançados
            if i == 0:  # Logs
                advanced_data["logs"] = result["results"]
            elif i == 1:  # Métricas de sistema
                advanced_data["system_metrics"] = result["results"]
            elif i == 2:  # Processos
                advanced_data["processes"] = result["results"]
    
    # Coleta dados específicos para aplicações browser
    elif domain == "BROWSER":
        tasks = []
        # 1. Query para erros de JavaScript
        js_error_query = f"SELECT count(*), errorClass, errorMessage, stackTrace, pageUrl, browserTransactionName, userAgentName, userAgentVersion FROM JavaScriptError WHERE entityGuid = '{guid}' {period_clause} FACET errorClass LIMIT 100"
        log_info(f"[DEBUG] period_clause: {period_clause}")
        log_info(f"[DEBUG] NRQL JavaScriptError: {js_error_query}")
        tasks.append(execute_nrql_query(js_error_query, session=session))
        # 2. Query para performance de página
        page_perf_query = f"SELECT count(*), average(duration), max(duration), sum(duration), pageUrl, deviceType, pageViewThroughput FROM PageView WHERE entityGuid = '{guid}' {period_clause} FACET pageUrl LIMIT 50"
        log_info(f"[DEBUG] period_clause: {period_clause}")
        log_info(f"[DEBUG] NRQL PageView: {page_perf_query}")
        tasks.append(execute_nrql_query(page_perf_query, session=session))
        # 3. Query para AJAX requests
        ajax_query = f"SELECT count(*), average(duration), max(duration), pageUrl, browserTransactionName, requestUrl FROM AjaxRequest WHERE entityGuid = '{guid}' {period_clause} FACET requestUrl LIMIT 50"
        log_info(f"[DEBUG] period_clause: {period_clause}")
        log_info(f"[DEBUG] NRQL AjaxRequest: {ajax_query}")
        tasks.append(execute_nrql_query(ajax_query, session=session))
        # Executa todas as queries em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa os resultados
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Erro na coleta avançada de {entity_name}: {str(result)}")
                continue
                
            if "error" in result:
                logger.warning(f"Erro na API para {entity_name}: {result['error']}")
                continue
                
            if "results" not in result:
                continue
                
            # Adiciona resultados aos dados avançados
            if i == 0:  # Erros JS
                advanced_data["js_errors"] = result["results"]
            elif i == 1:  # Performance de página
                advanced_data["page_performance"] = result["results"]
            elif i == 2:  # Ajax
                advanced_data["ajax_requests"] = result["results"]
    
    # Obtém relacionamentos com outras entidades (para qualquer tipo de entidade)
    # Descoberta: buscar apenas __typename para inspecionar estrutura
    relations_query = f"""
    {{
      actor {{
        entity(guid: \"{guid}\") {{
          relatedEntities {{
            __typename
          }}
        }}
      }}
    }}
    """
    # Após a consulta, logar o resultado bruto para análise
    relations_result = await execute_graphql_query(relations_query, session=session)
    if relations_result and "data" in relations_result and "actor" in relations_result["data"] and \
       "entity" in relations_result["data"]["actor"] and "relatedEntities" in relations_result["data"]["actor"]["entity"]:
        advanced_data["relationships"] = relations_result["data"]["actor"]["entity"]["relatedEntities"]
    return advanced_data

async def collect_entity_complete_data(entity: Dict, session: Optional[aiohttp.ClientSession] = None, semaphore: Optional[asyncio.Semaphore] = None) -> Dict:
    """
    Coleta todos os dados possíveis para uma entidade.
    
    Args:
        entity: Entidade a ser processada
        session: ClientSession opcional para reuso
    Returns:
        Entidade enriquecida com todos os dados
    """
    guid = entity.get("guid")
    entity_name = entity.get("name", "Unknown")
    
    if not guid:
        log_warning(f"Entidade sem GUID: {entity_name}, pulando coleta completa")
        return entity
    
    try:
        if semaphore:
            async with semaphore:
                return await _collect_entity_complete_data_inner(entity, session)
        else:
            return await _collect_entity_complete_data_inner(entity, session)
    except Exception as e:
        log_error(f"Erro ao coletar dados completos para {entity_name}: {str(e)}")
        entity["problema"] = f"ERRO_COLETA: {str(e)}"
        return entity

async def _collect_entity_complete_data_inner(entity: Dict, session: Optional[aiohttp.ClientSession]) -> Dict:
    guid = entity.get("guid")
    entity_name = entity.get("name", "Unknown")
    processed_entity = entity.copy()
    processed_entity["metricas"] = {}
    for period_key in PERIODOS.keys():
        metrics = await get_entity_metrics(
            guid,
            ["apdex", "response_time", "error_rate", "throughput"],
            period_key,
            session=session
        )
        processed_entity["metricas"][period_key] = metrics
    advanced_data = await get_entity_advanced_data(entity, "7d", session=session)
    processed_entity["dados_avancados"] = advanced_data
    processed_entity["metricas"]["timestamp"] = datetime.now().isoformat()
    return processed_entity

async def collect_full_data() -> Dict[str, List[Dict]]:
    """
    Coleta completa de dados do New Relic.
    
    Returns:
        Dicionário com entidades por domínio
    """
    try:
        connector = TCPConnector(force_close=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            # 1. Obtém todas as entidades do New Relic
            log_info("Iniciando coleta avançada de dados do New Relic...")
            entities = await get_all_entities(session=session)

            # Estrutura para armazenar resultado (entidades por domínio)
            result = {}
            all_entities = []

            # 2. Para cada entidade, coleta dados completos em lotes para evitar sobrecarga
            total = len(entities)
            log_info(f"Coletando dados completos para {total} entidades...")


            # Limite global de concorrência para evitar sobrecarga
            max_concurrent = 10
            semaphore = asyncio.Semaphore(max_concurrent)
            for i in range(0, total, BATCH_SIZE):
                batch = entities[i:i + BATCH_SIZE]
                # TODO: Futuramente, padronizar todos os logs para usar log_info do utilitário centralizado
                # logger.info pode ser substituído por log_info para unificação completa do logging
                log_info(f"Processando lote {i//BATCH_SIZE + 1}/{(total+BATCH_SIZE-1)//BATCH_SIZE}, "
                         f"{len(batch)} entidades ({i+1}-{min(i+BATCH_SIZE, total)}/{total})")

                batch_tasks = [collect_entity_complete_data(e, session=session, semaphore=semaphore) for e in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                for idx, res in enumerate(batch_results):
                    if isinstance(res, Exception):
                        log_error(f"Erro no processamento de entidade no lote {i//BATCH_SIZE + 1}, índice {idx}: {str(res)}")
                        continue
                    if not isinstance(res, dict):
                        log_warning(f"Resultado inesperado no lote {i//BATCH_SIZE + 1}, índice {idx}: {type(res)}")
                        continue
                    if not res.get("guid"):
                        log_warning(f"Entidade sem GUID no lote {i//BATCH_SIZE + 1}, índice {idx}: {res}")
                        continue
                    if not res.get("domain"):
                        log_warning(f"Entidade sem domínio no lote {i//BATCH_SIZE + 1}, índice {idx}: {res}")
                        continue
                    all_entities.append(res)
                    domain = res.get("domain", "UNKNOWN")
                    if domain not in result:
                        result[domain] = []
                    result[domain].append(res)

            # Adiciona lista completa de entidades ao resultado
            result["entidades"] = all_entities

            # 3. Coleta dados globais do sistema
            global_nrql = """
            SELECT count(*) FROM Transaction SINCE 1 hour ago COMPARE WITH 1 day ago
            """
            global_result = await execute_nrql_query(global_nrql, session=session)
            if global_result and "results" in global_result:
                result["status_global"] = global_result["results"]


            # 4. Coletar logs globais reais via NRQL
            try:
                logs_nrql = "SELECT * FROM Log SINCE 24 HOURS AGO LIMIT 100"
                logs_result = await execute_nrql_query(logs_nrql, session=session)
                logs_sample = logs_result.get("results", [])
                if not logs_sample:
                    log_warning(f"Nenhum log real retornado pela query NRQL: {logs_nrql}")
                result["logs"] = {"sample": logs_sample}
            except Exception as e:
                log_error(f"Erro ao coletar logs reais via NRQL '{logs_nrql}': {e}")
                result["logs"] = {"sample": []}

            # 5. Coletar incidentes reais via NRQL
            try:
                incidents_nrql = "SELECT * FROM NrAiIncident SINCE 24 HOURS AGO LIMIT 100"
                incidents_result = await execute_nrql_query(incidents_nrql, session=session)
                incidents_sample = incidents_result.get("results", [])
                if not incidents_sample:
                    log_warning(f"Nenhum incidente real retornado pela query NRQL: {incidents_nrql}")
                result["incidentes"] = {"sample": incidents_sample}
            except Exception as e:
                log_error(f"Erro ao coletar incidentes reais via NRQL '{incidents_nrql}': {e}")
                result["incidentes"] = {"sample": []}

            # 6. Coletar erros de transação reais via NRQL
            try:
                txerror_nrql = "SELECT * FROM TransactionError SINCE 24 HOURS AGO LIMIT 100"
                txerror_result = await execute_nrql_query(txerror_nrql, session=session)
                txerror_sample = txerror_result.get("results", [])
                if not txerror_sample:
                    log_warning(f"Nenhum TransactionError real retornado pela query NRQL: {txerror_nrql}")
                result["transaction_errors"] = {"sample": txerror_sample}
            except Exception as e:
                log_error(f"Erro ao coletar TransactionError reais via NRQL '{txerror_nrql}': {e}")
                result["transaction_errors"] = {"sample": []}

            # 7. Coletar erros de aplicação reais via NRQL
            try:
                errtrace_nrql = "SELECT * FROM ErrorTrace SINCE 24 HOURS AGO LIMIT 100"
                errtrace_result = await execute_nrql_query(errtrace_nrql, session=session)
                errtrace_sample = errtrace_result.get("results", [])
                if not errtrace_sample:
                    log_warning(f"Nenhum ErrorTrace real retornado pela query NRQL: {errtrace_nrql}")
                result["error_traces"] = {"sample": errtrace_sample}
            except Exception as e:
                log_error(f"Erro ao coletar ErrorTrace reais via NRQL '{errtrace_nrql}': {e}")
                result["error_traces"] = {"sample": []}

            # 8. Dashboards e alertas podem ser mantidos via GraphQL apenas para metadados, não eventos
            result["dashboards"] = {"list": []}
            result["alertas"] = {"policies": []}

            # Adiciona timestamp ao resultado final
            result["timestamp"] = datetime.now().isoformat()
            result["total_entidades"] = len(all_entities)

            # Adiciona estatísticas sobre a coleta
            dominios = {}
            for e in all_entities:
                dominio = e.get("domain", "UNKNOWN")
                dominios[dominio] = dominios.get(dominio, 0) + 1

            result["contagem_por_dominio"] = dominios
            log_info(f"Coleta completa finalizada. {len(all_entities)} entidades processadas.")
            log_info(f"Distribuição por domínio: {dominios}")

            return result
    except Exception as e:
        log_error(f"Erro na coleta completa: {str(e)}")
        return {"erro": str(e), "timestamp": datetime.now().isoformat()}

# Função principal para testar o coletor
async def test_collector():
    """Função para testar o coletor avançado"""
    try:
        log_info("Testando coletor avançado do New Relic...")
        
        # 1. Testa obtenção de entidades
        async with aiohttp.ClientSession() as session:
            entities = await get_all_entities(session=session)
        log_info(f"Obtidas {len(entities)} entidades")
        
        # 2. Testa coleta para uma entidade APM (se existir)
        apm_entity = next((e for e in entities if e.get("domain") == "APM"), None)
        if apm_entity:
            log_info(f"Testando coleta avançada para APM: {apm_entity.get('name')}")
            advanced_data = await get_entity_advanced_data(apm_entity, session=session)
            log_info(f"Dados avançados obtidos: {len(advanced_data.get('errors', []))} erros, "
                      f"{len(advanced_data.get('traces', []))} traces, "
                      f"{len(advanced_data.get('queries', []))} queries")
        
        log_info("Teste do coletor concluído com sucesso")
        return True
    except Exception as e:
        log_error(f"Erro ao testar coletor avançado: {str(e)}")
        return False

if __name__ == "__main__":
    # Configura logging para console e arquivo
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("log.txt", encoding="utf-8")
        ]
    )

    import asyncio
    try:
        asyncio.run(test_collector())
    except asyncio.CancelledError:
        log_warning("Asyncio CancelledError capturada durante shutdown. Ignorando.")
