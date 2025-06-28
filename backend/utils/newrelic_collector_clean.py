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
            
    except Exception as e:
        print(f"❌ Erro na coleta de entidades: {e}")
    
    # Teste 3: Status final
    print("\n--- Status final ---")
    final_health = collector.get_health_status()
    print(f"Status final: {final_health}")

# Funções antigas para compatibilidade (stubs)
async def coletar_contexto_completo():
    """Stub para compatibilidade com código existente"""
    collector = NewRelicCollector(NEW_RELIC_API_KEY, NEW_RELIC_ACCOUNT_ID)
    try:
        entities = await collector.collect_entities()
        return {"entidades": entities}
    except Exception as e:
        logger.error(f"Erro na coleta de contexto: {e}")
        return {"entidades": []}

if __name__ == "__main__":
    asyncio.run(main())
