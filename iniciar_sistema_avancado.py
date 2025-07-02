#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time
import logging
import argparse
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("iniciar_sistema_avancado.log", mode='a')
    ]
)

logger = logging.getLogger(__name__)

def iniciar_sincronizacao(modo="once"):
    """
    Inicia o processo de sincronização do New Relic
    
    Args:
        modo: "once" para uma sincronização única, "periodic" para sincronização periódica
    """
    logger.info(f"Iniciando sincronização do New Relic (modo: {modo})")
    
    comando = [sys.executable, "sincronizar_newrelic_avancado.py"]
    
    if modo == "once":
        comando.append("--once")
    elif modo == "periodic":
        comando.extend(["--periodic", "--interval", "30"])
    
    try:
        if modo == "once":
            # Sincronização única - aguardar conclusão
            logger.info("Executando sincronização completa (aguardando conclusão)")
            processo = subprocess.run(
                comando,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("Sincronização concluída com sucesso")
            return True
        else:
            # Sincronização periódica - iniciar em background
            logger.info("Iniciando sincronização periódica (em background)")
            processo = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # Aguardar um pouco para verificar se o processo iniciou corretamente
            time.sleep(2)
            
            if processo.poll() is not None:
                # Processo já encerrou - provavelmente erro
                stdout, stderr = processo.communicate()
                logger.error(f"Erro ao iniciar sincronização periódica: {stderr}")
                return False
                
            logger.info(f"Sincronização periódica iniciada (PID: {processo.pid})")
            return True
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao executar sincronização: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Erro ao iniciar sincronização: {e}")
        return False

def iniciar_backend():
    """
    Inicia o backend em um processo separado
    """
    logger.info("Iniciando backend")
    
    try:
        # Em Windows, usar 'start cmd.exe /c "comando"' para iniciar em uma janela separada
        if sys.platform == "win32":
            comando = f'start cmd.exe /c "cd {os.path.join(os.path.dirname(__file__), "backend")} && {sys.executable} main.py"'
            subprocess.Popen(comando, shell=True)
        else:
            # Em sistemas Unix, iniciar em um processo separado
            comando = f"cd {os.path.join(os.path.dirname(__file__), 'backend')} && {sys.executable} main.py"
            subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info("Backend iniciado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao iniciar backend: {e}")
        return False

def iniciar_frontend():
    """
    Inicia o frontend
    """
    logger.info("Iniciando frontend")
    
    try:
        # Mudar para o diretório frontend
        os.chdir(os.path.join(os.path.dirname(__file__), "frontend"))
        
        # Iniciar o frontend
        if sys.platform == "win32":
            subprocess.Popen("npm run dev", shell=True)
        else:
            subprocess.Popen("npm run dev", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info("Frontend iniciado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao iniciar frontend: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Inicia o sistema completo com sincronização avançada do New Relic")
    
    parser.add_argument("--no-sync", action="store_true", 
                       help="Não executar sincronização antes de iniciar o sistema")
    parser.add_argument("--periodic-sync", action="store_true",
                       help="Iniciar sincronização periódica em background")
    
    args = parser.parse_args()
    
    logger.info("Iniciando sistema completo com recursos avançados")
    
    # Verificar se deve executar sincronização
    if not args.no_sync:
        if args.periodic_sync:
            # Iniciar sincronização periódica em background
            if not iniciar_sincronizacao(modo="periodic"):
                logger.warning("Falha ao iniciar sincronização periódica, continuando com o sistema...")
        else:
            # Executar sincronização única antes de iniciar o sistema
            logger.info("Executando sincronização completa inicial...")
            if not iniciar_sincronizacao(modo="once"):
                logger.warning("Falha na sincronização inicial, continuando com o sistema...")
    
    # Iniciar backend em um processo separado
    iniciar_backend()
    
    # Pequena pausa para dar tempo do backend iniciar
    time.sleep(2)
    
    # Iniciar frontend
    iniciar_frontend()
    
    logger.info("Sistema completo iniciado com sucesso")
    print("\n" + "="*60)
    print("SISTEMA INICIADO COM RECURSOS AVANÇADOS")
    print("="*60)
    print("Backend e Frontend estão sendo executados em processos separados.")
    print("O sistema está pronto para uso.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
