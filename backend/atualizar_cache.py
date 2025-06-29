import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona um console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

async def forcar_atualizacao_cache():
    """
    Força atualização do cache e garantindo que as métricas sejam coletadas
    """
    logger.info("Forçando atualização do cache...")
    
    try:
        # Importa módulos necessários
        from utils.cache import atualizar_cache_completo, salvar_cache_no_disco
        from utils.newrelic_collector import coletar_contexto_completo
        
        # Força a atualização do cache
        logger.info("Iniciando atualização completa do cache com novas funcionalidades...")
        resultado = await atualizar_cache_completo(coletar_contexto_completo)
        
        if resultado:
            logger.info("Atualização de cache concluída com sucesso!")
            return True
        else:
            logger.error("Falha ao atualizar o cache")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao forçar atualização do cache: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Iniciando script de atualização forçada do cache...")
    resultado = asyncio.run(forcar_atualizacao_cache())
    
    if resultado:
        logger.info("✅ Cache atualizado com sucesso!")
    else:
        logger.error("❌ Falha na atualização do cache")
