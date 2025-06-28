"""
Módulo de integração para inicializar o sistema de cache avançado na inicialização da aplicação.
Deve ser importado no início do arquivo main.py para garantir que o cache esteja pronto antes
do início da aplicação.
"""

import os
import sys
import logging
import asyncio

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from utils.cache_advanced import inicializar_sistema_cache

# Função que será chamada automaticamente durante a importação
async def _initialize():
    """Inicializa o sistema de cache durante o startup da aplicação"""
    logger.info("Inicializando sistema de cache avançado durante o startup...")
    await inicializar_sistema_cache()

# Cria uma Task para inicializar o cache
# Este código será executado automaticamente quando o módulo for importado
try:
    # Obtém o loop de eventos atual ou cria um novo
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Cria uma Task para inicializar o cache
    if not loop.is_running():
        # Se o loop não estiver em execução, inicializa sincronamente
        logger.info("Loop não está em execução, inicializando cache agora...")
        loop.run_until_complete(_initialize())
    else:
        # Se o loop já estiver em execução, cria uma Task
        logger.info("Loop já em execução, agendando inicialização do cache...")
        asyncio.create_task(_initialize())
        
    logger.info("Sistema de cache agendado para inicialização")
except Exception as e:
    logger.error(f"Erro ao inicializar cache durante a importação: {e}")
    import traceback
    logger.error(traceback.format_exc())
