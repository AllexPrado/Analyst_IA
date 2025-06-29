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

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

NEW_RELIC_API_KEY = os.getenv("NEW_RELIC_API_KEY")
NEW_RELIC_ACCOUNT_ID = os.getenv("NEW_RELIC_ACCOUNT_ID")

# Configurações de timeout ajustadas para prevenir bloqueios no frontend
# Valor em segundos (30 segundos é um bom equilíbrio entre tempo de espera e prevenção de erros)
DEFAULT_TIMEOUT = 30.0  # Timeout padrão de 30 segundos para requisições HTTP
MAX_RETRIES = 2  # Número máximo de tentativas
RETRY_DELAY = 1.0  # Tempo de espera entre tentativas (segundos)

if not NEW_RELIC_API_KEY or not NEW_RELIC_ACCOUNT_ID:
    logger.critical("NEW_RELIC_API_KEY e NEW_RELIC_ACCOUNT_ID são obrigatórios!")
    raise RuntimeError("NEW_RELIC_API_KEY e NEW_RELIC_ACCOUNT_ID são obrigatórios!")

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
    """
    Coletor principal do New Relic com circuit breaker, rate limiting e fallback
    """
    
    def __init__(self, api_key: str, account_id: str):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = "https://api.newrelic.com/graphql"
        self.rate_controller = RateLimitController()
        self.last_successful_request = None
        
        if not api_key or not account_id:
            raise ValueError("API Key e Account ID são obrigatórios")
    
    async def execute_nrql_query(self, query: str, timeout: int = None) -> Dict:
        """
        Executa query NRQL com rate limiting inteligente, circuit breaker e retry adaptativo
        """
        # Usa o timeout definido globalmente se não for especificado
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
            
        max_retries = MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                # Circuit breaker e rate limiting
                await self.rate_controller.wait_if_needed()
                
                logger.info(f"Executando NRQL query (tentativa {attempt + 1}/{max_retries}): {query[:100]}...")
                
                # Preparar request GraphQL
                headers = {
                    'Api-Key': self.api_key,
                    'Content-Type': 'application/json'
                }
                
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
                
                # Timeout configurado para não bloquear a UI
                conn_timeout = aiohttp.ClientTimeout(
                    total=timeout,
                    sock_connect=min(10.0, timeout/3),  # Tempo máximo para conectar
                    sock_read=min(20.0, timeout/2)      # Tempo máximo para ler dados
                )
                
                async with aiohttp.ClientSession(timeout=conn_timeout) as session:
                    async with session.post(self.base_url, headers=headers, json={"query": graphql_query}) as response:
                        response_text = await response.text()
                        
                        if response.status == 200:
                            try:
                                data = json.loads(response_text)
                                
                                # Verifica se há erros na resposta GraphQL
                                if "errors" in data:
                                    errors = data["errors"]
                                    error_msg = str(errors)
                                    logger.error(f"Erro GraphQL: {error_msg}")
                                    
                                    # Verifica se é rate limit específico
                                    if any("TOO_MANY_REQUESTS" in str(err) or "NRDB:1106924" in str(err) for err in errors):
                                        logger.warning(f"Rate limit detectado nos erros GraphQL. Tentativa {attempt + 1}/{max_retries}")
                                        self.rate_controller.record_failure(is_rate_limit=True)
                                        if attempt < max_retries - 1:
                                            # Backoff exponencial com jitter para rate limit
                                            backoff_time = min((3 ** attempt) + random.uniform(0, 2), 300)
                                            logger.info(f"Aguardando {backoff_time:.2f}s antes da próxima tentativa...")
                                            await asyncio.sleep(backoff_time)
                                            continue
                                    else:
                                        self.rate_controller.record_failure()
                                        
                                    raise Exception(f"Erro GraphQL: {error_msg}")
                                
                                # Verifica se a resposta tem dados válidos
                                results = data.get("data", {}).get("actor", {}).get("account", {}).get("nrql", {}).get("results", [])
                                if results is None:
                                    logger.warning("Resposta GraphQL sem resultados válidos")
                                    self.rate_controller.record_failure()
                                    if attempt < max_retries - 1:
                                        await asyncio.sleep(2 ** attempt)
                                        continue
                                    else:
                                        raise Exception("Resposta GraphQL sem resultados válidos")
                                
                                logger.debug(f"Query executada com sucesso. Resultados: {len(results) if isinstance(results, list) else 'N/A'}")
                                self.rate_controller.record_success()
                                self.last_successful_request = datetime.now().isoformat()
                                
                                return results
                            
                            except json.JSONDecodeError:
                                logger.error(f"Resposta não é um JSON válido: {response_text[:200]}...")
                                self.rate_controller.record_failure()
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(2 ** attempt)
                                    continue
                                else:
                                    raise Exception("Falha ao decodificar resposta JSON")
                        
                        elif response.status == 429:
                            logger.error("Rate limit atingido")
                            self.rate_controller.record_failure(is_rate_limit=True)
                            
                            if attempt < max_retries - 1:
                                # Backoff exponencial com jitter para rate limit
                                backoff_time = min((5 ** attempt) + random.uniform(0, 3), 300)
                                logger.info(f"Rate limit: aguardando {backoff_time:.2f}s antes da próxima tentativa...")
                                await asyncio.sleep(backoff_time)
                                continue
                            else:
                                raise Exception("Rate limit atingido, tentativas esgotadas")
                        
                        elif response.status in [403, 401]:
                            logger.error(f"Erro de autenticação/autorização ({response.status}): {response_text[:500]}")
                            self.rate_controller.record_failure()
                            raise Exception(f"Erro de autenticação New Relic API: {response.status}")
                        
                        elif response.status >= 500:
                            # Erro do servidor - retry com backoff
                            logger.error(f"Erro do servidor New Relic ({response.status}): {response_text[:500]}")
                            self.rate_controller.record_failure()
                            
                            if attempt < max_retries - 1:
                                backoff_time = min(5 * (2 ** attempt), 60)  # Máximo 1 minuto para erros de servidor
                                logger.info(f"Erro de servidor: aguardando {backoff_time}s antes de retry")
                                await asyncio.sleep(backoff_time)
                                continue
                        
                        else:
                            logger.error(f"Erro HTTP não tratado ({response.status}): {response_text[:500]}")
                            self.rate_controller.record_failure()
                            
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)  # Backoff simples
                                continue
            
            except asyncio.TimeoutError:
                logger.error(f"Timeout na query NRQL (tentativa {attempt + 1})")
                self.rate_controller.record_failure()
                if attempt < max_retries - 1:
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                    
            except Exception as e:
                if "Circuit breaker OPEN" in str(e):
                    # Re-raise circuit breaker exceptions
                    raise e
                    
                logger.error(f"Erro inesperado na query NRQL (tentativa {attempt + 1}): {e}")
                self.rate_controller.record_failure()
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
        
        # Todas as tentativas falharam
        logger.error(f"Query NRQL falhou após {max_retries} tentativas: {query[:100]}")
        raise Exception(f"Falha completa na query NRQL após {max_retries} tentativas")
    
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
                        
                        logger.info(f"Coletadas {len(entities)} entidades de {count} total")
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
            
            metrics = {}
            
            # Coleta métricas para cada período temporal
            for period_key, period_query in PERIODOS.items():
                metrics[period_key] = {}
                
                # Estratégia baseada no domínio da entidade
                if domain == 'APM':
                    # Coleta Apdex
                    try:
                        apdex_query = f"SELECT apdexScore as score FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        apdex_result = await self.execute_nrql_query(apdex_query)
                        if apdex_result and isinstance(apdex_result, list) and len(apdex_result) > 0:
                            metrics[period_key]['apdex'] = apdex_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Apdex para {name}: {e}")
                    
                    # Coleta Response Time
                    try:
                        response_time_query = f"SELECT max(duration) as 'max.duration' FROM Transaction WHERE entity.guid = '{guid}' {period_query}"
                        response_time_result = await self.execute_nrql_query(response_time_query)
                        if response_time_result and isinstance(response_time_result, list) and len(response_time_result) > 0:
                            metrics[period_key]['response_time_max'] = response_time_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Response Time para {name}: {e}")
                    
                    # Coleta Error Rate
                    try:
                        error_query = f"SELECT latest(errorRate) as 'error_rate' FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        error_result = await self.execute_nrql_query(error_query)
                        if error_result and isinstance(error_result, list) and len(error_result) > 0:
                            metrics[period_key]['error_rate'] = error_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Error Rate para {name}: {e}")
                    
                    # Coleta erros recentes
                    try:
                        recent_errors_query = f"SELECT count(*), error.message, error.class, httpResponseCode FROM TransactionError WHERE entity.guid = '{guid}' {period_query} LIMIT 10"
                        recent_errors_result = await self.execute_nrql_query(recent_errors_query)
                        if recent_errors_result and isinstance(recent_errors_result, list) and len(recent_errors_result) > 0:
                            metrics[period_key]['recent_error'] = recent_errors_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar erros recentes para {name}: {e}")
                    
                    # Coleta Throughput
                    try:
                        throughput_query = f"SELECT average(newRelic.throughput) as 'avg.qps' FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        throughput_result = await self.execute_nrql_query(throughput_query)
                        if throughput_result and isinstance(throughput_result, list) and len(throughput_result) > 0:
                            metrics[period_key]['throughput'] = throughput_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Throughput para {name}: {e}")
                
                elif domain == 'BROWSER':
                    # Coleta Apdex para Browser
                    try:
                        apdex_query = f"SELECT apdexScore as score FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        apdex_result = await self.execute_nrql_query(apdex_query)
                        if apdex_result and isinstance(apdex_result, list) and len(apdex_result) > 0:
                            metrics[period_key]['apdex'] = apdex_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Apdex para Browser {name}: {e}")
                    
                    # Coleta Page Load Time
                    try:
                        load_time_query = f"SELECT average(pageLoadTime) as 'avg.loadTime' FROM PageView WHERE entity.guid = '{guid}' {period_query}"
                        load_time_result = await self.execute_nrql_query(load_time_query)
                        if load_time_result and isinstance(load_time_result, list) and len(load_time_result) > 0:
                            metrics[period_key]['page_load_time'] = load_time_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Page Load Time para Browser {name}: {e}")
                    
                    # Coleta JavaScript Errors
                    try:
                        js_error_query = f"SELECT count(*) as 'error_count', errorMessage FROM JavaScriptError WHERE entity.guid = '{guid}' {period_query} LIMIT 10"
                        js_error_result = await self.execute_nrql_query(js_error_query)
                        if js_error_result and isinstance(js_error_result, list) and len(js_error_result) > 0:
                            metrics[period_key]['js_errors'] = js_error_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar JavaScript Errors para Browser {name}: {e}")
                    
                elif domain == 'INFRA':
                    # Coleta CPU Usage
                    try:
                        cpu_query = f"SELECT average(cpuPercent) as 'avg.cpu' FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        cpu_result = await self.execute_nrql_query(cpu_query)
                        if cpu_result and isinstance(cpu_result, list) and len(cpu_result) > 0:
                            metrics[period_key]['cpu_usage'] = cpu_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar CPU Usage para {name}: {e}")
                    
                    # Coleta Memory Usage
                    try:
                        memory_query = f"SELECT average(memoryUsedBytes)/average(memoryTotalBytes)*100 as 'memory_percent' FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        memory_result = await self.execute_nrql_query(memory_query)
                        if memory_result and isinstance(memory_result, list) and len(memory_result) > 0:
                            metrics[period_key]['memory_usage'] = memory_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Memory Usage para {name}: {e}")
                    
                    # Coleta Disk Usage
                    try:
                        disk_query = f"SELECT average(diskUsedPercent) as 'disk_percent' FROM Metric WHERE entity.guid = '{guid}' {period_query}"
                        disk_result = await self.execute_nrql_query(disk_query)
                        if disk_result and isinstance(disk_result, list) and len(disk_result) > 0:
                            metrics[period_key]['disk_usage'] = disk_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar Disk Usage para {name}: {e}")
                
                else:
                    # Para outros tipos de entidades, tenta métricas genéricas
                    try:
                        generic_query = f"SELECT * FROM Metric WHERE entity.guid = '{guid}' {period_query} LIMIT 10"
                        generic_result = await self.execute_nrql_query(generic_query)
                        if generic_result and isinstance(generic_result, list) and len(generic_result) > 0:
                            metrics[period_key]['generic'] = generic_result
                    except Exception as e:
                        logger.warning(f"Erro ao coletar métricas genéricas para {name}: {e}")
            
            # Adiciona timestamp da coleta
            metrics['timestamp'] = datetime.now().isoformat()
            
            # Adiciona métricas na entidade
            entity['metricas'] = metrics
            
            # Converte para string JSON para compatibilidade com código existente que espera 'detalhe'
            entity['detalhe'] = json.dumps(metrics)
            
            metrics_count = sum(1 for period in metrics.values() if isinstance(period, dict) 
                               for metric in period.values() if metric)
            
            logger.info(f"Coletadas {metrics_count} métricas para {name}")
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
                else:
                    valid_entities.append(result)
            
            logger.info(f"Coleta concluída: {len(valid_entities)} entidades válidas, {errors} erros")
            
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
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
    
    if not api_key or not account_id:
        logger.error("NEW_RELIC_API_KEY e NEW_RELIC_ACCOUNT_ID devem estar configurados no .env")
        return
    
    collector = NewRelicCollector(api_key=api_key, account_id=account_id)
    
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
    collector = NewRelicCollector(NEW_RELIC_API_KEY, NEW_RELIC_ACCOUNT_ID)
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
