"""
Script para instalar dependências faltantes do Analyst_IA.
"""

import subprocess
import sys
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_package(package_name):
    """
    Verifica se um pacote está instalado.
    
    Args:
        package_name (str): Nome do pacote
        
    Returns:
        bool: True se instalado, False caso contrário
    """
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def install_package(package_name):
    """
    Instala um pacote usando pip.
    
    Args:
        package_name (str): Nome do pacote
        
    Returns:
        bool: True se instalado com sucesso, False caso contrário
    """
    try:
        logger.info(f"Instalando {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logger.info(f"{package_name} instalado com sucesso!")
        return True
    except subprocess.CalledProcessError:
        logger.error(f"Erro ao instalar {package_name}")
        return False

def install_missing_dependencies():
    """
    Instala todas as dependências faltantes necessárias.
    
    Returns:
        dict: Resultado da instalação
    """
    dependencies = {
        # Básicos
        "fastapi": "fastapi>=0.68.0",
        "uvicorn": "uvicorn[standard]>=0.15.0",
        "markdown": "markdown>=3.3.4",
        "openai": "openai>=0.27.0",
        "aiohttp": "aiohttp>=3.8.0",
        
        # Processamento de dados
        "pandas": "pandas>=1.3.0",
        "numpy": "numpy>=1.20.0",
        
        # Azure
        "azure.identity": "azure-identity>=1.10.0",
        "azure.mgmt.compute": "azure-mgmt-compute>=26.0.0",
        
        # Ferramentas úteis
        "pydantic": "pydantic>=1.8.0",
        "python-dotenv": "python-dotenv>=0.19.0",
        "requests": "requests>=2.26.0",
    }
    
    results = {}
    
    for package_name, package_spec in dependencies.items():
        try:
            if check_package(package_name):
                logger.info(f"{package_name} já está instalado")
                results[package_name] = "already_installed"
            else:
                success = install_package(package_spec)
                results[package_name] = "installed" if success else "failed"
        except Exception as e:
            logger.error(f"Erro ao verificar/instalar {package_name}: {str(e)}")
            results[package_name] = f"error: {str(e)}"
    
    return results

if __name__ == "__main__":
    logger.info("Iniciando instalação de dependências faltantes...")
    results = install_missing_dependencies()
    
    # Contar resultados
    installed = sum(1 for result in results.values() if result == "installed")
    already_installed = sum(1 for result in results.values() if result == "already_installed")
    failed = sum(1 for result in results.values() if result not in ["installed", "already_installed"])
    
    logger.info(f"Instalação concluída: {installed} pacotes instalados, {already_installed} já instalados, {failed} falhas")
    
    if failed > 0:
        logger.warning("Alguns pacotes não puderam ser instalados:")
        for package, result in results.items():
            if result not in ["installed", "already_installed"]:
                logger.warning(f"  - {package}: {result}")
