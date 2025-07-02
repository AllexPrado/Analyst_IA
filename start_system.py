#!/usr/bin/env python3
"""
Script para inicialização completa do sistema Analyst-IA (Backend + Frontend)
"""

import os
import sys
import subprocess
import time
import signal
import platform
from pathlib import Path

# Configuração de caminhos
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Verifica se estamos no Windows
IS_WINDOWS = platform.system() == "Windows"

def log_info(message):
    """Exibe uma mensagem informativa"""
    print(f"[INFO] {message}")

def log_error(message):
    """Exibe uma mensagem de erro"""
    print(f"[ERRO] {message}")

def log_success(message):
    """Exibe uma mensagem de sucesso"""
    print(f"[SUCESSO] {message}")

def run_process(command, cwd=None, shell=None):
    """Executa um processo e retorna o objeto"""
    if shell is None:
        shell = IS_WINDOWS
    
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8'
        )
        return process
    except Exception as e:
        log_error(f"Erro ao executar comando: {e}")
        return None

def check_cache():
    """Verifica e corrige o cache do sistema"""
    log_info("Verificando e corrigindo cache...")
    
    # Define o comando baseado no sistema operacional
    if IS_WINDOWS:
        command = [sys.executable, "check_and_fix_cache.py"]
    else:
        command = [sys.executable, "check_and_fix_cache.py"]
    
    # Executa o processo
    process = run_process(command, cwd=str(BACKEND_DIR))
    if not process:
        log_error("Falha ao executar o script de verificação de cache")
        return False
    
    # Aguarda a conclusão
    process.wait()
    
    if process.returncode == 0:
        log_success("Cache verificado e corrigido com sucesso")
        return True
    else:
        log_error("Falha na verificação de cache")
        return False

def start_backend():
    """Inicia o servidor backend"""
    log_info("Iniciando o servidor backend...")
    
    # Define o comando baseado no sistema operacional
    if IS_WINDOWS:
        command = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    else:
        command = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    
    # Executa o processo
    process = run_process(command, cwd=str(BACKEND_DIR))
    if not process:
        log_error("Falha ao iniciar o servidor backend")
        return None
    
    # Aguarda um pouco para o servidor iniciar
    time.sleep(2)
    
    log_success(f"Servidor backend iniciado (PID: {process.pid})")
    return process

def start_frontend():
    """Inicia o servidor frontend"""
    log_info("Iniciando o servidor frontend...")
    
    # Verifica se o diretório frontend existe
    if not FRONTEND_DIR.exists():
        log_error(f"Diretório frontend não encontrado: {FRONTEND_DIR}")
        return None
    
    # Define o comando baseado no sistema operacional
    if IS_WINDOWS:
        command = ["npm", "run", "dev"]
    else:
        command = ["npm", "run", "dev"]
    
    # Executa o processo
    process = run_process(command, cwd=str(FRONTEND_DIR), shell=True)
    if not process:
        log_error("Falha ao iniciar o servidor frontend")
        return None
    
    # Aguarda um pouco para o servidor iniciar
    time.sleep(3)
    
    log_success(f"Servidor frontend iniciado (PID: {process.pid})")
    return process

def setup_signal_handlers(processes):
    """Configura os manipuladores de sinais para encerrar os processos corretamente"""
    def signal_handler(sig, frame):
        log_info("\nEncerrando servidores...")
        for process in processes:
            if process and process.poll() is None:  # Se o processo ainda estiver em execução
                try:
                    if IS_WINDOWS:
                        process.terminate()
                    else:
                        process.send_signal(signal.SIGTERM)
                except Exception as e:
                    log_error(f"Erro ao encerrar processo: {e}")
        
        log_info("Servidores encerrados. Até breve!")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Função principal para iniciar todo o sistema"""
    print("\n" + "=" * 80)
    print(" INICIALIZAÇÃO DO SISTEMA ANALYST-IA ")
    print("=" * 80)
    
    # Verificar e corrigir o cache
    check_cache()
    
    # Iniciar o backend
    backend_process = start_backend()
    if not backend_process:
        log_error("Falha ao iniciar o backend. Abortando...")
        return
    
    # Iniciar o frontend
    frontend_process = start_frontend()
    if not frontend_process:
        log_error("Falha ao iniciar o frontend. Encerrando backend...")
        if backend_process:
            backend_process.terminate()
        return
    
    # Configurar manipuladores de sinais
    setup_signal_handlers([backend_process, frontend_process])
    
    print("\n" + "=" * 80)
    print(" SISTEMA ANALYST-IA INICIADO COM SUCESSO ")
    print("=" * 80)
    print("Backend: http://localhost:8000")
    print("Frontend: http://localhost:5173")
    print("API Docs: http://localhost:8000/docs")
    print("\nPressione Ctrl+C para encerrar os servidores.")
    
    # Manter o script em execução
    try:
        while True:
            # Verificar se os processos ainda estão em execução
            if backend_process and backend_process.poll() is not None:
                log_error("O servidor backend foi encerrado inesperadamente")
                if frontend_process and frontend_process.poll() is None:
                    frontend_process.terminate()
                break
            
            if frontend_process and frontend_process.poll() is not None:
                log_error("O servidor frontend foi encerrado inesperadamente")
                if backend_process and backend_process.poll() is None:
                    backend_process.terminate()
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        # Já tratado pelo manipulador de sinais
        pass

if __name__ == "__main__":
    main()
