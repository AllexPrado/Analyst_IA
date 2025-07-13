"""
Teste específico para a funcionalidade de coleta de dependências do New Relic Collector.
"""
import os
import sys
import asyncio
import logging
import json
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao PATH
sys.path.append(str(Path(__file__).parent))

# Importações do sistema
from utils.newrelic_collector import NewRelicCollector

# Obter credenciais do ambiente ou usar valores padrão para testes
NEW_RELIC_API_KEY = os.environ.get('NEW_RELIC_API_KEY', 'NRAK-J49R10YS4W1FUDESPRVYGRH2ADR')
NEW_RELIC_ACCOUNT_ID = os.environ.get('NEW_RELIC_ACCOUNT_ID', '3882820')

async def test_dependency_collector():
    """
    Testa a coleta de dependências de uma entidade.
    """
    logger.info("Iniciando teste de coleta de dependências...")
    
    try:
        # Inicializar o coletor
        collector = NewRelicCollector(
            api_key=NEW_RELIC_API_KEY,
            account_id=NEW_RELIC_ACCOUNT_ID,
            query_key=NEW_RELIC_API_KEY
        )
        
        logger.info("Coletor do New Relic inicializado")
        
        # Primeiro, precisamos obter pelo menos uma entidade para teste
        logger.info("Coletando lista de entidades...")
        entities = await collector.collect_entities()
        
        if not entities:
            logger.warning("Nenhuma entidade encontrada para teste")
            return
            
        logger.info(f"Encontradas {len(entities)} entidades")
        
        # Selecionar a primeira entidade APM para teste, ou qualquer outra se não houver APM
        test_entity = next((e for e in entities if e.get('domain') == 'APM'), entities[0])
        
        logger.info(f"Entidade selecionada para teste: {test_entity.get('name')} (GUID: {test_entity.get('guid')})")
        
        # Testar coleta de dependências
        guid = test_entity.get('guid')
        logger.info(f"Coletando dependências para GUID: {guid}")
        
        dependencies = await collector.collect_entity_dependencies(guid)
        
        # Mostrar resultado
        logger.info(f"Dependências upstream encontradas: {len(dependencies.get('upstream', []))}")
        logger.info(f"Dependências downstream encontradas: {len(dependencies.get('downstream', []))}")
        
        # Formatando saída JSON para melhor visualização
        logger.info("Amostra do resultado (até 2 dependências de cada):")
        upstream_sample = dependencies.get('upstream', [])[:2]
        downstream_sample = dependencies.get('downstream', [])[:2]
        
        result_sample = {
            "upstream_sample": upstream_sample,
            "downstream_sample": downstream_sample
        }
        
        logger.info(json.dumps(result_sample, indent=2))
        
        logger.info("✅ Teste de coleta de dependências concluído com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_dependency_collector())
