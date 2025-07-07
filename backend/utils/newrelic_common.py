"""
Módulo utilitário central para coletores New Relic.
Responsável por centralizar lógica de controle de rate limit, execução de queries, logging e utilitários comuns.

Este módulo NÃO altera o funcionamento dos coletores existentes. Serve como base para refatoração incremental e padronização futura.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any
import aiohttp
import math

# RateLimitController centralizado
class RateLimitController:
    """
    Controla o número de requisições por janela de tempo para evitar rate limit.
    Pode ser usado como context manager async.
    """
    def __init__(self, max_requests: int, period: float):
        self.max_requests = max_requests
        self.period = period
        self.timestamps = []
        self.lock = asyncio.Lock()

    async def __aenter__(self):
        async with self.lock:
            now = time.monotonic()
            self.timestamps = [t for t in self.timestamps if now - t < self.period]
            if len(self.timestamps) >= self.max_requests:
                sleep_time = self.period - (now - self.timestamps[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            self.timestamps.append(time.monotonic())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Logging utilitário padronizado
logger = logging.getLogger("utils.newrelic_common")

def log_info(msg: str):
    logger.info(msg)

def log_warning(msg: str):
    logger.warning(msg)

def log_error(msg: str):
    logger.error(msg)

# Execução de queries NRQL/GraphQL centralizada
async def execute_nrql_query_common(nrql: str, headers: Dict[str, str], url: str, timeout: float = 60.0, session: Optional[aiohttp.ClientSession] = None, max_retries: int = 3, retry_delay: float = 10.0) -> Dict:
    """
    Executa consulta NRQL com retry, logging e timeout.
    """
    data = {"query": nrql} if url.endswith("/query") else {"query": nrql}
    try:
        # Se a sessão passada estiver fechada, cria uma nova
        if session is not None and getattr(session, 'closed', False):
            log_warning("Sessão aiohttp passada já está fechada. Criando nova sessão.")
            _session = aiohttp.ClientSession()
            close_session = True
        else:
            _session = session or aiohttp.ClientSession()
            close_session = session is None
        try:
            for attempt in range(max_retries):
                try:
                    async with _session.post(url, json=data, headers=headers, timeout=timeout) as response:
                        if response.status == 200:
                            return await response.json()
                        log_warning(f"NRQL query failed with status {response.status}: {response.reason}")
                except asyncio.TimeoutError:
                    delay = retry_delay * math.pow(2, attempt)
                    log_warning(f"Timeout on NRQL query attempt {attempt + 1}, aguardando {delay}s antes de tentar novamente...")
                    await asyncio.sleep(delay)
                except Exception as e:
                    delay = retry_delay * math.pow(2, attempt)
                    log_error(f"Unexpected error on NRQL query attempt {attempt + 1}: {str(e)}. Aguardando {delay}s antes de tentar novamente...")
                    await asyncio.sleep(delay)
            # Se todas as tentativas falharem, retorna erro padronizado
            return {"error": "All attempts failed"}
        finally:
            if close_session:
                try:
                    await _session.close()
                except Exception as e:
                    log_warning(f"Erro ao fechar ClientSession: {e}")
    except Exception as e:
        log_error(f"Critical error executing NRQL query: {str(e)}")
        return {"error": f"Critical error: {str(e)}"}

async def execute_graphql_query_common(query: str, headers: Dict[str, str], url: str, variables: Optional[Dict] = None, timeout: float = 60.0, session: Optional[aiohttp.ClientSession] = None, max_retries: int = 3, retry_delay: float = 10.0) -> Dict:
    """
    Executa consulta GraphQL com retry, logging e timeout.
    """
    data = {"query": query}
    if variables:
        data["variables"] = variables
    try:
        # Se a sessão passada estiver fechada, cria uma nova
        if session is not None and getattr(session, 'closed', False):
            log_warning("Sessão aiohttp passada já está fechada. Criando nova sessão.")
            _session = aiohttp.ClientSession()
            close_session = True
        else:
            _session = session or aiohttp.ClientSession()
            close_session = session is None
        try:
            for attempt in range(max_retries):
                try:
                    async with _session.post(url, json=data, headers=headers, timeout=timeout) as response:
                        if response.status == 200:
                            return await response.json()
                        log_warning(f"GraphQL query failed with status {response.status}: {response.reason}")
                except asyncio.TimeoutError:
                    delay = retry_delay * math.pow(2, attempt)
                    log_warning(f"Timeout on GraphQL query attempt {attempt + 1}, aguardando {delay}s antes de tentar novamente...")
                    await asyncio.sleep(delay)
                except Exception as e:
                    delay = retry_delay * math.pow(2, attempt)
                    log_error(f"Unexpected error on GraphQL query attempt {attempt + 1}: {str(e)}. Aguardando {delay}s antes de tentar novamente...")
                    await asyncio.sleep(delay)
            # Se todas as tentativas falharem, retorna erro padronizado
            return {"error": "All attempts failed"}
        finally:
            if close_session:
                try:
                    await _session.close()
                except Exception as e:
                    log_warning(f"Erro ao fechar ClientSession: {e}")
    except Exception as e:
        log_error(f"Critical error executing GraphQL query: {str(e)}\nQuery sent:\n{query}\nVariables: {variables}")
        return {"error": f"Critical error: {str(e)}", "query": query, "variables": variables}

# Exemplo de interface pública do módulo
__all__ = [
    "RateLimitController",
    "execute_nrql_query_common",
    "execute_graphql_query_common",
    "log_info",
    "log_warning",
    "log_error"
]
