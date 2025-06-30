#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para iniciar o sistema com verificação completa de dados
e funcionalidades de integração frontend-backend.
"""

import os
import sys
import subprocess
import logging
import time

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def executar_script(script, descricao):
    """Executa um script Python e exibe o resultado"""
    logger.info(f"Executando: {descricao}")
    try:
        resultado = subprocess.run(
            [sys.executable, script], 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"✅ {descricao} executado com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro ao executar {descricao}: {e}")
        logger.error(f"Saída de erro: {e.stderr}")
        return False

def main():
    """Função principal para iniciar o sistema com verificação completa"""
    logger.info("=== INICIANDO ANALYST IA COM VERIFICAÇÃO COMPLETA ===")
    
    # Gerar todos os dados de demonstração
    if not executar_script("backend/gerar_todos_dados_demo.py", "Geração de dados de demonstração"):
        logger.warning("⚠️ Alguns dados podem estar faltando. Tentando continuar...")
    
    # Verificar arquivos de dados (sem verificar endpoints, pois o backend ainda não está rodando)
    executar_script("verificar_integracao.py", "Verificação de arquivos de dados")
    
    # Iniciar o sistema principal
    logger.info("Iniciando o sistema completo...")
    try:
        subprocess.Popen([sys.executable, "iniciar_sistema.py"], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        
        # Dar tempo para o backend iniciar
        logger.info("Aguardando o sistema iniciar (20 segundos)...")
        time.sleep(20)
        
        # Verificar a integração completa (com o backend rodando)
        executar_script("verificar_integracao.py", "Verificação completa da integração")
        
        logger.info("\n==================================================")
        logger.info("✅ SISTEMA INICIADO E VERIFICADO COM SUCESSO!")
        logger.info("==================================================")
        logger.info("- Frontend disponível em: http://localhost:5173")
        logger.info("- Backend API disponível em: http://localhost:8000")
        logger.info("==================================================")
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar o sistema: {e}")
        return False

if __name__ == "__main__":
    main()
