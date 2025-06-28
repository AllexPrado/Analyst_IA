#!/usr/bin/env python3
"""
Script para iniciar o backend unificado do Analyst-IA.
Este backend corrige os erros anteriores e é a única
versão que deve ser usada.
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Função principal para iniciar o backend unificado"""
    logger.info("Iniciando Analyst-IA Backend Unificado...")
    
    # Verificar se diretório de logs existe
    log_dir = Path("logs")
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Criado diretório de logs")
    
    # Verificar se diretório de histórico existe
    historico_dir = Path("historico")
    if not historico_dir.exists():
        historico_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Criado diretório de histórico")
        
        # Criar subdiretório para consultas
        consultas_dir = historico_dir / "consultas"
        if not consultas_dir.exists():
            consultas_dir.mkdir(parents=True, exist_ok=True)
    
    # Iniciar o servidor
    try:
        port = 8000
        logger.info(f"Servidor iniciando na porta {port}...")
        uvicorn.run(
            "unified_backend:app", 
            host="127.0.0.1", 
            port=port, 
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
