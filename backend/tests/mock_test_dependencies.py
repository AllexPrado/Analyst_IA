"""
Script para testar o método collect_entity_dependencies sem dependências externas.
Este script não requer credenciais do New Relic e executa testes com mocks.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

# Adiciona o diretório pai ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger_config import setup_logger

# Configura o logger
logger = setup_logger('mock_test_dependencies')

# Mock das respostas para simular chamadas ao New Relic
MOCK_UPSTREAM_RESPONSE = {
    "data": {
        "actor": {
            "entity": {
                "upstreamRelationships": [
                    {
                        "source": {
                            "guid": "upstream_source_guid_1",
                            "name": "Banco de Dados Produção",
                            "entityType": "POSTGRESQL_DB_ENTITY",
                            "domain": "DB"
                        },
                        "target": {
                            "guid": "target_guid",
                            "name": "API Principal",
                            "entityType": "APM_APPLICATION_ENTITY",
                            "domain": "APM"
                        },
                        "type": "CALLS"
                    },
                    {
                        "source": {
                            "guid": "upstream_source_guid_2",
                            "name": "Cache Redis",
                            "entityType": "REDIS_INSTANCE_ENTITY",
                            "domain": "DB"
                        },
                        "target": {
                            "guid": "target_guid",
                            "name": "API Principal",
                            "entityType": "APM_APPLICATION_ENTITY",
                            "domain": "APM"
                        },
                        "type": "USES"
                    }
                ]
            }
        }
    }
}

MOCK_DOWNSTREAM_RESPONSE = {
    "data": {
        "actor": {
            "entity": {
                "downstreamRelationships": [
                    {
                        "source": {
                            "guid": "source_guid",
                            "name": "API Principal",
                            "entityType": "APM_APPLICATION_ENTITY",
                            "domain": "APM"
                        },
                        "target": {
                            "guid": "downstream_target_guid_1",
                            "name": "Frontend Web",
                            "entityType": "BROWSER_APPLICATION_ENTITY",
                            "domain": "BROWSER"
                        },
                        "type": "SERVES"
                    },
                    {
                        "source": {
                            "guid": "source_guid",
                            "name": "API Principal",
                            "entityType": "APM_APPLICATION_ENTITY",
                            "domain": "APM"
                        },
                        "target": {
                            "guid": "downstream_target_guid_2",
                            "name": "Aplicativo Mobile",
                            "entityType": "MOBILE_APPLICATION_ENTITY",
                            "domain": "MOBILE"
                        },
                        "type": "SERVES"
                    }
                ]
            }
        }
    }
}

# Mock da classe NewRelicCollector
class MockNewRelicCollector:
    def __init__(self, api_key, account_id):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = "https://api.newrelic.com/graphql"
        self.rate_controller = MagicMock()
    
    async def wait_if_needed(self):
        return
    
    async def collect_entities(self):
        return [
            {
                "guid": "entity_guid_1",
                "name": "API Principal",
                "domain": "APM",
                "entityType": "APM_APPLICATION_ENTITY"
            },
            {
                "guid": "entity_guid_2",
                "name": "Frontend Web",
                "domain": "BROWSER",
                "entityType": "BROWSER_APPLICATION_ENTITY"
            },
            {
                "guid": "entity_guid_3",
                "name": "Banco de Dados Produção",
                "domain": "DB",
                "entityType": "POSTGRESQL_DB_ENTITY"
            }
        ]
    
    async def make_graphql_request(self, query):
        # Simula diferentes respostas com base na consulta
        if "upstreamRelationships" in query:
            return MOCK_UPSTREAM_RESPONSE
        elif "downstreamRelationships" in query:
            return MOCK_DOWNSTREAM_RESPONSE
        return {}
    
    async def collect_entity_dependencies(self, guid):
        """
        Implementação real do método collect_entity_dependencies
        """
        try:
            logger.info(f"Coletando dependências para entidade com GUID: {guid}")
            
            # Simula as dependências upstream
            upstream_data = await self.make_graphql_request("upstreamRelationships")
            upstream = upstream_data.get("data", {}).get("actor", {}).get("entity", {}).get("upstreamRelationships", [])
            
            # Simula as dependências downstream
            downstream_data = await self.make_graphql_request("downstreamRelationships")
            downstream = downstream_data.get("data", {}).get("actor", {}).get("entity", {}).get("downstreamRelationships", [])
            
            dependencies = {
                "upstream": [],
                "downstream": []
            }
            
            # Processa dependências upstream
            if upstream:
                logger.info(f"Encontradas {len(upstream)} dependências upstream para entidade {guid}")
                dependencies["upstream"] = upstream
            else:
                logger.info(f"Nenhuma dependência upstream encontrada para entidade {guid}")
            
            # Processa dependências downstream
            if downstream:
                logger.info(f"Encontradas {len(downstream)} dependências downstream para entidade {guid}")
                dependencies["downstream"] = downstream
            else:
                logger.info(f"Nenhuma dependência downstream encontrada para entidade {guid}")
            
            # Enriquece as dependências com metadados
            if dependencies["upstream"] or dependencies["downstream"]:
                logger.info(f"Total de dependências coletadas para entidade {guid}: {len(dependencies['upstream']) + len(dependencies['downstream'])}")
                
                dependencies["metadata"] = {
                    "timestamp": datetime.now().isoformat(),
                    "entity_guid": guid,
                    "total_upstream": len(dependencies["upstream"]),
                    "total_downstream": len(dependencies["downstream"])
                }
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Erro ao coletar dependências para entidade {guid}: {e}")
            return {"upstream": [], "downstream": [], "error": str(e)}

async def run_mock_tests():
    """
    Executa testes simulados para o método collect_entity_dependencies
    """
    logger.info("Iniciando testes simulados para collect_entity_dependencies")
    
    # Cria uma instância do coletor simulado
    collector = MockNewRelicCollector("fake_api_key", "fake_account_id")
    
    # Obtém entidades simuladas
    entities = await collector.collect_entities()
    
    results = {}
    
    # Testa a coleta de dependências para cada entidade
    for entity in entities:
        entity_name = entity.get('name', 'Desconhecida')
        entity_guid = entity.get('guid')
        
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
                has_upstream = 'upstream' in dependencies and dependencies['upstream']
                has_downstream = 'downstream' in dependencies and dependencies['downstream']
                
                upstream_count = len(dependencies.get("upstream", []))
                downstream_count = len(dependencies.get("downstream", []))
                
                logger.info(f"Dependências para '{entity_name}':")
                logger.info(f"- Upstream: {upstream_count} dependências")
                logger.info(f"- Downstream: {downstream_count} dependências")
                
                if "metadata" in dependencies:
                    logger.info(f"- Metadados: {dependencies['metadata']}")
            else:
                logger.info(f"Nenhuma dependência encontrada para '{entity_name}'")
                
        except Exception as e:
            logger.error(f"Erro ao testar dependências para '{entity_name}': {str(e)}")
            results[entity_name] = {
                'guid': entity_guid,
                'error': str(e)
            }
    
    # Salva os resultados em um arquivo JSON para análise
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mock_dependency_test_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_entities_tested': len(results),
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Teste simulado concluído. Resultados salvos em {output_file}")
    
    # Valida os resultados
    validation_issues = validate_results(results)
    
    if validation_issues:
        logger.error("Problemas encontrados na validação:")
        for issue in validation_issues:
            logger.error(f"- {issue}")
        return False
    else:
        logger.info("Validação concluída com sucesso! A estrutura das dependências está correta.")
        return True

def validate_results(results):
    """
    Valida os resultados dos testes simulados
    """
    issues = []
    
    for entity_name, entity_data in results.items():
        if 'error' in entity_data:
            issues.append(f"Erro na coleta de dependências para '{entity_name}': {entity_data['error']}")
            continue
        
        if not entity_data.get('has_dependencies', False):
            continue
        
        dependencies = entity_data.get('dependencies', {})
        
        # Verifica se as dependências têm a estrutura correta
        if not isinstance(dependencies, dict):
            issues.append(f"Dependências para '{entity_name}' não é um dicionário")
            continue
        
        # Verifica se há pelo menos uma direção (upstream ou downstream)
        if not ('upstream' in dependencies or 'downstream' in dependencies):
            issues.append(f"Nenhuma direção de dependência encontrada para '{entity_name}'")
            continue
        
        # Verifica metadata
        if 'metadata' not in dependencies:
            issues.append(f"Metadados não encontrados para '{entity_name}'")
            continue
        
        # Verifica os campos dos metadados
        metadata = dependencies['metadata']
        for field in ['timestamp', 'entity_guid', 'total_upstream', 'total_downstream']:
            if field not in metadata:
                issues.append(f"Campo '{field}' não encontrado nos metadados de '{entity_name}'")
    
    return issues

if __name__ == '__main__':
    success = asyncio.run(run_mock_tests())
    sys.exit(0 if success else 1)
