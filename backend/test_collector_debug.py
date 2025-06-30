#!/usr/bin/env python3
"""
Script para testar e debugar o coletor do New Relic
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona o diretório atual ao path
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

async def test_newrelic_connection():
    """Testa a conexão básica com o New Relic"""
    try:
        from utils.newrelic_collector import NewRelicCollector
        
        api_key = os.getenv('NEW_RELIC_API_KEY')
        account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
        
        logger.info("=== TESTE DE CONEXÃO NEW RELIC ===")
        logger.info(f"API Key presente: {'Sim' if api_key else 'Não'}")
        logger.info(f"Account ID: {account_id}")
        
        if not api_key or not account_id:
            logger.error("Credenciais do New Relic não encontradas!")
            return False
        
        # Cria o coletor
        collector = NewRelicCollector(api_key, account_id)
        
        # Testa coleta de entidades
        logger.info("Coletando entidades...")
        entities = await collector.collect_entities()
        
        logger.info(f"✅ Total de entidades coletadas: {len(entities)}")
        
        if entities:
            # Mostra detalhes das primeiras entidades
            logger.info("=== PRIMEIRAS ENTIDADES ===")
            for i, entity in enumerate(entities[:5]):
                name = entity.get('name', 'N/A')
                domain = entity.get('domain', 'N/A')
                entity_type = entity.get('entityType', 'N/A')
                reporting = entity.get('reporting', 'N/A')
                logger.info(f"{i+1}. {name} ({domain}/{entity_type}) - Reporting: {reporting}")
            
            # Contagem por domínio
            domains = {}
            for entity in entities:
                domain = entity.get('domain', 'UNKNOWN')
                domains[domain] = domains.get(domain, 0) + 1
            
            logger.info("=== DISTRIBUIÇÃO POR DOMÍNIO ===")
            for domain, count in domains.items():
                logger.info(f"{domain}: {count} entidades")
        else:
            logger.warning("❌ Nenhuma entidade encontrada!")
            logger.warning("Possíveis causas:")
            logger.warning("1. Account ID incorreto")
            logger.warning("2. API Key sem permissões")
            logger.warning("3. Nenhuma aplicação instrumentada")
            logger.warning("4. Filtros muito restritivos")
        
        return len(entities) > 0
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_entity_filtering():
    """Testa o filtro de entidades"""
    try:
        from utils.newrelic_collector import NewRelicCollector
        from utils.entity_processor import filter_entities_with_data
        
        api_key = os.getenv('NEW_RELIC_API_KEY')
        account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
        
        if not api_key or not account_id:
            logger.error("Credenciais não encontradas para teste de filtro")
            return False
        
        collector = NewRelicCollector(api_key, account_id)
        
        # Coleta entidades brutas
        logger.info("=== TESTE DE FILTRO DE ENTIDADES ===")
        entities_raw = await collector.collect_entities()
        logger.info(f"Entidades brutas coletadas: {len(entities_raw)}")
        
        # Adiciona métricas a algumas entidades para teste
        for i, entity in enumerate(entities_raw[:3]):
            logger.info(f"Coletando métricas para: {entity.get('name', 'N/A')}")
            try:
                metrics = await collector.collect_entity_metrics(entity)
                entity['metricas'] = metrics
                logger.info(f"Métricas adicionadas: {len(metrics) if metrics else 0} períodos")
            except Exception as e:
                logger.warning(f"Erro ao coletar métricas: {e}")
        
        # Aplica filtro
        logger.info("Aplicando filtro de entidades...")
        entities_filtered = filter_entities_with_data(entities_raw)
        
        logger.info(f"✅ Entidades após filtro: {len(entities_filtered)}")
        logger.info(f"Taxa de aprovação: {len(entities_filtered)/len(entities_raw)*100:.1f}%" if entities_raw else "N/A")
        
        return len(entities_filtered) > 0
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de filtro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Executa todos os testes"""
    logger.info("🚀 INICIANDO DIAGNÓSTICO DO COLETOR NEW RELIC")
    
    # Teste 1: Conexão básica
    success1 = await test_newrelic_connection()
    
    # Teste 2: Filtro de entidades
    success2 = await test_entity_filtering()
    
    logger.info("=== RESUMO DOS TESTES ===")
    logger.info(f"Conexão New Relic: {'✅' if success1 else '❌'}")
    logger.info(f"Filtro de entidades: {'✅' if success2 else '❌'}")
    
    if success1 and success2:
        logger.info("🎉 TODOS OS TESTES PASSARAM!")
    else:
        logger.error("💥 ALGUNS TESTES FALHARAM!")
        logger.error("Verifique as configurações do New Relic e credenciais")

if __name__ == "__main__":
    asyncio.run(main())
