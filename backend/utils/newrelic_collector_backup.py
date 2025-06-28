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
            total_delay = delay + jitter
            logger.warning(f"Rate limit adaptativo: aguardando {total_delay:.2f}s após {self.consecutive_failures} falhas consecutivas")
            await asyncio.sleep(total_delay)
        
        # Rate limiting básico - mínimo entre requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            await asyncio.sleep(sleep_time)
            
        self.last_request_time = time.time()
        self.request_count += 1
    
    def record_success(self):
        """Registra sucesso - reseta contadores de falha e gerencia circuit breaker"""
        self.consecutive_failures = 0
        
        if self.circuit_state == "HALF_OPEN":
            self.consecutive_successes += 1
            logger.info(f"Circuit breaker HALF_OPEN: {self.consecutive_successes}/{self.success_threshold} sucessos")
            
            if self.consecutive_successes >= self.success_threshold:
                logger.info("Circuit breaker: Transicionando de HALF_OPEN para CLOSED")
                self.circuit_state = "CLOSED"
                self.consecutive_successes = 0
    
    def record_failure(self, is_rate_limit=False):
        """Registra falha - incrementa contadores e gerencia circuit breaker"""
        self.consecutive_failures += 1
        
        if is_rate_limit:
            # Se foi rate limit, aumenta drasticamente o delay
            self.consecutive_failures += 2
            logger.warning(f"Rate limit detectado! Total de falhas consecutivas: {self.consecutive_failures}")
        
        # Circuit breaker: abre o circuito se muitas falhas
        if self.consecutive_failures >= self.max_failures and self.circuit_state == "CLOSED":
            logger.error(f"Circuit breaker: Abrindo circuito após {self.consecutive_failures} falhas consecutivas")
            self.circuit_state = "OPEN"
            self.circuit_opened_at = time.time()
            self.consecutive_successes = 0
        
        # Se estava em HALF_OPEN e falhou, volta para OPEN
        elif self.circuit_state == "HALF_OPEN":
            logger.warning("Circuit breaker: Retornando de HALF_OPEN para OPEN após falha")
            self.circuit_state = "OPEN"
            self.circuit_opened_at = time.time()
            self.consecutive_successes = 0
    
    def get_status(self):
        """Retorna status detalhado do rate controller"""
        return {
            "circuit_state": self.circuit_state,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,            "request_count": self.request_count,
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
    
    async def execute_nrql_query(self, query: str, timeout: int = 120) -> Dict:
        """
        Executa query NRQL com rate limiting inteligente, circuit breaker e retry adaptativo
        """
        max_retries = 5
        
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
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout + 10)) as session:
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
                                
                                # Extrai os resultados
                                actor = data.get("data", {}).get("actor")
                                if not actor:
                                    raise Exception("Resposta sem 'actor'")
                                
                                account = actor.get("account")
                                if not account:
                                    raise Exception("Resposta sem 'account'")
                                
                                nrql_result = account.get("nrql")
                                if not nrql_result:
                                    raise Exception("Resposta sem 'nrql'")
                                
                                results = nrql_result.get("results", [])
                                
                                # Sucesso!
                                self.rate_controller.record_success()
                                self.last_successful_request = datetime.now().isoformat()
                                
                                logger.debug(f"NRQL executado com sucesso. Resultados: {len(results)}")
                                return {"results": results}
                            
                            except json.JSONDecodeError as e:
                                logger.error(f"Erro ao decodificar JSON: {e}")
                                self.rate_controller.record_failure()
                                raise Exception(f"Resposta inválida da API do New Relic: {e}")
                        
                        elif response.status == 429:
                            # Rate limit detectado
                            logger.error(f"Rate limit atingido (429). Headers: {dict(response.headers)}")
                            self.rate_controller.record_failure(is_rate_limit=True)
                            
                            # Busca reset time no header se disponível
                            reset_header = response.headers.get('X-RateLimit-Reset')
                            if reset_header:
                                reset_time = int(reset_header)
                                wait_time = max(reset_time - int(time.time()), 60)  # Mínimo 1 minuto
                                logger.warning(f"Rate limit reset em {wait_time}s")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(min(wait_time, 300))  # Máximo 5 minutos
                                    continue
                            else:
                                # Backoff exponencial padrão para rate limit
                                if attempt < max_retries - 1:
                                    backoff_time = min(60 * (2 ** attempt), 300)  # Máximo 5 minutos
                                    logger.warning(f"Rate limit: aguardando {backoff_time}s (tentativa {attempt + 1})")
                                    await asyncio.sleep(backoff_time)
                                    continue
                        
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

