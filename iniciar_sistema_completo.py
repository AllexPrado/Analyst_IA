#!/usr/bin/env python3
"""
Script para corrigir e iniciar o sistema Analyst-IA
Este script aplica todas as correções necessárias e inicia o sistema
"""

import os
import sys
import subprocess
import platform
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_script(script_path, description):
    """Executa um script Python"""
    logger.info(f"Executando: {description}")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"✓ {description} concluído com sucesso")
            return True
        else:
            logger.error(f"✗ {description} falhou com código {result.returncode}")
            logger.error(f"Erro: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"✗ {description} falhou: {e}")
        return False

def check_backend_files():
    """Verifica se os arquivos essenciais do backend existem"""
    files_to_check = [
        "backend/unified_backend.py",
        "backend/utils/openai_connector.py",
        "backend/utils/newrelic_collector.py",
        "backend/utils/entity_processor.py",
        "backend/utils/cache.py"
    ]
    
    missing_files = []
    for file_path in files_to_check:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error("✗ Arquivos essenciais ausentes:")
        for file_path in missing_files:
            logger.error(f"  - {file_path}")
        return False
    
    logger.info("✓ Todos os arquivos essenciais do backend estão presentes")
    return True

def check_frontend_files():
    """Verifica se os arquivos essenciais do frontend existem"""
    files_to_check = [
        "frontend/package.json",
        "frontend/vite.config.js",
        "frontend/index.html"
    ]
    
    missing_files = []
    for file_path in files_to_check:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error("✗ Arquivos essenciais ausentes:")
        for file_path in missing_files:
            logger.error(f"  - {file_path}")
        return False
    
    logger.info("✓ Todos os arquivos essenciais do frontend estão presentes")
    return True

def has_node_npm():
    """Verifica se Node.js e npm estão instalados"""
    try:
        subprocess.run(
            ["node", "--version"],
            capture_output=True,
            check=True
        )
        
        subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            check=True
        )
        
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    """Função principal"""
    logger.info("=== Inicializando Correção e Inicialização do Analyst-IA ===")
    
    # 1. Verificar arquivos essenciais
    logger.info("\n1. Verificando arquivos essenciais...")
    backend_ok = check_backend_files()
    frontend_ok = check_frontend_files()
    
    if not backend_ok or not frontend_ok:
        logger.error("Arquivos essenciais ausentes. Abortando inicialização.")
        return 1
    
    # 2. Aplicar correções específicas
    logger.info("\n2. Aplicando correções específicas...")
    if not run_script("corrigir_backend.py", "Correção do backend"):
        logger.warning("Algumas correções do backend podem ter falhado, continuando mesmo assim.")
    
    # 3. Verificar dependências
    logger.info("\n3. Verificando dependências...")
    if not run_script("instalar_dependencias.py", "Instalação de dependências do Python"):
        logger.error("Falha ao instalar dependências do Python")
        return 1
    
    # 4. Verificar Node.js e npm
    logger.info("\n4. Verificando Node.js e npm...")
    if has_node_npm():
        logger.info("✓ Node.js e npm encontrados")
    else:
        logger.error("✗ Node.js ou npm não encontrados")
        logger.info("Executando script de verificação de Node.js...")
        run_script("verificar_node.py", "Verificação de Node.js")
        logger.error("Por favor, instale Node.js e execute este script novamente")
        return 1
    
    # 5. Reiniciar o sistema
    logger.info("\n5. Reiniciando o sistema...")
    if not run_script("reiniciar_sistema.py", "Reinicialização do sistema"):
        logger.error("Falha ao reiniciar o sistema")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
