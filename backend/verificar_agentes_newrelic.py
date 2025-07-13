"""
Script para verificar o status dos agentes New Relic
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Adicionar o diretório pai ao PATH para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.newrelic_collector import NewRelicCollector
from utils.logger_config import setup_logger

# Configurar logger
logger = setup_logger('verificar_agentes_newrelic')

async def verificar_agentes():
    # Carregar variáveis de ambiente
    load_dotenv()
    api_key = os.getenv('NEW_RELIC_API_KEY')
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
    
    if not api_key or not account_id:
        logger.error("Chaves de API New Relic não encontradas no arquivo .env")
        return False
    
    # Inicializar coletor
    try:
        collector = NewRelicCollector(api_key, account_id)
        logger.info("Coletor New Relic inicializado com sucesso")
        
        # Verificar entidades (isso testará a conexão com a API do New Relic)
        logger.info("Verificando entidades monitoradas pelo New Relic...")
        entities = await collector.collect_entities()
        
        if not entities:
            logger.warning("Nenhuma entidade encontrada. Verifique se os agentes estão instalados corretamente.")
            return False
        
        # Contar entidades por domínio
        domains = {}
        for entity in entities:
            domain = entity.get('domain', 'Unknown')
            domains[domain] = domains.get(domain, 0) + 1
        
        logger.info(f"Encontradas {len(entities)} entidades monitoradas pelo New Relic")
        for domain, count in domains.items():
            logger.info(f"  - {domain}: {count} entidades")
        
        # Verificar dependências de uma entidade de exemplo
        if entities:
            sample_entity = entities[0]
            guid = sample_entity.get('guid')
            name = sample_entity.get('name', 'Desconhecido')
            
            logger.info(f"Verificando dependências para entidade de exemplo: {name} (GUID: {guid})")
            dependencies = await collector.collect_entity_dependencies(guid)
            
            upstream_count = 0
            downstream_count = 0
            
            if 'upstream' in dependencies:
                for category, items in dependencies['upstream'].items():
                    if isinstance(items, list):
                        upstream_count += len(items)
            
            if 'downstream' in dependencies:
                for category, items in dependencies['downstream'].items():
                    if isinstance(items, list):
                        downstream_count += len(items)
            
            logger.info(f"Dependências encontradas para {name}:")
            logger.info(f"  - Upstream: {upstream_count}")
            logger.info(f"  - Downstream: {downstream_count}")
            
            # Verificar se há metadados (indicativo de que a coleta foi bem-sucedida)
            if 'metadata' in dependencies:
                logger.info("✅ Coleta de dependências funcionando corretamente")
            else:
                logger.warning("⚠️ Coleta de dependências pode estar incompleta")
        
        logger.info("✅ Agentes New Relic estão funcionando corretamente")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao verificar agentes New Relic: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = asyncio.run(verificar_agentes())
    sys.exit(0 if success else 1)
