async def fetch_logs_sample(limit=100):
    """Coleta uma amostra global de logs do New Relic via NRQL."""
    try:
        # NRQL não pode conter chaves externas, apenas texto puro
        nrql = f"SELECT message, hostname, level, timestamp, entity.name, entity.guid FROM Log SINCE 1 day ago LIMIT {limit}"
        result = await execute_nrql_query(nrql)
        logs = result.get("results", [])
        if not logs:
            logger.warning(f"Nenhum log retornado pela query NRQL: {nrql} | Resposta bruta: {result}")
        return logs
    except Exception as e:
        logger.error(f"Erro ao coletar logs globais: {e}")
        return []

async def fetch_incidents_sample(limit=100):
    """Coleta uma amostra global de incidentes do New Relic via GraphQL."""
    try:
        query = f'''
        {{
          actor {{
            account(id: {NEW_RELIC_ACCOUNT_ID}) {{
              incidentsSearch(criteria: {{}}) {{
                results(limit: {limit}) {{
                  entities {{
                    id
                    name
                    state
                    openedAt
                    closedAt
                    policyName
                    conditionName
                  }}
                }}
              }}
            }}
          }}
        }}
        '''
        result = await execute_graphql_query(query)
        results = result.get("data", {}).get("actor", {}).get("account", {}).get("incidentsSearch", {}).get("results", [])
        entities = []
        for r in results:
            entities.extend(r.get("entities", []))
        if not entities:
            logger.warning(f"Nenhum incidente retornado pela query GraphQL. Resposta bruta: {result}")
        return entities
    except Exception as e:
        logger.error(f"Erro ao coletar incidentes globais: {e}")
        return []

async def fetch_dashboards_sample(limit=20):
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
        result = await execute_graphql_query(query)
        entities = result.get("data", {}).get("actor", {}).get("entitySearch", {}).get("results", {}).get("entities", [])
        if not entities:
            logger.warning(f"Nenhum dashboard retornado pela query GraphQL. Resposta bruta: {result}")
        return entities[:limit]
    except Exception as e:
        logger.error(f"Erro ao coletar dashboards globais: {e}")
        return []

async def fetch_alerts_sample(limit=50):
    """Coleta uma amostra de alertas (policies) do New Relic via GraphQL."""
    try:
        query = f'''
        {{
          actor {{
            account(id: {NEW_RELIC_ACCOUNT_ID}) {{
              alerts {{
                policiesSearch(searchCriteria: {{}}) {{
                  policies {{
                    id
                    name
                    incidentPreference
                    createdAt
                    updatedAt
                  }}
                }}
              }}
            }}
          }}
        }}
        '''
        result = await execute_graphql_query(query)
        policies = result.get("data", {}).get("actor", {}).get("account", {}).get("alerts", {}).get("policiesSearch", {}).get("policies", [])
        if not policies:
            logger.warning(f"Nenhuma policy de alerta retornada pela query GraphQL. Resposta bruta: {result}")
        return policies[:limit]
    except Exception as e:
        logger.error(f"Erro ao coletar alertas globais: {e}")
        return []
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
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Configuração básica de logging
logger = logging.getLogger(__name__)

load_dotenv()

NEW_RELIC_API_KEY = os.getenv("NEW_RELIC_API_KEY")
NEW_RELIC_QUERY_KEY = os.getenv("NEW_RELIC_QUERY_KEY")
NEW_RELIC_ACCOUNT_ID = os.getenv("NEW_RELIC_ACCOUNT_ID")

if not NEW_RELIC_API_KEY or not NEW_RELIC_ACCOUNT_ID or not NEW_RELIC_QUERY_KEY:
    logger.critical("NEW_RELIC_API_KEY, NEW_RELIC_QUERY_KEY e NEW_RELIC_ACCOUNT_ID são obrigatórios!")
    raise RuntimeError("NEW_RELIC_API_KEY, NEW_RELIC_QUERY_KEY e NEW_RELIC_ACCOUNT_ID são obrigatórios!")

# Configurações
TIMEOUT = 60.0  # Timeout maior para consultas complexas
MAX_RETRIES = 3
RETRY_DELAY = 5.0  # Aumentado para evitar bloqueio
BATCH_SIZE = 2  # Reduzido para evitar rate limit

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

