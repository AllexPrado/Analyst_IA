"""
Teste da estrutura do método collect_entity_dependencies sem dependências externas.
"""
import os
import sys
import importlib.util
import logging
import inspect
from datetime import datetime

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dependency_structure_test')

def import_module(file_path, module_name):
    """Importa um módulo Python a partir do caminho do arquivo."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Erro ao importar módulo {module_name}: {str(e)}")
        return None

def test_method_structure():
    """Testa a estrutura do método collect_entity_dependencies."""
    # Importa o módulo NewRelicCollector
    module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              'utils', 'newrelic_collector.py')
    module = import_module(module_path, 'newrelic_collector')
    
    if not module:
        logger.error("Não foi possível importar o módulo NewRelicCollector")
        return False
    
    # Verifica se a classe NewRelicCollector existe
    if not hasattr(module, 'NewRelicCollector'):
        logger.error("Classe NewRelicCollector não encontrada")
        return False
    
    NewRelicCollector = module.NewRelicCollector
    
    # Verifica se o método collect_entity_dependencies existe
    if not hasattr(NewRelicCollector, 'collect_entity_dependencies'):
        logger.error("Método collect_entity_dependencies não encontrado")
        return False
    
    logger.info("Método collect_entity_dependencies existe na classe NewRelicCollector")
    
    # Verifica a assinatura do método
    method = getattr(NewRelicCollector, 'collect_entity_dependencies')
    signature = str(inspect.signature(method))
    
    if signature == '(self, guid)':
        logger.info(f"Assinatura do método está correta: collect_entity_dependencies{signature}")
    else:
        logger.warning(f"Assinatura do método não está conforme esperado: collect_entity_dependencies{signature}")
    
    # Verifica se há docstring
    if method.__doc__:
        logger.info("Método possui docstring ")
    else:
        logger.warning("Método não possui docstring")
    
    # Análise do código do método
    source_code = inspect.getsource(method)
    
    # Verifica características essenciais
    essential_features = [
        ('try/except', 'try:' in source_code and 'except' in source_code),
        ('upstream', 'upstream' in source_code),
        ('downstream', 'downstream' in source_code),
        ('logging', ('logger.info' in source_code) or ('logger.error' in source_code)),
        ('metadata', 'metadata' in source_code),
        ('processamento de erros', 'error' in source_code.lower()),
        ('categorização', ('servicos_externos' in source_code) or ('bancos_dados' in source_code)),
        ('retorno estruturado', 'return dependencies' in source_code)
    ]
    
    all_features_present = True
    for feature_name, is_present in essential_features:
        if not is_present:
            logger.warning(f"Característica '{feature_name}' não encontrada no método")
            all_features_present = False
    
    if all_features_present:
        logger.info("Estrutura do método collect_entity_dependencies está correta!")
        return True
    else:
        logger.warning("Estrutura do método collect_entity_dependencies pode estar incompleta")
        return False

if __name__ == "__main__":
    test_method_structure()