async def buscar_todas_entidades(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    url = "https://api.newrelic.com/graphql"
    headers = {
        "API-Key": NEW_RELIC_API_KEY,
        "Content-Type": "application/json"
    }
    # Filtro explícito de domínios suportados
    filtro_dominios = "domain IN ('APM','BROWSER','INFRA','DB','MOBILE','IOT','SERVERLESS','SYNTH','EXT')"
    query = f'''
    {{
      actor {{
        entitySearch(query: "accountId = {NEW_RELIC_ACCOUNT_ID} AND {filtro_dominios}") {{
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
    }}    '''
    
    data = None
    try:
        logger.info("Buscando todas as entidades do New Relic...")
        async with session.post(url, headers=headers, json={"query": query}, timeout=60) as resp:
            data = await resp.json()
    except Exception as e:
        logger.error(f"Erro na requisição à API do New Relic: {e}")
        return []
    
    if not data or "data" not in data:
        logger.error(f"A resposta não contém o campo 'data'. Resposta completa: {data}")
        return []
        
    try:
        results = data["data"]["actor"]["entitySearch"]["results"]["entities"]
        count = data["data"]["actor"]["entitySearch"]["count"]
        logger.info(f"Total de entidades segundo count: {count}")
        entidades = []
        dominios_encontrados = set()
        for ent in results:
            # Ignora entidades de domínios não suportados
            if ent.get("domain") in DOMINIOS_IGNORADOS:
                continue
            entidade = {
                "guid": ent.get("guid"),
                "name": ent.get("name"),
                "domain": ent.get("domain"),
                "type": ent.get("entityType"),
                "tags": ent.get("tags", []),
                "reporting": ent.get("reporting"),
                "metricas": {}  # Garantindo que todas as entidades tenham um campo de métricas inicializado
            }
            # Validação de campos obrigatórios, mas sendo mais flexível
            if not entidade["guid"]:
                logger.warning(f"Entidade sem GUID encontrada: {entidade}")
                continue
                
            # Se o domínio for nulo, usar "UNKNOWN"
            if not entidade["domain"]:
                entidade["domain"] = "UNKNOWN"
                logger.warning(f"Entidade sem domain, definindo como UNKNOWN: {entidade['name']}")
                
            # Se o nome for nulo, usar o guid
            if not entidade["name"]:
                entidade["name"] = entidade["guid"][-10:]
                logger.warning(f"Entidade sem name, usando parte do GUID: {entidade['name']}")
                
            entidades.append(entidade)
            dominios_encontrados.add(entidade["domain"])
        # Log de domínios encontrados e faltantes
        faltando = set(DOMINIOS_NEWRELIC) - dominios_encontrados
        logger.info(f"Domínios encontrados: {sorted(list(dominios_encontrados))}")
        if faltando:
            logger.warning(f"Domínios do New Relic sem entidades reportando: {sorted(list(faltando))}")
        
        logger.info(f"Total de entidades processadas: {len(entidades)}")
        
        # Contagem por domínio para debug
        dominios = {}
        for ent in entidades:
            domain = ent["domain"]
            if domain not in dominios:
                dominios[domain] = 0
            dominios[domain] += 1
        logger.info(f"Contagem por domínio: {dominios}")
        
        return entidades
    except Exception as e:
        logger.error(f"Erro ao coletar entidades: {e}")
        logger.error(f"Resposta recebida da API: {data}")
        return []

def safe_first(lst, default=None):
    """Retorna o primeiro item da lista ou um valor padrão se a lista estiver vazia ou não for lista."""
    if isinstance(lst, list) and lst:
        return lst[0]
    return default

async def executar_nrql_graphql(session: aiohttp.ClientSession, nrql_query: str, retries: int = 8) -> List[Dict[str, Any]]:
    """
    Executa uma query NRQL com retry/backoff exponencial robusto e rate limiting inteligente.
    """
    await rate_controller.wait_if_needed()
    
    url = "https://api.newrelic.com/graphql"
    headers = {
        "API-Key": NEW_RELIC_API_KEY,
        "Content-Type": "application/json"
    }
    query = f"""
    {{
      actor {{
        account(id: {NEW_RELIC_ACCOUNT_ID}) {{
          nrql(query: \"\"\"{nrql_query}\"\"\") {{
            results
          }}
        }}
      }}
    }}
    """
    
    # Validação básica da query NRQL
    if len(nrql_query) > 4000:
        logger.error(f"Query NRQL excede o tamanho máximo permitido (4 KB): {nrql_query}")
        rate_controller.record_failure()
        return []
    if not nrql_query.strip().lower().startswith("select"):
        logger.error(f"Query NRQL inválida, deve começar com SELECT: {nrql_query}")
        rate_controller.record_failure()
        return []

    logger.debug(f"[NRQL] Executando query: {nrql_query}")

    for attempt in range(retries):
        try:
            # Timeout progressivo: aumenta a cada tentativa
            timeout = aiohttp.ClientTimeout(total=30 + (attempt * 10))
            
            async with session.post(url, headers=headers, json={"query": query}, timeout=timeout) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Erro ao decodificar JSON da resposta: {e} | Response: {response_text[:500]}")
                        rate_controller.record_failure()
                        if attempt < retries - 1:
                            backoff_time = (2 ** attempt) + random.uniform(0, 1)
                            await asyncio.sleep(backoff_time)
                            continue
                        return []
                    
                    if not data:
                        logger.warning(f"NRQL resposta vazia! Query: {nrql_query}")
                        rate_controller.record_failure()
                        if attempt < retries - 1:
                            backoff_time = (2 ** attempt) + random.uniform(0, 1)
                            await asyncio.sleep(backoff_time)
                            continue
                        return []
                    
                    # Verifica se há erros na resposta
                    if "errors" in data:
                        errors = data["errors"]
                        error_msg = str(errors)
                        logger.error(f"Erro GraphQL na query: {error_msg} | Query: {nrql_query}")
                        
                        # Verifica se é rate limit específico
                        if any("TOO_MANY_REQUESTS" in str(err) or "NRDB:1106924" in str(err) for err in errors):
                            logger.warning(f"Rate limit detectado nos erros GraphQL. Tentativa {attempt + 1}/{retries}")
                            rate_controller.record_failure(is_rate_limit=True)
                            if attempt < retries - 1:
                                # Backoff exponencial com jitter para rate limit
                                backoff_time = min((3 ** attempt) + random.uniform(0, 2), 300)
                                logger.info(f"Aguardando {backoff_time:.2f}s antes da próxima tentativa...")
                                await asyncio.sleep(backoff_time)
                                continue
                        else:
                            rate_controller.record_failure()
                            
                        return []
                    
                    # Extrai os resultados
                    actor = data.get("data", {}).get("actor")
                    if not actor:
                        logger.warning(f"NRQL resposta sem 'actor'! Query: {nrql_query}")
                        rate_controller.record_failure()
                        if attempt < retries - 1:
                            backoff_time = (2 ** attempt) + random.uniform(0, 1)
                            await asyncio.sleep(backoff_time)
                            continue
                        return []
                    
                    account = actor.get("account")
                    if not account:
                        logger.warning(f"NRQL resposta sem 'account'! Query: {nrql_query}")
                        rate_controller.record_failure()
                        if attempt < retries - 1:
                            backoff_time = (2 ** attempt) + random.uniform(0, 1)
                            await asyncio.sleep(backoff_time)
                            continue
                        return []
                    
                    nrql_result = account.get("nrql")
                    if not nrql_result:
                        logger.warning(f"NRQL resposta sem 'nrql'! Query: {nrql_query}")
                        rate_controller.record_failure()
                        if attempt < retries - 1:
                            backoff_time = (2 ** attempt) + random.uniform(0, 1)
                            await asyncio.sleep(backoff_time)
                            continue
                        return []
                    
                    results = nrql_result.get("results")
                    if results is None:
                        logger.warning(f"NRQL resposta sem 'results'! Query: {nrql_query}")
                        rate_controller.record_failure()
                        if attempt < retries - 1:
                            backoff_time = (2 ** attempt) + random.uniform(0, 1)
                            await asyncio.sleep(backoff_time)
                            continue
                        return []
                    
                    # Sucesso!
                    rate_controller.record_success()
                    if not results:
                        logger.debug(f"NRQL query sem resultados: {nrql_query}")
                    else:
                        logger.debug(f"NRQL executado com sucesso. Resultados: {len(results)}")
                    
                    return results if results is not None else []
                
                elif response.status == 429:
                    logger.warning(f"Rate limit HTTP 429 detectado. Tentativa {attempt + 1}/{retries}")
                    rate_controller.record_failure(is_rate_limit=True)
                    if attempt < retries - 1:
                        # Backoff exponencial com jitter mais agressivo para 429
                        backoff_time = min((4 ** attempt) + random.uniform(0, 3), 300)
                        logger.info(f"Aguardando {backoff_time:.2f}s após HTTP 429...")
                        await asyncio.sleep(backoff_time)
                        continue
                
                elif response.status in [500, 502, 503, 504]:
                    logger.warning(f"Erro de servidor {response.status}. Tentativa {attempt + 1}/{retries}")
                    rate_controller.record_failure()
                    if attempt < retries - 1:
                        backoff_time = (2 ** attempt) + random.uniform(0, 1)
                        await asyncio.sleep(backoff_time)
                        continue
                
                else:
                    logger.error(f"Erro NRQL GraphQL: {response.status} {response_text[:1000]} | Query: {nrql_query}")
                    rate_controller.record_failure()
                    if attempt < retries - 1:
                        backoff_time = (2 ** attempt) + random.uniform(0, 1)
                        await asyncio.sleep(backoff_time)
                        continue
                    return []
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout na query NRQL. Tentativa {attempt + 1}/{retries} | Query: {nrql_query}")
            rate_controller.record_failure()
            if attempt < retries - 1:
                backoff_time = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(backoff_time)
                continue
        
        except Exception as e:
            logger.error(f"Erro inesperado ao executar NRQL. Tentativa {attempt + 1}/{retries}: {e} | Query: {nrql_query}")
            rate_controller.record_failure()
            if attempt < retries - 1:
                backoff_time = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(backoff_time)
                continue

    logger.error(f"Todas as {retries} tentativas falharam para a query: {nrql_query}")
    return []

async def buscar_alertas_ativos(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    url = "https://api.newrelic.com/graphql"
    headers = {
        "API-Key": NEW_RELIC_API_KEY,
        "Content-Type": "application/json"
    }
    query = f"""
    {{
      actor {{
        account(id: {NEW_RELIC_ACCOUNT_ID}) {{
          alerts {{
            incidentsSearch(criteria: {{states: OPEN}}) {{
              incidents {{
                id
                name
                state
                priority
                createdAt
                policyName
                conditionName
              }}
            }}
          }}
        }}
      }}
    }}
    """
    async with session.post(url, headers=headers, json={"query": query}) as response:
        if response.status == 200:
            try:
                return (
                    (await response.json())["data"]["actor"]["account"]["alerts"]["incidentsSearch"]["incidents"]
                )
            except Exception as e:
                logger.error(f"Erro ao extrair alertas: {e}")
                return []
        else:
            logger.error(f"Erro alertas GraphQL: {response.status} {response.text}")
            return []

def entidade_tem_dados(metricas):
    """
    Verifica se uma entidade tem dados válidos nas métricas coletadas.
    Retorna True se a estrutura de métricas estiver correta e contiver dados reais.
    
    Args:
        metricas: Dicionário com métricas coletadas do New Relic
    """
    if not metricas or not isinstance(metricas, dict):
        return False
        
    # Verifica cada período (30min, 24h, 7d, 30d)
    for periodo, periodo_data in metricas.items():
        if not isinstance(periodo_data, dict):
            continue
            
        # Verifica cada tipo de métrica no período
        for metrica_nome, metrica_valores in periodo_data.items():
            # Ignora valores nulos
            if metrica_valores is None:
                continue
                
            # Se for uma lista de resultados
            if isinstance(metrica_valores, list):
                # Ignora listas vazias
                if not metrica_valores:
                    continue
                
                # Verifica cada item na lista
                for item in metrica_valores:
                    # Se for um dicionário, verifica valores dentro dele
                    if isinstance(item, dict) and item:
                        for val in item.values():
                            # Se encontrou qualquer valor válido
                            if val not in (None, 0, "", []):
                                return True
            
            # Se for um valor direto
            elif metrica_valores not in (None, 0, "", []):
                return True
                
    return False

# Função utilitária para coletar atributos detalhados de erros, queries, logs, traces, etc.
async def coletar_atributos_detalhados(session, guid, periodo_nrql):
    detalhes = {}
    # Coleta backtrace, logs, atributos, queries, traces, etc.
    detalhes["erros_detalhados"] = await executar_nrql_graphql(
        session,
        f"SELECT * FROM TransactionError WHERE entityGuid = '{guid}' {periodo_nrql} LIMIT 10"
    )
    detalhes["traces"] = await executar_nrql_graphql(
        session,
        f"SELECT * FROM TransactionTrace WHERE entityGuid = '{guid}' {periodo_nrql} LIMIT 10"
    )
    detalhes["logs"] = await executar_nrql_graphql(
        session,
        f"SELECT * FROM Log WHERE entityGuid = '{guid}' {periodo_nrql} LIMIT 20"
    )
    detalhes["attributes"] = await executar_nrql_graphql(
        session,
        f"SELECT * FROM Span WHERE entityGuid = '{guid}' {periodo_nrql} LIMIT 20"
    )
    detalhes["queries_sql"] = await executar_nrql_graphql(
        session,
        f"SELECT query, duration, database, host, backtrace FROM DatastoreSample WHERE entityGuid = '{guid}' {periodo_nrql} LIMIT 10"
    )
    # Logging detalhado se todos vierem vazios
    if all(not detalhes[k] for k in ["logs", "queries_sql", "traces", "erros_detalhados"]):
        logger.warning(f"[NRQL] Nenhum dado detalhado encontrado para entidade {guid} no período {periodo_nrql}. Verifique a instrumentação no New Relic.")
    return detalhes

async def coletar_metricas_entidade(entidade, top_n=5):
    guid = entidade.get("guid")
    domain = entidade.get("domain")
    if not guid or not domain:
        registrar_entidade_sem_metricas(entidade, "Sem guid ou domínio")
        return {}
    metricas = {}
    async with aiohttp.ClientSession() as session:
        for periodo_nome, periodo_nrql in PERIODOS.items():
            try:
                # Usa o dicionário NRQL_QUERIES detalhado
                queries = NRQL_QUERIES.get(domain, {})
                metricas[periodo_nome] = {}
                for metrica_nome, nrql_template in queries.items():
                    nrql_query = nrql_template.format(guid=guid, periodo=periodo_nrql)
                    metricas[periodo_nome][metrica_nome] = await executar_nrql_graphql(session, nrql_query)
                # Mantém coleta de detalhes se for APM, BROWSER, DB, INFRA
                if domain in ("APM", "BROWSER", "DB", "INFRA"):
                    metricas[periodo_nome]["detalhes"] = await coletar_atributos_detalhados(session, guid, periodo_nrql)
            except Exception as e:
                registrar_entidade_sem_metricas(entidade, f"Erro ao coletar métricas: {e}")
                metricas[periodo_nome] = {"erro": str(e)}
    # Validação final: garantir que todos os períodos estão presentes
    for periodo in PERIODOS.keys():
        if periodo not in metricas:
            registrar_entidade_sem_metricas(entidade, f"Métricas ausentes para período {periodo}")
            metricas[periodo] = {}
    if not entidade_tem_dados(metricas):
        registrar_entidade_sem_metricas(entidade, "Sem dados válidos para análise")
    else:
        logger.info(f"Métricas coletadas com sucesso para entidade {guid} ({entidade.get('name', 'N/A')}).")
    return metricas

async def buscar_entidades_por_guids(guids: list) -> list:
    """
    Busca entidades específicas pelo GUID usando a API do New Relic.
    """
    if not guids:
        return []
    async with aiohttp.ClientSession() as session:
        entidades = await buscar_todas_entidades(session)
        return [ent for ent in entidades if ent.get("guid") in guids]

async def coletar_metricas_nrql(guid: str, periodo: str, domain: str, top_n: int = 5) -> dict:
    """
    Coleta métricas específicas para um GUID, período e domínio usando NRQL.
    """
    metricas = {}
    periodo_nrql = PERIODOS.get(periodo, PERIODOS["7d"])
    async with aiohttp.ClientSession() as session:
        if domain == "APM":
            metricas = {
                "response_time_max": await executar_nrql_graphql(
                    session,
                    f"SELECT max(duration) FROM Transaction WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "recent_error": await executar_nrql_graphql(
                    session,
                    f"SELECT * FROM TransactionError WHERE entityGuid = '{guid}' {periodo_nrql} LIMIT {top_n}"
                ),
                "apdex": await executar_nrql_graphql(
                    session,
                    f"SELECT apdex(duration, t:0.5) FROM Transaction WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "throughput": await executar_nrql_graphql(
                    session,
                    f"SELECT rate(count(*), 1 minute) FROM Transaction WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
            }
        elif domain == "BROWSER":
            metricas = {
                "largest_contentful_paint": await executar_nrql_graphql(
                    session,
                    f"SELECT average(largestContentfulPaint) FROM PageViewTiming WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "cls": await executar_nrql_graphql(
                    session,
                    f"SELECT average(cumulativeLayoutShift) FROM PageViewTiming WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "fid": await executar_nrql_graphql(
                    session,
                    f"SELECT average(firstInputDelay) FROM PageViewTiming WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "js_errors": await executar_nrql_graphql(
                    session,
                    f"SELECT * FROM JavaScriptError WHERE entityGuid = '{guid}' {periodo_nrql} LIMIT {top_n}"
                ),
            }
        elif domain == "INFRA":
            metricas = {
                "cpu": await executar_nrql_graphql(
                    session,
                    f"SELECT average(cpuPercent) FROM SystemSample WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "memoria": await executar_nrql_graphql(
                    session,
                    f"SELECT average(memoryUsedBytes) FROM SystemSample WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "uptime": await executar_nrql_graphql(
                    session,
                    f"SELECT latest(uptime) FROM SystemSample WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
            }
        elif domain == "DB":
            metricas = {
                "query_count": await executar_nrql_graphql(
                    session,
                    f"SELECT count(*) FROM DatastoreSample WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "query_time_avg": await executar_nrql_graphql(
                    session,
                    f"SELECT average(duration) FROM DatastoreSample WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "connection_count": await executar_nrql_graphql(
                    session,
                    f"SELECT average(connectionCount) FROM DatastoreSample WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "slowest_queries": await executar_nrql_graphql(
                    session,
                    f"SELECT duration, operation, query FROM DatastoreSample WHERE entityGuid = '{guid}' {periodo_nrql} ORDER BY duration DESC LIMIT {top_n}"
                ),
            }
        elif domain == "MOBILE":
            metricas = {
                "crash_rate": await executar_nrql_graphql(
                    session,
                    f"SELECT percentage(count(*), WHERE crashCount > 0) FROM Mobile WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "http_errors": await executar_nrql_graphql(
                    session,
                    f"SELECT count(*) FROM MobileRequestError WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "app_launch_time": await executar_nrql_graphql(
                    session,
                    f"SELECT average(appLaunchTime) FROM Mobile WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "top_crashes": await executar_nrql_graphql(
                    session,
                    f"SELECT * FROM MobileCrash WHERE entityGuid = '{guid}' {periodo_nrql} LIMIT {top_n}"
                ),
            }
        elif domain == "IOT":
            metricas = {
                "message_count": await executar_nrql_graphql(
                    session,
                    f"SELECT count(*) FROM IoTDeviceEvent WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "device_errors": await executar_nrql_graphql(
                    session,
                    f"SELECT count(*) FROM IoTDeviceError WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "device_connected": await executar_nrql_graphql(
                    session,
                    f"SELECT latest(connected) FROM IoTDeviceSample WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "recent_errors": await executar_nrql_graphql(
                    session,
                    f"SELECT * FROM IoTDeviceError WHERE entityGuid = '{guid}' {periodo_nrql} LIMIT {top_n}"
                ),
            }
        elif domain == "SERVERLESS":
            metricas = {
                "invocation_count": await executar_nrql_graphql(
                    session,
                    f"SELECT count(*) FROM ServerlessSample WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "duration_avg": await executar_nrql_graphql(
                    session,
                    f"SELECT average(duration) FROM ServerlessSample WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "error_rate": await executar_nrql_graphql(
                    session,
                    f"SELECT percentage(count(*), WHERE error IS TRUE) FROM ServerlessSample WHERE entityGuid = '{guid}' {periodo_nrql}"
                ),
                "cold_starts": await executar_nrql_graphql(
                    session,
                    f"SELECT count(*) FROM ServerlessSample WHERE entityGuid = '{guid}' AND coldStart = 'true' {periodo_nrql}"
                ),
            }
    return metricas

# Dicionário de queries NRQL detalhadas por domínio (inspirado no projeto antigo)
NRQL_QUERIES = {
    "APM": {
        "throughput": "SELECT rate(count(*), 1 minute) AS rpm FROM Transaction WHERE entityGuid = '{guid}' {periodo}",
        "response_time_avg": "SELECT average(duration) AS avg_duration FROM Transaction WHERE entityGuid = '{guid}' {periodo}",
        "response_time_max": "SELECT max(duration) AS max_duration FROM Transaction WHERE entityGuid = '{guid}' {periodo}",
        "apdex": "SELECT apdex(duration, t:0.5) FROM Transaction WHERE entityGuid = '{guid}' {periodo}",
        "error_rate": "SELECT percentage(count(*), WHERE error IS true) AS error_pct FROM Transaction WHERE entityGuid = '{guid}' {periodo}",
        "top10_slowest": "SELECT name, average(duration) AS avg_duration, max(duration) AS max_duration, count(*) AS qtd FROM Transaction WHERE entityGuid = '{guid}' {periodo} FACET name LIMIT 10 ORDER BY avg_duration DESC",
        "recent_error": "SELECT * FROM TransactionError WHERE entityGuid = '{guid}' {periodo} LIMIT 5",
        "stacktrace": "SELECT error.class, error.message, stack_trace, file, line, function FROM TransactionError WHERE entityGuid = '{guid}' AND error.message IS NOT NULL {periodo} LIMIT 3",
        "logs": "SELECT message, level, timestamp FROM Log WHERE entity.guid = '{guid}' {periodo} LIMIT 5",
        "traces_lentos": "SELECT name, duration, traceId, guid FROM Span WHERE entityGuid = '{guid}' AND duration > 2 {periodo} LIMIT 5"
    },
    "BROWSER": {
        "page_load_time": "SELECT average(duration) AS avg_load FROM PageView WHERE entityGuid = '{guid}' {periodo}",
        "page_views": "SELECT count(*) AS views FROM PageView WHERE entityGuid = '{guid}' {periodo}",
        "largest_contentful_paint": "SELECT average(largestContentfulPaint) AS lcp FROM PageViewTiming WHERE entityGuid = '{guid}' {periodo}",
        "cumulative_layout_shift": "SELECT average(cumulativeLayoutShift) AS cls FROM PageViewTiming WHERE entityGuid = '{guid}' {periodo}",
        "first_input_delay": "SELECT average(firstInputDelay) AS fid FROM PageViewTiming WHERE entityGuid = '{guid}' {periodo}",
        "js_error_rate": "SELECT rate(count(*), 1 minute) AS js_errors FROM JavaScriptError WHERE entityGuid = '{guid}' {periodo}",
        "ajax_errors": "SELECT * FROM AjaxRequest WHERE entityGuid = '{guid}' AND status >= 400 {periodo} LIMIT 5",
        "top10_lcp": "SELECT pageUrl, average(largestContentfulPaint) AS lcp FROM PageViewTiming WHERE entityGuid = '{guid}' {periodo} FACET pageUrl LIMIT 10 ORDER BY lcp DESC"
    },
    "INFRA": {
        "cpu_percent": "SELECT average(cpuPercent) AS cpu FROM SystemSample WHERE entityGuid = '{guid}' {periodo}",
        "mem_percent": "SELECT average(memoryUsedBytes/memoryTotalBytes*100) AS mem FROM SystemSample WHERE entityGuid = '{guid}' {periodo}",
        "disk_percent": "SELECT average(diskUsedBytes/diskTotalBytes*100) AS disk FROM StorageSample WHERE entityGuid = '{guid}' {periodo}",
        "uptime": "SELECT max(uptime) AS uptime FROM SystemSample WHERE entityGuid = '{guid}' {periodo}",
        "network_in": "SELECT average(receiveBytesPerSecond) AS net_in FROM SystemSample WHERE entityGuid = '{guid}' {periodo}",
        "network_out": "SELECT average(transmitBytesPerSecond) AS net_out FROM SystemSample WHERE entityGuid = '{guid}' {periodo}",
        "host_count": "SELECT uniqueCount(hostname) AS hosts FROM SystemSample WHERE entityGuid = '{guid}' {periodo}",
        "logs": "SELECT message, level, timestamp FROM Log WHERE entity.guid = '{guid}' {periodo} LIMIT 5"
    },
    "DB": {
        "query_count": "SELECT count(*) FROM DatastoreSample WHERE entityGuid = '{guid}' {periodo}",
        "query_time_avg": "SELECT average(duration) FROM DatastoreSample WHERE entityGuid = '{guid}' {periodo}",
        "connection_count": "SELECT average(connectionCount) FROM DatastoreSample WHERE entityGuid = '{guid}' {periodo}",
        "slowest_queries": "SELECT duration, operation, query, backtrace FROM DatastoreSample WHERE entityGuid = '{guid}' {periodo} ORDER BY duration DESC LIMIT 10"
    },
    "MOBILE": {
        "crash_rate": "SELECT percentage(count(*), WHERE crashCount > 0) FROM Mobile WHERE entityGuid = '{guid}' {periodo}",
        "http_errors": "SELECT count(*) FROM MobileRequestError WHERE entityGuid = '{guid}' {periodo}",
        "app_launch_time": "SELECT average(appLaunchTime) FROM Mobile WHERE entityGuid = '{guid}' {periodo}",
        "top_crashes": "SELECT * FROM MobileCrash WHERE entityGuid = '{guid}' {periodo} LIMIT 5",
        "swift_backtrace": "SELECT * FROM MobileCrash WHERE entityGuid = '{guid}' AND osName = 'iOS' {periodo} LIMIT 2"
    },
    "IOT": {
        "message_count": "SELECT count(*) FROM IoTDeviceEvent WHERE entityGuid = '{guid}' {periodo}",
        "device_errors": "SELECT count(*) FROM IoTDeviceError WHERE entityGuid = '{guid}' {periodo}",
        "device_connected": "SELECT latest(connected) FROM IoTDeviceSample WHERE entityGuid = '{guid}' {periodo}",
        "recent_errors": "SELECT * FROM IoTDeviceError WHERE entityGuid = '{guid}' {periodo} LIMIT 5"
    },
    "SERVERLESS": {
        "invocation_count": "SELECT count(*) FROM ServerlessSample WHERE entityGuid = '{guid}' {periodo}",
        "duration_avg": "SELECT average(duration) FROM ServerlessSample WHERE entityGuid = '{guid}' {periodo}",
        "error_rate": "SELECT percentage(count(*), WHERE error IS TRUE) FROM ServerlessSample WHERE entityGuid = '{guid}' {periodo}",
        "cold_starts": "SELECT count(*) FROM ServerlessSample WHERE entityGuid = '{guid}' AND coldStart = 'true' {periodo}"
    }
}

async def coletar_contexto_completo(top_n=5):
    """
    Coleta contexto completo com fallback seguro em caso de rate limit massivo.
    """
    contexto = {"apm": [], "browser": [], "infra": [], "db": [], "mobile": [], "iot": [], "serverless": [], "synth": [], "ext": [], "alertas": []}
    
    async with aiohttp.ClientSession() as session:
        try:
            entidades = await buscar_todas_entidades(session)
            if not entidades:
                logger.error("Nenhuma entidade encontrada na coleta do contexto completo!")
                # Fallback: retorna contexto vazio, mas o cache usará o último válido
                return {"apm": [], "browser": [], "infra": [], "db": [], "mobile": [], "iot": [], "serverless": [], "synth": [], "ext": [], "alertas": [], "entidades": []}
            
            # Filtra apenas entidades que estão reportando
            entidades_reportando = [e for e in entidades if e.get("reporting")]
            logger.info(f"Total de entidades reportando: {len(entidades_reportando)} de {len(entidades)}")
            
            # Coleta paralela controlada para evitar rate limit
            tarefas = []
            batch_size = 5  # Processa em lotes menores para evitar sobrecarga
            
            for i in range(0, len(entidades_reportando), batch_size):
                batch = entidades_reportando[i:i+batch_size]
                for ent in batch:
                    tarefas.append(coletar_metricas_entidade(ent, top_n))
                
                # Executa o lote atual
                logger.info(f"Processando lote {i//batch_size + 1} de {len(entidades_reportando)//batch_size + 1} (entidades {i+1}-{min(i+batch_size, len(entidades_reportando))})")
                batch_resultados = await asyncio.gather(*tarefas[-len(batch):], return_exceptions=True)
                
                # Processa resultados do lote
                for ent, metricas in zip(batch, batch_resultados):
                    if isinstance(metricas, Exception):
                        logger.error(f"Erro ao coletar métricas para entidade {ent.get('guid')}: {metricas}")
                        continue
                    
                    # Verifica se a entidade tem dados válidos
                    if not entidade_tem_dados(metricas):
                        logger.warning(f"Entidade {ent.get('guid')} ({ent.get('name', 'N/A')}) sem dados válidos de métricas.")
                        continue
                    
                    domain = ent["domain"]
                    item = {
                        "name": ent["name"],
                        "guid": ent["guid"],
                        "domain": ent["domain"],
                        "type": ent.get("type"),
                        "tags": ent.get("tags", []),
                        "metricas": metricas
                    }
                    
                    # Mapeamento de domínios
                    dominio_map = {
                        "APM": "apm",
                        "BROWSER": "browser",
                        "INFRA": "infra",
                        "DB": "db",
                        "MOBILE": "mobile",
                        "IOT": "iot", 
                        "SERVERLESS": "serverless",
                        "SYNTH": "synth",
                        "EXT": "ext"
                    }
                    dominio_chave = dominio_map.get(domain, "alertas")
                    contexto[dominio_chave].append(item)
                
                # Pequena pausa entre lotes para não sobrecarregar a API
                if i + batch_size < len(entidades_reportando):
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Erro crítico durante coleta do contexto completo: {e}")
            logger.error(traceback.format_exc())
            # Em caso de erro crítico, retorna contexto vazio
            # O sistema de cache deve usar o último cache válido
            return {"apm": [], "browser": [], "infra": [], "db": [], "mobile": [], "iot": [], "serverless": [], "synth": [], "ext": [], "alertas": [], "entidades": []}
    
    # Coleta entidades válidas em formato flat para API
    entidades_validas_flat = []
    for dominio_itens in contexto.values():
        if isinstance(dominio_itens, list):
            entidades_validas_flat.extend(dominio_itens)
    
    # Logging de todas as categorias de entidades
    log_parts = []
    total_entidades = 0
    for dominio, itens in contexto.items():
        if dominio != "entidades" and isinstance(itens, list):
            count = len(itens)
            total_entidades += count
            if count > 0:
                log_parts.append(f"{dominio.upper()}={count}")
    
    if total_entidades > 0:
        logger.info(f"Contexto completo coletado com sucesso: {', '.join(log_parts)} | Total: {total_entidades} entidades")
    else:
        logger.warning("Contexto completo coletado mas NENHUMA entidade possui dados válidos!")
        logger.warning(f"Rate controller - Falhas consecutivas: {rate_controller.consecutive_failures}")
        
        # Se tivemos muitas falhas, sugere usar cache anterior
        if rate_controller.consecutive_failures > 5:
            logger.error("ATENÇÃO: Muitas falhas consecutivas detectadas! Recomenda-se usar último cache válido.")
    
    # Add flat list of valid entities for cache and API
    contexto["entidades"] = entidades_validas_flat
    contexto["metadata"] = {
        "timestamp": datetime.now().isoformat(),
        "total_entidades": total_entidades,
        "rate_limit_failures": rate_controller.consecutive_failures,
        "coleta_bem_sucedida": total_entidades > 0
    }
    
    return contexto

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
    
    async def execute_nrql_query(self, query: str, timeout: int = 120) -> Dict:
        """
        Executa query NRQL com rate limiting inteligente, circuit breaker e retry adaptativo
        """
        max_retries = 5
        
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
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout + 10)) as session:
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
                                
                                # Extrai os resultados
                                actor = data.get("data", {}).get("actor")
                                if not actor:
                                    raise Exception("Resposta sem 'actor'")
                                
                                account = actor.get("account")
                                if not account:
                                    raise Exception("Resposta sem 'account'")
                                
                                nrql_result = account.get("nrql")
                                if not nrql_result:
                                    raise Exception("Resposta sem 'nrql'")
                                
                                results = nrql_result.get("results", [])
                                
                                # Sucesso!
                                self.rate_controller.record_success()
                                self.last_successful_request = datetime.now().isoformat()
                                
                                logger.debug(f"NRQL executado com sucesso. Resultados: {len(results)}")
                                return {"results": results}
                            
                            except json.JSONDecodeError as e:
                                logger.error(f"Erro ao decodificar JSON: {e}")
                                self.rate_controller.record_failure()
                                raise Exception(f"Resposta inválida da API do New Relic: {e}")
                        
                        elif response.status == 429:
                            # Rate limit detectado
                            logger.error(f"Rate limit atingido (429). Headers: {dict(response.headers)}")
                            self.rate_controller.record_failure(is_rate_limit=True)
                            
                            # Busca reset time no header se disponível
                            reset_header = response.headers.get('X-RateLimit-Reset')
                            if reset_header:
                                reset_time = int(reset_header)
                                wait_time = max(reset_time - int(time.time()), 60)  # Mínimo 1 minuto
                                logger.warning(f"Rate limit reset em {wait_time}s")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(min(wait_time, 300))  # Máximo 5 minutos
                                    continue
                            else:
                                # Backoff exponencial padrão para rate limit
                                if attempt < max_retries - 1:
                                    backoff_time = min(60 * (2 ** attempt), 300)  # Máximo 5 minutos
                                    logger.warning(f"Rate limit: aguardando {backoff_time}s (tentativa {attempt + 1})")
                                    await asyncio.sleep(backoff_time)
                                    continue
                        
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
            
    except Exception as e:
        print(f"❌ Erro na coleta de entidades: {e}")
    
    # Teste 3: Status final
    print("\n--- Status final ---")
    final_health = collector.get_health_status()
    print(f"Status final: {final_health}")

if __name__ == "__main__":
    asyncio.run(main())