async def execute_nrql_query(nrql: str, timeout: float = TIMEOUT) -> Dict:
    """
    Executa consulta NRQL e retorna resultados.
    
    Args:
        nrql: Query NRQL para executar
        timeout: Tempo máximo de espera (segundos)
        
    Returns:
        Dicionário com os resultados da consulta
    """
    # Usa GraphQL para executar NRQL
    graphql_query = f'''
    {{
      actor {{
        account(id: {NEW_RELIC_ACCOUNT_ID}) {{
          nrql(query: "{nrql}") {{
            results
            metadata {{
              eventTypes
              facets
              eventCount
            }}
          }}
        }}
      }}
    }}
    '''
    data = {"query": graphql_query}
    try:
        async with aiohttp.ClientSession() as session:
            for attempt in range(MAX_RETRIES):
                try:
                    async with session.post(
                        NR_GRAPHQL_URL,
                        headers=GRAPHQL_HEADERS,
                        json=data,
                        timeout=timeout
                    ) as response:
                        resp_text = await response.text()
                        if response.status == 200:
                            try:
                                result = await response.json()
                                # Extrai resultados NRQL do GraphQL
                                return result.get("data", {}).get("actor", {}).get("account", {}).get("nrql", {})
                            except Exception as e:
                                logger.error(f"Erro ao decodificar JSON NRQL: {e} | Body: {resp_text}")
                                return {"error": f"Erro ao decodificar JSON: {e}", "body": resp_text}
                        else:
                            logger.warning(f"Erro na consulta NRQL (tentativa {attempt+1}/{MAX_RETRIES}): Status {response.status} - {resp_text}")
                            if attempt < MAX_RETRIES - 1:
                                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                            else:
                                return {"error": f"Falha após {MAX_RETRIES} tentativas: {resp_text}", "status": response.status, "body": resp_text}
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout na consulta NRQL (tentativa {attempt+1}/{MAX_RETRIES})")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        return {"error": "Timeout após múltiplas tentativas"}
                except Exception as e:
                    logger.warning(f"Erro inesperado na consulta NRQL (tentativa {attempt+1}/{MAX_RETRIES}): {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        return {"error": f"Erro após múltiplas tentativas: {str(e)}"}
    except Exception as e:
        logger.error(f"Erro crítico ao executar consulta NRQL: {str(e)}")
        return {"error": f"Erro crítico: {str(e)}"}

async def execute_graphql_query(query: str, variables: Optional[Dict] = None, timeout: float = TIMEOUT) -> Dict:
    """
    Executa consulta GraphQL na API do New Relic.
    
    Args:
        query: Query GraphQL
        variables: Variáveis para a query
        timeout: Tempo máximo de espera (segundos)
        
    Returns:
        Dicionário com os resultados da consulta
    """
    data = {
        "query": query
    }
    
    if variables:
        data["variables"] = variables
    
    try:
        async with aiohttp.ClientSession() as session:
            for attempt in range(MAX_RETRIES):
                try:
                    async with session.post(
                        NR_GRAPHQL_URL,
                        headers=GRAPHQL_HEADERS,  # <-- Corrigido
                        json=data,
                        timeout=timeout
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            if "errors" in result:
                                logger.warning(f"Erro GraphQL: {result['errors']}")
                            return result
                        else:
                            error_text = await response.text()
                            logger.warning(f"Erro na consulta GraphQL (tentativa {attempt+1}/{MAX_RETRIES}): "
                                         f"Status {response.status} - {error_text}")
                            
                            if attempt < MAX_RETRIES - 1:
                                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                            else:
                                return {"error": f"Falha após {MAX_RETRIES} tentativas: {error_text}"}
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout na consulta GraphQL (tentativa {attempt+1}/{MAX_RETRIES})")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        return {"error": "Timeout após múltiplas tentativas"}
                except Exception as e:
                    logger.warning(f"Erro inesperado na consulta GraphQL (tentativa {attempt+1}/{MAX_RETRIES}): {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        return {"error": f"Erro após múltiplas tentativas: {str(e)}"}
    except Exception as e:
        logger.error(f"Erro crítico ao executar consulta GraphQL: {str(e)}")
        return {"error": f"Erro crítico: {str(e)}"}

async def get_all_entities() -> List[Dict]:
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
        result = await execute_graphql_query(query, variables)
        if not (result and "data" in result and "actor" in result["data"]):
            break
        search_results = result["data"]["actor"]["entitySearch"]["results"]
        entities.extend(search_results["entities"])
        cursor = search_results.get("nextCursor")
        if not cursor:
            break

    logger.info(f"Coletadas {len(entities)} entidades do New Relic")
    return entities

async def get_entity_metrics(entity_guid: str, metrics_list: List[str], period_key: str = "30min") -> Dict:
    """
    Recupera métricas específicas para uma entidade.
    
    Args:
        entity_guid: GUID da entidade
        metrics_list: Lista de métricas desejadas
        period_key: Período de tempo para consulta
        
    Returns:
        Dicionário com os resultados das métricas
    """
    # Escolhe o período de tempo baseado na chave
    period_clause = PERIODOS.get(period_key, "SINCE 30 MINUTES AGO")
    metric_results = {}
    
    # Métricas específicas por tipo de entidade
    entity_query = f"""
    {{
      actor {{
        entity(guid: "{entity_guid}") {{
          ... on ApmApplicationEntity {{
            name
            domain
            entityType
            applicationId
            apmSummary {{
              apdexScore {period_clause}
              errorRate {period_clause}
              hostCount {period_clause}
              instanceCount {period_clause}
              nonWebResponseTimeAverage {period_clause}
              nonWebThroughput {period_clause}
              responseTimeAverage {period_clause}
              throughput {period_clause}
              webResponseTimeAverage {period_clause}
              webThroughput {period_clause}
            }}
          }}
          ... on BrowserApplicationEntity {{
            name
            domain
            entityType
            browserSummary {{
              ajaxRequestThroughput {period_clause}
              ajaxResponseTimeAverage {period_clause}
              jsErrorRate {period_clause}
              pageLoadThroughput {period_clause}
              pageLoadTimeAverage {period_clause}
              pageLoadTimeMedian {period_clause}
              pageLoadTimeStdDev {period_clause}
              pageLoadTimeWithFrustration {period_clause}
              pageLoadTimeWithTolerating {period_clause}
              pageLoadTimeWithSatisfied {period_clause}
            }}
          }}
          ... on InfrastructureHostEntity {{
            name
            domain
            entityType
            infrastructureSummary: hostSummary {{
              cpuUtilizationPercent {period_clause}
              diskFreePercent {period_clause}
              memoryFreePercent {period_clause}
              networkReceiveRate {period_clause}
              networkTransmitRate {period_clause}
            }}
          }}
          ... on MobileApplicationEntity {{
            name
            domain
            entityType
            mobileSummary {{
              appLaunchCount {period_clause}
              crashCount {period_clause}
              crashRate {period_clause}
              httpErrorRate {period_clause}
              httpRequestCount {period_clause}
              httpRequestRate {period_clause}
              httpResponseTimeAverage {period_clause}
              mobileSessionCount {period_clause}
              networkFailureRate {period_clause}
            }}
          }}
          ... on SyntheticMonitorEntity {{
            name
            domain
            entityType
            monitorId
            monitorType
            monitorSummary {{
              locationsFailing {period_clause}
              successRate {period_clause}
              responseTimeAverage {period_clause}
              durationAverage {period_clause}
              locationCount
            }}
          }}
          ... on GenericInfrastructureEntity {{
            name
            domain
            entityType
            summary {{
              response {{
                jsonV2
              }}
            }}
          }}
        }}
      }}
    }}
    """
    
    result = await execute_graphql_query(entity_query)
    
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

async def get_entity_advanced_data(entity: Dict, period_key: str = "30min") -> Dict:
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
    
    if not guid:
        logger.warning(f"Entidade sem GUID, pulando coleta avançada")
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
        error_query = f"SELECT count(*), error.class, error.message, error.expected, error.exceptionClass, error.exceptionMessage, error.stackTrace, httpResponseCode, request.method, request.uri, request.headers, transactionName FROM TransactionError WHERE entityGuid = '{guid}' {period_clause} LIMIT 100"
        tasks.append(execute_nrql_query(error_query))
        # 2. Query para traces detalhados
        trace_query = f"SELECT * FROM Span WHERE entityGuid = '{guid}' {period_clause} LIMIT 1000"
        tasks.append(execute_nrql_query(trace_query))
        # 3. Query para SQL queries lentas
        sql_query = f"SELECT count(*), average(duration), max(duration), databaseCallCount, query, request.uri, min(timestamp) FROM Transaction WHERE entityGuid = '{guid}' AND databaseCallCount > 0 {period_clause} FACET query LIMIT 50"
        tasks.append(execute_nrql_query(sql_query))
        # 4. Query para tempos de execução por linha de código
        code_execution_query = f"SELECT codeExecutionCount, codeExecutionTime, codeExecutionTimePercentage, method, name, packageName, className, lineNumber, timestamp FROM CodeExecution WHERE entityGuid = '{guid}' {period_clause} LIMIT 200"
        tasks.append(execute_nrql_query(code_execution_query))
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
        tasks.append(execute_nrql_query(logs_query))
        # 2. Query para métricas de sistema
        system_query = f"SELECT average(cpuSystemPercent), average(cpuUserPercent), average(cpuIOWaitPercent), average(memoryUsedBytes), average(memoryTotalBytes), average(diskUtilizationPercent), average(diskUsedPercent), average(networkReceiveBytes), average(networkTransmitBytes) FROM SystemSample WHERE entityGuid = '{guid}' {period_clause} TIMESERIES"
        tasks.append(execute_nrql_query(system_query))
        # 3. Query para dados de processos
        process_query = f"SELECT average(cpuPercent), average(memoryResidentSizeBytes), processDisplayName, commandLine, processId FROM ProcessSample WHERE entityGuid = '{guid}' {period_clause} FACET processDisplayName LIMIT 50"
        tasks.append(execute_nrql_query(process_query))
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
        tasks.append(execute_nrql_query(js_error_query))
        # 2. Query para performance de página
        page_perf_query = f"SELECT count(*), average(duration), max(duration), sum(duration), pageUrl, deviceType, pageViewThroughput FROM PageView WHERE entityGuid = '{guid}' {period_clause} FACET pageUrl LIMIT 50"
        tasks.append(execute_nrql_query(page_perf_query))
        # 3. Query para AJAX requests
        ajax_query = f"SELECT count(*), average(duration), max(duration), pageUrl, browserTransactionName, requestUrl FROM AjaxRequest WHERE entityGuid = '{guid}' {period_clause} FACET requestUrl LIMIT 50"
        tasks.append(execute_nrql_query(ajax_query))
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
    relations_result = await execute_graphql_query(relations_query)
    if relations_result and "data" in relations_result and "actor" in relations_result["data"] and \
       "entity" in relations_result["data"]["actor"] and "relatedEntities" in relations_result["data"]["actor"]["entity"]:
        advanced_data["relationships"] = relations_result["data"]["actor"]["entity"]["relatedEntities"]
    return advanced_data

async def collect_entity_complete_data(entity: Dict) -> Dict:
    """
    Coleta todos os dados possíveis para uma entidade.
    
    Args:
        entity: Entidade a ser processada
        
    Returns:
        Entidade enriquecida com todos os dados
    """
    guid = entity.get("guid")
    entity_name = entity.get("name", "Unknown")
    
    if not guid:
        logger.warning(f"Entidade sem GUID: {entity_name}, pulando coleta completa")
        return entity
    
    try:
        # Cria um clone para trabalhar
        processed_entity = entity.copy()
        
        # Adiciona métricas básicas para todos os períodos
        processed_entity["metricas"] = {}
        
        # Para cada período temporal, obtém métricas
        for period_key in PERIODOS.keys():
            metrics = await get_entity_metrics(
                guid,
                ["apdex", "response_time", "error_rate", "throughput"],
                period_key
            )
            processed_entity["metricas"][period_key] = metrics
        
        # Coleta dados avançados (logs, traces, etc)
        advanced_data = await get_entity_advanced_data(entity, "30min")
        
        # Adiciona dados avançados à entidade
        processed_entity["dados_avancados"] = advanced_data
        
        # Adiciona timestamp da coleta
        processed_entity["metricas"]["timestamp"] = datetime.now().isoformat()
        
        return processed_entity
    except Exception as e:
        logger.error(f"Erro ao coletar dados completos para {entity_name}: {str(e)}")
        entity["problema"] = f"ERRO_COLETA: {str(e)}"
        return entity

async def collect_full_data() -> Dict[str, List[Dict]]:
    """
    Coleta completa de dados do New Relic.
    
    Returns:
        Dicionário com entidades por domínio
    """
    try:
        # 1. Obtém todas as entidades do New Relic
        logger.info("Iniciando coleta avançada de dados do New Relic...")
        entities = await get_all_entities()

        # Estrutura para armazenar resultado (entidades por domínio)
        result = {}
        all_entities = []

        # 2. Para cada entidade, coleta dados completos em lotes para evitar sobrecarga
        total = len(entities)
        logger.info(f"Coletando dados completos para {total} entidades...")

        for i in range(0, total, BATCH_SIZE):
            batch = entities[i:i + BATCH_SIZE]
            logger.info(f"Processando lote {i//BATCH_SIZE + 1}/{(total+BATCH_SIZE-1)//BATCH_SIZE}, "
                        f"{len(batch)} entidades ({i+1}-{min(i+BATCH_SIZE, total)}/{total})")

            # Processa entidades em paralelo (com limite de concorrência)
            batch_tasks = [collect_entity_complete_data(e) for e in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Agrupa resultados por domínio e adiciona à lista completa
            for res in batch_results:
                if isinstance(res, Exception):
                    logger.error(f"Erro no processamento de entidade: {str(res)}")
                    continue

                if not isinstance(res, dict):
                    logger.warning(f"Resultado inesperado: {type(res)}")
                    continue

                # Adiciona à lista completa
                all_entities.append(res)

                # Agrupa por domínio
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
        global_result = await execute_nrql_query(global_nrql)
        if global_result and "results" in global_result:
            result["status_global"] = global_result["results"]

        # 4. Coletar logs globais (amostra)
        if hasattr(globals(), "fetch_logs_sample"):
            try:
                logs_sample = await fetch_logs_sample(limit=100)
                result["logs"] = {"sample": logs_sample}
            except Exception as e:
                logger.warning(f"Erro ao coletar logs globais: {e}")
                result["logs"] = {"sample": []}
        else:
            result["logs"] = {"sample": []}

        # 5. Coletar incidentes globais (se função existir)
        if hasattr(globals(), "fetch_incidents_sample"):
            try:
                incidents_sample = await fetch_incidents_sample(limit=100)
                result["incidentes"] = {"sample": incidents_sample}
            except Exception as e:
                logger.warning(f"Erro ao coletar incidentes globais: {e}")
                result["incidentes"] = {"sample": []}
        else:
            result["incidentes"] = {"sample": []}

        # 6. Coletar dashboards globais (se função existir)
        if hasattr(globals(), "fetch_dashboards_sample"):
            try:
                dashboards_sample = await fetch_dashboards_sample(limit=20)
                result["dashboards"] = {"list": dashboards_sample}
            except Exception as e:
                logger.warning(f"Erro ao coletar dashboards globais: {e}")
                result["dashboards"] = {"list": []}
        else:
            result["dashboards"] = {"list": []}

        # 7. Coletar alertas globais (se função existir)
        if hasattr(globals(), "fetch_alerts_sample"):
            try:
                alerts_sample = await fetch_alerts_sample(limit=50)
                result["alertas"] = {"policies": alerts_sample}
            except Exception as e:
                logger.warning(f"Erro ao coletar alertas globais: {e}")
                result["alertas"] = {"policies": []}
        else:
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
        logger.info(f"Coleta completa finalizada. {len(all_entities)} entidades processadas.")
        logger.info(f"Distribuição por domínio: {dominios}")

        return result
    except Exception as e:
        logger.error(f"Erro na coleta completa: {str(e)}")
        return {"erro": str(e), "timestamp": datetime.now().isoformat()}

# Função principal para testar o coletor
async def test_collector():
    """Função para testar o coletor avançado"""
    try:
        logger.info("Testando coletor avançado do New Relic...")
        
        # 1. Testa obtenção de entidades
        entities = await get_all_entities()
        logger.info(f"Obtidas {len(entities)} entidades")
        
        # 2. Testa coleta para uma entidade APM (se existir)
        apm_entity = next((e for e in entities if e.get("domain") == "APM"), None)
        if apm_entity:
            logger.info(f"Testando coleta avançada para APM: {apm_entity.get('name')}")
            advanced_data = await get_entity_advanced_data(apm_entity)
            logger.info(f"Dados avançados obtidos: {len(advanced_data.get('errors', []))} erros, "
                      f"{len(advanced_data.get('traces', []))} traces, "
                      f"{len(advanced_data.get('queries', []))} queries")
        
        logger.info("Teste do coletor concluído com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao testar coletor avançado: {str(e)}")
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

    # Executa o teste do coletor
    import asyncio
    asyncio.run(test_collector())
