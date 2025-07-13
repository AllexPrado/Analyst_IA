"""
Script para testar a coleta de dependências de entidades no New Relic.
Este script valida a implementação do método collect_entity_dependencies.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Adiciona o diretório pai ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.newrelic_collector import NewRelicCollector
from utils.logger_config import setup_logger

# Configura o logger
logger = setup_logger('test_dependencies')

async def test_dependencies_collection():
    """
    Testa a coleta de dependências para uma entidade específica.
    """
    # Carrega as variáveis de ambiente
    load_dotenv()
    
    # Inicializa o coletor
    api_key = os.getenv('NEW_RELIC_API_KEY')
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
    
    if not api_key or not account_id:
        logger.error("API KEY ou ACCOUNT ID do New Relic não configurados nas variáveis de ambiente")
        return
    
    collector = NewRelicCollector(api_key, [account_id])
    
    # Coleta algumas entidades para teste
    logger.info("Coletando entidades para teste...")
    entities = await collector.collect_entities()
    
    if not entities or len(entities) == 0:
        logger.error("Não foi possível coletar entidades para teste")
        return
    
    # Seleciona algumas entidades para teste (no máximo 3)
    test_entities = entities[:min(3, len(entities))]
    
    results = {}
    
    # Testa a coleta de dependências para cada entidade
    for entity in test_entities:
        entity_name = entity.get('name', 'Desconhecida')
        entity_guid = entity.get('guid')
        
        if not entity_guid:
            logger.warning(f"Entidade sem GUID: {entity_name}")
            continue
        
        logger.info(f"Testando coleta de dependências para '{entity_name}' (GUID: {entity_guid})")
        
        try:
            # Coleta as dependências
            dependencies = await collector.collect_entity_dependencies(entity_guid)
            
            # Registra o resultado
            results[entity_name] = {
                'guid': entity_guid,
                'has_dependencies': dependencies is not None,
                'dependencies': dependencies
            }
            
            # Exibe informações sobre as dependências encontradas
            if dependencies:
                has_upstream = 'upstream' in dependencies
                has_downstream = 'downstream' in dependencies
                
                upstream_count = sum(len(val) for val in dependencies.get('upstream', {}).values()) if has_upstream else 0
                downstream_count = sum(len(val) for val in dependencies.get('downstream', {}).values()) if has_downstream else 0
                
                logger.info(f"Dependências para '{entity_name}':")
                logger.info(f"- Upstream: {upstream_count} dependências")
                logger.info(f"- Downstream: {downstream_count} dependências")
            else:
                logger.info(f"Nenhuma dependência encontrada para '{entity_name}'")
                
        except Exception as e:
            logger.error(f"Erro ao testar dependências para '{entity_name}': {str(e)}")
            results[entity_name] = {
                'guid': entity_guid,
                'error': str(e)
            }
    
    # Salva os resultados em um arquivo JSON para análise
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dependency_test_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_entities_tested': len(results),
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Teste concluído. Resultados salvos em {output_file}")

if __name__ == '__main__':
    asyncio.run(test_dependencies_collection())
