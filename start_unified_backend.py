#!/usr/bin/env python3
"""
Script principal para iniciar o backend unificado do Analyst-IA.
Este script verifica se há versões antigas rodando, interrompe-as,
e inicia apenas o backend unificado corrigido.
"""

import os
import sys
import subprocess
import time
import logging
import signal
import psutil
import platform
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def kill_process_by_port(port):
    """Mata um processo que está usando a porta especificada"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["netstat", "-ano", "|", "findstr", f":{port}"],
                capture_output=True,
                text=True,
                shell=True
            )
            for line in result.stdout.splitlines():
                parts = [p for p in line.strip().split() if p]
                if len(parts) > 4 and "LISTENING" in line:
                    pid = parts[-1]
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        logger.info(f"Processo na porta {port} (PID: {pid}) terminado")
                        time.sleep(1)  # Aguarda um segundo para o processo encerrar
                    except (ProcessLookupError, PermissionError) as e:
                        logger.error(f"Não foi possível matar o processo {pid}: {e}")
        else:
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-t"],
                capture_output=True,
                text=True
            )
            for pid in result.stdout.splitlines():
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    logger.info(f"Processo na porta {port} (PID: {pid}) terminado")
                    time.sleep(1)  # Aguarda um segundo para o processo encerrar
                except (ProcessLookupError, PermissionError) as e:
                    logger.error(f"Não foi possível matar o processo {pid}: {e}")
    except Exception as e:
        logger.error(f"Erro ao tentar matar processos na porta {port}: {str(e)}")

def kill_python_processes_by_name(name_patterns):
    """Mata processos Python que contenham qualquer um dos padrões de nome especificados"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
                if proc.info['name'] == 'python.exe' or proc.info['name'] == 'python':
                    if any(pattern in cmdline for pattern in name_patterns):
                        logger.info(f"Terminando processo: {proc.info['pid']} - {cmdline[:50]}...")
                        try:
                            psutil.Process(proc.info['pid']).terminate()
                            time.sleep(1)  # Aguarda um segundo para o processo encerrar
                        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                            logger.error(f"Erro ao tentar terminar processo {proc.info['pid']}: {e}")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                pass
    except Exception as e:
        logger.error(f"Erro ao tentar matar processos Python: {str(e)}")

def start_unified_backend():
    """Inicia o backend unificado"""
    try:
        backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
        os.chdir(backend_dir)
        
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
        logger.info(f"Iniciando backend unificado a partir de: {os.getcwd()}")
        
        # Em Windows, use subprocess.Popen para não bloquear
        if platform.system() == "Windows":
            process = subprocess.Popen(
                [sys.executable, "start_unified.py"],
                cwd=backend_dir
            )
            logger.info(f"Backend unificado iniciado com PID: {process.pid}")
        else:
            # Em Unix, use subprocess.run
            process = subprocess.Popen(
                [sys.executable, "start_unified.py"],
                cwd=backend_dir
            )
            logger.info(f"Backend unificado iniciado com PID: {process.pid}")
        
        return process
    except Exception as e:
        logger.error(f"Erro ao iniciar backend unificado: {str(e)}")
        return None

def main():
    """Função principal que gerencia o início do backend unificado"""
    logger.info("Gerenciador de backend Analyst-IA iniciando...")
    
    # Mata qualquer processo existente nas portas que usamos
    logger.info("Verificando e matando processos existentes nas portas...")
    kill_process_by_port(8000)
    
    # Mata processos Python antigos
    logger.info("Verificando e matando processos Python antigos...")
    kill_python_processes_by_name([
        "main.py", 
        "main_minimal.py",
        "start_backend.py",
        "start_backend_safe.py",
        "start_simple.py"
    ])
    
    # Aguarda um momento para garantir que tudo foi encerrado
    time.sleep(2)
    
    # Inicia o backend unificado
    logger.info("Iniciando backend unificado...")
    process = start_unified_backend()
    
    if process:
        logger.info("Backend iniciado com sucesso!")
        
        try:
            # No Windows, apenas registra que o processo foi iniciado
            if platform.system() == "Windows":
                logger.info(f"Processo iniciado com PID {process.pid}. O script continuará em execução.")
                time.sleep(5)  # Aguarda 5 segundos para verificar que o backend iniciou corretamente
                logger.info("Backend parece estar funcionando. Verifique o log para mais detalhes.")
                return 0
            else:
                # Em sistemas Unix, aguarda o processo terminar
                return_code = process.wait()
                logger.info(f"Backend unificado encerrado com código de retorno: {return_code}")
                return return_code
        except KeyboardInterrupt:
            logger.info("Interrupção detectada, encerrando backend...")
            if process.poll() is None:  # Se o processo ainda estiver em execução
                process.terminate()
                try:
                    process.wait(timeout=5)  # Aguarda até 5 segundos
                except subprocess.TimeoutExpired:
                    process.kill()  # Força o encerramento se demorar muito
            logger.info("Backend encerrado.")
            return 0
    else:
        logger.error("Falha ao iniciar o backend unificado!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
