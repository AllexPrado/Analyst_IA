#!/usr/bin/env python
"""
Script para reiniciar o servidor FastAPI
"""
import os
import sys
import subprocess
import psutil
import time
import signal

def find_uvicorn_processes():
    """Encontra processos uvicorn rodando na porta 8000"""
    result = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'uvicorn' in ' '.join(cmdline) and 'main:app' in ' '.join(cmdline):
                result.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return result

def kill_uvicorn_processes():
    """Mata todos os processos uvicorn rodando"""
    procs = find_uvicorn_processes()
    if not procs:
        print("Nenhum processo uvicorn encontrado.")
        return 0
    
    count = 0
    for proc in procs:
        try:
            pid = proc.info['pid']
            print(f"Encerrando processo uvicorn (PID: {pid})...")
            
            # Tenta encerrar graciosamente primeiro
            os.kill(pid, signal.SIGTERM)
            
            # Espera um pouco para o processo encerrar
            time.sleep(1)
            
            # Se ainda estiver rodando, força o encerramento
            if psutil.pid_exists(pid):
                os.kill(pid, signal.SIGKILL)
            
            count += 1
        except Exception as e:
            print(f"Erro ao encerrar processo: {e}")
    
    return count

def main():
    print("=== REINICIANDO SERVIDOR FASTAPI ===")
    
    # 1. Encerrar quaisquer servidores existentes
    killed = kill_uvicorn_processes()
    if killed > 0:
        print(f"✅ {killed} processo(s) uvicorn encerrado(s)")
        # Esperar um pouco para garantir que a porta seja liberada
        time.sleep(2)
    
    # 2. Iniciar o novo servidor
    print("\nIniciando servidor FastAPI...")
    
    try:
        # Comando para iniciar o servidor
        cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload"]
        
        # Inicia o servidor em um novo processo (não bloqueia este script)
        # No Windows, usa CREATE_NEW_PROCESS_GROUP para evitar a propagação de sinais
        process = subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        print(f"✅ Servidor iniciado com PID: {process.pid}")
        print("\nAguardando inicialização do servidor...")
        
        # Aguarda um tempo para o servidor iniciar
        time.sleep(5)
        
        print("\n✅ Servidor FastAPI reiniciado com sucesso!")
        print("\nPara testar o endpoint Agno, execute:")
        print("python teste_simples_agno.py")
        
    except Exception as e:
        print(f"❌ Erro ao iniciar o servidor: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
