#!/usr/bin/env python3
"""
Script para reiniciar completamente o sistema Analyst-IA após correções
"""

import os
import sys
import subprocess
import time
import logging
import psutil
import platform
import signal
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
                        time.sleep(1)
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
                    time.sleep(1)
                except (ProcessLookupError, PermissionError) as e:
                    logger.error(f"Não foi possível matar o processo {pid}: {e}")
    except Exception as e:
        logger.error(f"Erro ao tentar matar processos na porta {port}: {str(e)}")

def find_and_kill_python_processes(name_patterns):
    """Encontra e mata processos Python que correspondem aos padrões fornecidos"""
    found = False
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe' or proc.info['name'] == 'python':
                cmdline = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
                
                # Verifica se algum padrão corresponde
                if any(pattern in cmdline for pattern in name_patterns):
                    logger.info(f"Encontrado processo Python: PID {proc.info['pid']} - {cmdline[:100]}...")
                    try:
                        proc_obj = psutil.Process(proc.info['pid'])
                        proc_obj.terminate()
                        found = True
                        logger.info(f"Processo terminado: {proc.info['pid']}")
                        time.sleep(1)
                    except Exception as e:
                        logger.error(f"Erro ao terminar processo {proc.info['pid']}: {e}")
        except Exception:
            pass
    
    return found

def clear_node_modules():
    """Limpa o node_modules do frontend para garantir uma instalação limpa"""
    node_modules_path = Path("frontend/node_modules")
    
    if node_modules_path.exists():
        logger.info("Removendo node_modules existente para instalação limpa...")
        try:
            if platform.system() == "Windows":
                subprocess.run(["rmdir", "/s", "/q", str(node_modules_path)], shell=True)
            else:
                subprocess.run(["rm", "-rf", str(node_modules_path)])
            logger.info("node_modules removido com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover node_modules: {e}")
            return False
    
    return True

def start_backend():
    """Inicia o backend unificado"""
    logger.info("Iniciando backend unificado...")
    
    try:
        backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
        
        if not Path(backend_dir).exists():
            logger.error(f"Diretório backend não encontrado: {backend_dir}")
            return None
        
        # Em Windows, use subprocess.Popen para não bloquear
        if platform.system() == "Windows":
            process = subprocess.Popen(
                [sys.executable, "unified_backend.py"],
                cwd=backend_dir
            )
            logger.info(f"Backend iniciado com PID: {process.pid}")
        else:
            # Em Unix, também use Popen para não bloquear
            process = subprocess.Popen(
                [sys.executable, "unified_backend.py"],
                cwd=backend_dir
            )
            logger.info(f"Backend iniciado com PID: {process.pid}")
        
        # Aguarda alguns segundos para o backend iniciar
        logger.info("Aguardando o backend inicializar...")
        time.sleep(5)
        
        return process
    except Exception as e:
        logger.error(f"Erro ao iniciar backend: {e}")
        return None

def wait_for_backend():
    """Aguarda o backend estar pronto"""
    import requests
    
    for i in range(30):  # Tenta por 30 segundos
        try:
            response = requests.get("http://localhost:8000/api/status", timeout=1)
            if response.status_code == 200:
                logger.info("Backend está pronto!")
                return True
        except Exception:
            pass
        
        time.sleep(1)
        if i % 5 == 0:
            logger.info(f"Ainda aguardando o backend... ({i}s)")
    
    logger.error("Timeout aguardando o backend iniciar")
    return False

def check_npm_installed():
    """Verifica se o npm está instalado e disponível no PATH"""
    try:
        result = subprocess.run(['npm', '--version'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def start_frontend():
    """Inicia o frontend"""
    logger.info("Iniciando frontend...")
    
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
    
    if not Path(frontend_dir).exists():
        logger.error(f"Diretório frontend não encontrado: {frontend_dir}")
        return None
    
    # Verifica se package.json existe
    if not Path(frontend_dir, "package.json").exists():
        logger.error("package.json não encontrado no diretório do frontend")
        return None
    
    # Verifica se npm está instalado
    try:
        npm_check = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True
        )
        if npm_check.returncode != 0:
            logger.error("Node.js/npm não está instalado ou não está no PATH")
            logger.error("Por favor, instale Node.js de https://nodejs.org/ e reinicie este script")
            return None
    except FileNotFoundError:
        logger.error("Node.js/npm não está instalado ou não está no PATH")
        logger.error("Por favor, instale Node.js de https://nodejs.org/ e reinicie este script")
        return None
    
    # Instala dependências se não existirem
    node_modules = Path(frontend_dir, "node_modules")
    if not node_modules.exists():
        logger.info("Instalando dependências do frontend...")
        try:
            result = subprocess.run(
                ["npm", "install"],
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Erro ao instalar dependências: {result.stderr}")
                return None
            
            logger.info("Dependências instaladas com sucesso")
        except Exception as e:
            logger.error(f"Erro ao instalar dependências: {e}")
            return None
    
    # Inicia o servidor de desenvolvimento
    try:
        # Usa shell=True para garantir que o comando funcione corretamente no Windows
        process = subprocess.Popen(
            "npm run dev",
            cwd=frontend_dir,
            shell=True
        )
        
        logger.info(f"Frontend iniciado com PID: {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Erro ao iniciar frontend: {e}")
        logger.error(f"Detalhes do erro: {str(e)}")
        return None

def main():
    """Função principal"""
    logger.info("=== Reiniciando Sistema Analyst-IA ===")
    
    # 1. Mata todos os processos existentes
    logger.info("\n1. Encerrando processos existentes...")
    
    # Mata processos nas portas conhecidas
    kill_process_by_port(8000)  # Backend
    kill_process_by_port(5173)  # Frontend
    
    # Mata processos Python conhecidos
    patterns = [
        "main.py",
        "unified_backend.py",
        "start_backend",
        "start_unified",
        "analyst_ia"
    ]
    
    if find_and_kill_python_processes(patterns):
        logger.info("Processos Python encerrados")
        time.sleep(2)  # Aguarda um pouco para garantir que os processos foram encerrados
    else:
        logger.info("Nenhum processo Python relacionado encontrado")
    
    # 2. Limpa instalações antigas
    logger.info("\n2. Limpando instalações antigas...")
    clear_node_modules()
    
    # 3. Inicia o backend
    logger.info("\n3. Iniciando backend...")
    backend_process = start_backend()
    
    if not backend_process:
        logger.error("Falha ao iniciar o backend")
        return 1
    
    # Aguarda o backend ficar pronto
    if not wait_for_backend():
        logger.error("Backend não respondeu no tempo esperado")
        return 1
    
    # 4. Inicia o frontend
    logger.info("\n4. Iniciando frontend...")
    frontend_process = start_frontend()
    
    if not frontend_process:
        logger.error("Falha ao iniciar o frontend")
        return 1
    
    logger.info("\n=== Sistema Analyst-IA Reiniciado com Sucesso ===")
    logger.info("Frontend: http://localhost:5173")
    logger.info("Backend: http://localhost:8000")
    logger.info("\nPressione Ctrl+C para encerrar todos os processos")
    
    # Aguarda até que o usuário interrompa o script
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nEncerrando processos...")
        
        if backend_process and backend_process.poll() is None:
            backend_process.terminate()
        
        if frontend_process and frontend_process.poll() is None:
            frontend_process.terminate()
        
        logger.info("Processos encerrados")
    
    return 0

if __name__ == "__main__":
    import signal
    sys.exit(main())
