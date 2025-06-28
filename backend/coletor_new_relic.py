"""
Módulo de coleta de dados do New Relic.
Este arquivo serve como ponte para utilizar as funções do módulo utils/newrelic_collector.py.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar funções do coletor real
from utils.newrelic_collector import coletar_contexto_completo, NewRelicCollector

async def coletar_entidades(api_key: str, account_id: str) -> List[Dict[str, Any]]:
    """
    Coleta todas as entidades do New Relic.
    
    Args:
        api_key: API Key do New Relic
        account_id: ID da conta do New Relic
        
    Returns:
        Lista de entidades encontradas no New Relic
    """
    try:
        logger.info(f"Iniciando coleta de entidades do New Relic (Account ID: {account_id})")
        
        # Usa o novo coletor
        collector = NewRelicCollector(api_key, account_id)
        entidades = await collector.collect_entities()
            
        if entidades:
            logger.info(f"Coletadas {len(entidades)} entidades do New Relic")
        else:
            logger.warning("Nenhuma entidade foi coletada do New Relic")
                
        return entidades
    except Exception as e:
        logger.error(f"Erro ao coletar entidades do New Relic: {e}")
        return []

async def coletar_alertas(api_key: str, account_id: str) -> List[Dict[str, Any]]:
    """
    Coleta alertas ativos do New Relic.
    
    Args:
        api_key: API Key do New Relic
        account_id: ID da conta do New Relic
        
    Returns:
        Lista de alertas ativos encontrados no New Relic
    """
    try:
        logger.info(f"Iniciando coleta de alertas do New Relic (Account ID: {account_id})")
        
        # Usa o contexto completo que já inclui alertas
        contexto = await coletar_contexto_completo()
        alertas = contexto.get('alertas', [])
            
        if alertas:
            logger.info(f"Coletados {len(alertas)} alertas ativos do New Relic")
        else:
            logger.warning("Nenhum alerta ativo foi coletado do New Relic")
                
        return alertas
    except Exception as e:
        logger.error(f"Erro ao coletar alertas do New Relic: {e}")
        return []

# Função para teste direto deste módulo
async def teste_coleta():
    """Teste de coleta de entidades e alertas"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("NEW_RELIC_API_KEY")
    account_id = os.getenv("NEW_RELIC_ACCOUNT_ID")
    
    if not api_key or not account_id:
        logger.error("NEW_RELIC_API_KEY e NEW_RELIC_ACCOUNT_ID não estão configurados")
        return
        
    entidades = await coletar_entidades(api_key, account_id)
    logger.info(f"Teste finalizado: {len(entidades)} entidades encontradas")
    
    # Mostrar alguns detalhes das primeiras entidades
    for i, entidade in enumerate(entidades[:5]):
        logger.info(f"Entidade {i+1}: {entidade.get('name')} ({entidade.get('domain')})")

if __name__ == "__main__":
    asyncio.run(teste_coleta())
