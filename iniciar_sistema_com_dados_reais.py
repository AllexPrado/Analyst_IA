#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para iniciar o sistema Analyst_IA com dados reais do New Relic.
Este script realiza as seguintes operações:
1. Verifica as credenciais do New Relic
2. Integra dados reais ou simulados conforme disponibilidade das credenciais
3. Inicia a sincronização periódica em segundo plano
4. Inicia o backend e frontend do sistema
"""

import os
import sys
import subprocess
import time
import logging
import argparse
from datetime import datetime
import threading

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/iniciar_sistema_real.log", mode='a')
    ]
)

logger = logging.getLogger(__name__)
os.makedirs("logs", exist_ok=True)

def verificar_credenciais():
    """Verifica se as credenciais do New Relic estão disponíveis"""
    account_id = os.environ.get("NEW_RELIC_ACCOUNT_ID")
    api_key = os.environ.get("NEW_RELIC_API_KEY")
    
    if account_id and api_key:
        logger.info("Credenciais do New Relic encontradas!")
        return True
    else:
        logger.warning("Credenciais do New Relic não encontradas. Usando dados simulados.")
        return False

def integrar_dados_reais():
    """Integra dados reais ou simulados do New Relic"""
    try:
        logger.info("Integrando dados do New Relic...")
        
        # Definir comando com base na disponibilidade das credenciais
        if verificar_credenciais():
            cmd = [sys.executable, "integrar_dados_reais_newrelic.py"]
        else:
            cmd = [sys.executable, "integrar_dados_reais_newrelic.py", "--simulated"]
            
        # Executar script de integração
        subprocess.run(cmd, check=True)
        logger.info("Integração de dados concluída com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao integrar dados: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao integrar dados: {e}")
        return False

def iniciar_sincronizacao_periodica(intervalo=30):
    """Inicia a sincronização periódica em segundo plano"""
    try:
        logger.info(f"Iniciando sincronização periódica a cada {intervalo} minutos...")
        
        # Iniciar o script de sincronização periódica em segundo plano
        cmd = [sys.executable, "sincronizar_periodico_newrelic.py", "--intervalo", str(intervalo)]
        
        if os.name == 'nt':  # Windows
            proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # Linux/Mac
            proc = subprocess.Popen(cmd, start_new_session=True)
            
        logger.info(f"Sincronização periódica iniciada (PID: {proc.pid})")
        return proc
    except Exception as e:
        logger.error(f"Erro ao iniciar sincronização periódica: {e}")
        return None

def iniciar_backend():
    """Inicia o backend do sistema"""
    try:
        logger.info("Iniciando backend...")
        
        # Primeiro verificar e corrigir o cache
        subprocess.run([sys.executable, "backend/check_and_fix_cache.py"], check=True)
        
        # Iniciar o backend
        if os.name == 'nt':  # Windows
            proc = subprocess.Popen([sys.executable, "backend/main.py"], 
                                  creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # Linux/Mac
            proc = subprocess.Popen([sys.executable, "backend/main.py"],
                                  start_new_session=True)
            
        logger.info(f"Backend iniciado (PID: {proc.pid})")
        return proc
    except Exception as e:
        logger.error(f"Erro ao iniciar backend: {e}")
        return None

def iniciar_frontend():
    """Inicia o frontend do sistema"""
    try:
        logger.info("Iniciando frontend...")
        
        # Navegar para o diretório do frontend
        os.chdir("frontend")
        
        # Iniciar o frontend
        if os.name == 'nt':  # Windows
            proc = subprocess.Popen(["npm", "run", "dev"], 
                                  creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # Linux/Mac
            proc = subprocess.Popen(["npm", "run", "dev"],
                                  start_new_session=True)
            
        # Voltar ao diretório original
        os.chdir("..")
            
        logger.info(f"Frontend iniciado (PID: {proc.pid})")
        return proc
    except Exception as e:
        logger.error(f"Erro ao iniciar frontend: {e}")
        return None

def iniciar_sistema():
    """Inicia o sistema completo com dados reais"""
    logger.info("=== INICIANDO SISTEMA ANALYST_IA COM DADOS REAIS ===")
    
    # Etapa 1: Integrar dados reais ou simulados
    if not integrar_dados_reais():
        logger.warning("Falha na integração de dados. Continuando com dados existentes.")
    
    # Etapa 2: Iniciar sincronização periódica
    sync_proc = iniciar_sincronizacao_periodica()
    
    # Etapa 3: Iniciar backend
    backend_proc = iniciar_backend()
    if not backend_proc:
        logger.error("Falha ao iniciar backend. Abortando.")
        if sync_proc:
            sync_proc.terminate()
        return False
    
    # Aguardar alguns segundos para o backend inicializar
    logger.info("Aguardando inicialização do backend...")
    time.sleep(5)
    
    # Etapa 4: Iniciar frontend
    frontend_proc = iniciar_frontend()
    if not frontend_proc:
        logger.error("Falha ao iniciar frontend.")
        if backend_proc:
            backend_proc.terminate()
        if sync_proc:
            sync_proc.terminate()
        return False
    
    logger.info("\n=== SISTEMA INICIADO COM SUCESSO! ===")
    logger.info("Frontend disponível em: http://localhost:3000")
    logger.info("Backend disponível em: http://localhost:8000")
    logger.info("Dados sendo sincronizados periodicamente")
    
    if not verificar_credenciais():
        logger.warning("\nATENÇÃO: Sistema usando dados SIMULADOS.")
        logger.warning("Para usar dados reais, defina as variáveis de ambiente:")
        logger.warning("  - NEW_RELIC_ACCOUNT_ID")
        logger.warning("  - NEW_RELIC_API_KEY")
    else:
        logger.info("\nSistema usando dados REAIS do New Relic.")
    
    logger.info("\nPressione CTRL+C para encerrar todos os processos\n")
    
    try:
        # Manter o script em execução para que o usuário possa interromper com CTRL+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Encerrando sistema...")
        
        # Encerrar processos
        if frontend_proc:
            frontend_proc.terminate()
        if backend_proc:
            backend_proc.terminate()
        if sync_proc:
            sync_proc.terminate()
            
        logger.info("Sistema encerrado.")
    
    return True

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Iniciar sistema Analyst_IA com dados reais")
    parser.add_argument('--sem-sincronizacao', action='store_true',
                      help="Iniciar sem sincronização periódica")
    parser.add_argument('--intervalo', type=int, default=30,
                      help="Intervalo em minutos para sincronização periódica (padrão: 30)")
    args = parser.parse_args()
    
    try:
        # Verificar se o diretório atual é o diretório raiz do projeto
        if not os.path.exists("frontend") or not os.path.exists("backend"):
            logger.error("Este script deve ser executado no diretório raiz do projeto Analyst_IA.")
            return 1
        
        # Iniciar sistema
        iniciar_sistema()
    except Exception as e:
        logger.error(f"Erro ao iniciar sistema: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
