"""
Script para execução completa de testes da coleta de dependências.
Executa a coleta e a validação em sequência.
"""

import asyncio
import os
import sys
import time

# Adiciona o diretório pai ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Agora podemos importar módulos do projeto
from utils.logger_config import setup_logger
from tests.test_dependencies import test_dependencies_collection
from tests.validate_dependencies import validate_test_results

# Configura o logger
logger = setup_logger('run_dependency_validation')

async def run_validation():
    """
    Executa o ciclo completo de teste e validação:
    1. Coleta dependências de algumas entidades
    2. Valida a estrutura das dependências coletadas
    """
    logger.info("Iniciando validação completa da coleta de dependências")
    
    # Passo 1: Coleta dependências
    logger.info("Passo 1: Coletando dependências de entidades de teste...")
    await test_dependencies_collection()
    
    # Passo 2: Valida os resultados
    logger.info("Passo 2: Validando estrutura das dependências coletadas...")
    results_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dependency_test_results.json')
    
    if not os.path.exists(results_file):
        logger.error(f"Arquivo de resultados não encontrado: {results_file}")
        return False
    
    # Pequena pausa para garantir que o arquivo foi salvo completamente
    time.sleep(1)
    
    is_valid = validate_test_results(results_file)
    
    if is_valid:
        logger.info("✅ Validação completa finalizada com sucesso!")
        return True
    else:
        logger.error("❌ Validação completa falhou. Verifique os logs para detalhes.")
        return False

if __name__ == '__main__':
    success = asyncio.run(run_validation())
    sys.exit(0 if success else 1)
