"""
Script para iniciar o backend com os novos endpoints implementados.
Este script garante que todos os diretórios e arquivos necessários existam.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Configurar o logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Garantir que o diretório de dados existe
# Tentar várias localizações possíveis para o diretório de dados
dados_dir_attempts = [
    Path('dados'),         # Relativo ao diretório atual
    Path('../dados'),      # Um nível acima (se estamos em backend)
    Path('backend/dados')  # Caminho relativo ao diretório raiz
]

dados_dir = None
for path in dados_dir_attempts:
    if path.exists() and path.is_dir():
        dados_dir = path
        logger.info(f"Diretório de dados encontrado: {dados_dir.absolute()}")
        break

# Se não encontrou, criar no diretório atual
if dados_dir is None:
    dados_dir = Path('dados')
    dados_dir.mkdir(exist_ok=True)
    logger.info(f"Diretório de dados criado: {dados_dir.absolute()}")

# Verificar se o módulo de endpoints existe
# Checar várias localizações possíveis
endpoints_dir_attempts = [
    Path('endpoints'),         # Relativo ao diretório atual
    Path('../endpoints'),      # Um nível acima (se estamos em backend)
    Path('backend/endpoints')  # Caminho relativo ao diretório raiz
]

endpoints_dir = None
for path in endpoints_dir_attempts:
    if path.exists() and path.is_dir():
        endpoints_dir = path
        logger.info(f"Módulo de endpoints encontrado: {endpoints_dir}")
        break

# Se não encontrou, tentar criar no diretório atual
if endpoints_dir is None:
    endpoints_dir = Path('endpoints')
    endpoints_dir.mkdir(exist_ok=True)
    logger.info(f"Diretório de endpoints criado: {endpoints_dir}")
    if not (endpoints_dir / '__init__.py').exists():
        with open(endpoints_dir / '__init__.py', 'w') as f:
            f.write("# Módulo de endpoints da API")
        logger.info("Arquivo __init__.py criado no diretório de endpoints")

# Mesmo depois de tentar criar, verificar novamente
if not endpoints_dir.exists() or not endpoints_dir.is_dir():
    logger.error("Diretório de endpoints não pôde ser criado. Verifique as permissões.")
    sys.exit(1)

logger.info(f"Módulo de endpoints verificado: {endpoints_dir}")

try:
    import uvicorn
    from fastapi import FastAPI
    logger.info("Dependências verificadas: FastAPI e uvicorn instalados")
except ImportError as e:
    logger.error(f"Faltam dependências necessárias: {e}")
    logger.error("Execute: pip install fastapi uvicorn")
    sys.exit(1)

if __name__ == "__main__":
    logger.info("Iniciando servidor FastAPI com novos endpoints...")
    try:
        # Iniciar o servidor com hot-reload para desenvolvimento
        uvicorn.run(
            "main:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True, 
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Erro ao iniciar o servidor: {e}")
        sys.exit(1)
