"""
Verificador de dependências para o sistema otimizado do Analyst IA.
Este script verifica se todas as dependências necessárias estão instaladas.
"""

import sys
import importlib
import subprocess
import logging
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Lista de bibliotecas necessárias
REQUIRED_LIBS = [
    # Essenciais
    "aiohttp", "fastapi", "uvicorn", "dotenv", "pydantic",
    
    # Processamento de dados
    "asyncio", "PyPDF2", "json", "datetime", "pathlib"
]

# Bibliotecas opcionais
OPTIONAL_LIBS = [
    # Para visualizações
    "matplotlib", "numpy",
    
    # Para testes
    "pytest"
]

def check_library(lib_name):
    """Verifica se uma biblioteca está instalada."""
    try:
        importlib.import_module(lib_name)
        return True
    except ImportError:
        return False
        
def suggest_pip_install():
    """Sugere comando pip para instalar dependências."""
    requirements_file = Path("requirements_otimizado.txt")
    if requirements_file.exists():
        logger.info("\nPara instalar todas as dependências, execute:")
        logger.info(f"pip install -r {requirements_file}")
    else:
        logger.warning("\nArquivo requirements_otimizado.txt não encontrado.")
        
def main():
    """Função principal de verificação."""
    logger.info("Verificando dependências para o sistema otimizado...")
    
    # Verifica bibliotecas necessárias
    missing_required = []
    for lib in REQUIRED_LIBS:
        lib_name = lib.split(".")[0]  # Remove submodules
        if not check_library(lib_name):
            missing_required.append(lib_name)
    
    # Verifica bibliotecas opcionais
    missing_optional = []
    for lib in OPTIONAL_LIBS:
        lib_name = lib.split(".")[0]  # Remove submodules
        if not check_library(lib_name):
            missing_optional.append(lib_name)
    
    # Resultado
    logger.info("\n" + "="*50)
    logger.info("RESULTADO DA VERIFICAÇÃO DE DEPENDÊNCIAS")
    logger.info("="*50)
    
    if not missing_required:
        logger.info("✅ Todas as bibliotecas necessárias estão instaladas!")
    else:
        logger.warning(f"❌ Bibliotecas necessárias faltando: {', '.join(missing_required)}")
        logger.warning("O sistema pode não funcionar corretamente sem estas bibliotecas.")
    
    if not missing_optional:
        logger.info("✅ Todas as bibliotecas opcionais estão instaladas!")
    else:
        logger.info(f"⚠️ Bibliotecas opcionais faltando: {', '.join(missing_optional)}")
        logger.info("O sistema funcionará com recursos limitados.")
    
    # Sugestão de instalação
    if missing_required or missing_optional:
        suggest_pip_install()
    
    logger.info("\n" + "="*50)
    
    return 0 if not missing_required else 1

if __name__ == "__main__":
    sys.exit(main())
