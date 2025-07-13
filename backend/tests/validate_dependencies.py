"""
Script para validar o formato da resposta do método collect_entity_dependencies.
Verifica se a estrutura retornada segue o padrão esperado.
"""

import json
import os
import sys

# Adiciona o diretório pai ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger_config import setup_logger

# Configura o logger
logger = setup_logger('validate_dependencies')

def validate_dependency_structure(dependencies):
    """
    Valida a estrutura de um objeto de dependências.
    
    Args:
        dependencies (dict): O objeto de dependências a ser validado
        
    Returns:
        tuple: (is_valid, issues) onde is_valid é um booleano indicando se a estrutura é válida
               e issues é uma lista de problemas encontrados
    """
    issues = []
    
    if not isinstance(dependencies, dict):
        issues.append(f"Dependências deve ser um dicionário, não {type(dependencies).__name__}")
        return False, issues
    
    # Verifica as direções
    expected_directions = ["upstream", "downstream"]
    found_directions = [d for d in expected_directions if d in dependencies]
    
    if not found_directions:
        issues.append(f"Nenhuma direção de dependência encontrada. Esperado pelo menos uma de: {expected_directions}")
        return False, issues
    
    # Para cada direção encontrada, valida as categorias
    for direction in found_directions:
        if not isinstance(dependencies[direction], dict):
            issues.append(f"Dependências '{direction}' deve ser um dicionário, não {type(dependencies[direction]).__name__}")
            continue
        
        expected_categories = ["servicos_externos", "bancos_dados", "outros"]
        found_categories = [c for c in expected_categories if c in dependencies[direction]]
        
        if not found_categories:
            issues.append(f"Nenhuma categoria de dependência encontrada para '{direction}'. Esperado pelo menos uma de: {expected_categories}")
            continue
        
        # Para cada categoria encontrada, valida os itens
        for category in found_categories:
            if not isinstance(dependencies[direction][category], list):
                issues.append(f"Categoria '{category}' em '{direction}' deve ser uma lista, não {type(dependencies[direction][category]).__name__}")
                continue
            
            # Valida cada item na lista
            for i, item in enumerate(dependencies[direction][category]):
                if not isinstance(item, dict):
                    issues.append(f"Item {i} em '{direction}.{category}' deve ser um dicionário, não {type(item).__name__}")
                    continue
                
                # Valida campos obrigatórios
                required_fields = ["nome", "guid", "tipo"]
                for field in required_fields:
                    if field not in item:
                        issues.append(f"Campo '{field}' não encontrado no item {i} de '{direction}.{category}'")
    
    return len(issues) == 0, issues

def validate_test_results(results_file):
    """
    Valida os resultados de um teste de dependências.
    
    Args:
        results_file (str): Caminho para o arquivo de resultados
        
    Returns:
        bool: True se os resultados são válidos, False caso contrário
    """
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        # Validações básicas
        if 'results' not in test_data:
            logger.error("Campo 'results' não encontrado nos dados de teste")
            return False
        
        results = test_data['results']
        valid_count = 0
        invalid_count = 0
        error_count = 0
        
        for entity_name, entity_data in results.items():
            # Verifica se houve erro na coleta
            if 'error' in entity_data:
                logger.warning(f"Erro na coleta de dependências para '{entity_name}': {entity_data['error']}")
                error_count += 1
                continue
            
            # Verifica se tem dependências
            if not entity_data.get('has_dependencies', False):
                logger.info(f"Entidade '{entity_name}' não possui dependências")
                valid_count += 1
                continue
            
            # Valida a estrutura das dependências
            dependencies = entity_data.get('dependencies')
            is_valid, issues = validate_dependency_structure(dependencies)
            
            if is_valid:
                logger.info(f"Estrutura de dependências válida para '{entity_name}'")
                valid_count += 1
            else:
                logger.error(f"Estrutura de dependências inválida para '{entity_name}':")
                for issue in issues:
                    logger.error(f"- {issue}")
                invalid_count += 1
        
        # Exibe o resumo da validação
        total = valid_count + invalid_count + error_count
        logger.info(f"Validação concluída: {total} entidades analisadas")
        logger.info(f"- {valid_count} estruturas válidas")
        logger.info(f"- {invalid_count} estruturas inválidas")
        logger.info(f"- {error_count} erros de coleta")
        
        return invalid_count == 0
        
    except Exception as e:
        logger.error(f"Erro ao validar resultados: {str(e)}")
        return False

if __name__ == '__main__':
    # Localiza o arquivo de resultados mais recente
    test_dir = os.path.dirname(os.path.abspath(__file__))
    results_file = os.path.join(test_dir, 'dependency_test_results.json')
    
    if not os.path.exists(results_file):
        logger.error(f"Arquivo de resultados não encontrado: {results_file}")
        logger.error("Execute o script test_dependencies.py primeiro para gerar os resultados")
        sys.exit(1)
    
    # Valida os resultados
    is_valid = validate_test_results(results_file)
    
    if is_valid:
        logger.info("Validação concluída com sucesso!")
        sys.exit(0)
    else:
        logger.error("Validação falhou. Verifique os erros reportados.")
        sys.exit(1)
