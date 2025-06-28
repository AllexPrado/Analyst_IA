#!/usr/bin/env python3
"""
Script para reiniciar os servidores backend e frontend
"""

import os
import sys
import subprocess
import time
import platform
import signal
from pathlib import Path

def kill_process(process_name):
    """Mata processos pelo nome"""
    if platform.system() == "Windows":
        try:
            os.system(f"taskkill /f /im {process_name} /t > nul 2>&1")
            print(f"✓ Processos {process_name} terminados")
        except Exception as e:
            print(f"✗ Erro ao terminar {process_name}: {e}")
    else:
        try:
            os.system(f"pkill -f {process_name}")
            print(f"✓ Processos {process_name} terminados")
        except Exception as e:
            print(f"✗ Erro ao terminar {process_name}: {e}")

def main():
    """Função principal"""
    print("\n" + "=" * 60)
    print(" Reiniciando servidores Backend e Frontend ".center(60, "="))
    print("=" * 60 + "\n")
    
    # Encontra o diretório base do projeto
    base_dir = Path(__file__).parent.absolute()
    
    # 1. Mata processos em execução
    print("1. Terminando processos em execução...")
    kill_process("unified_backend.py")
    kill_process("node.exe" if platform.system() == "Windows" else "node")
    time.sleep(2)
    
    # 2. Inicia o backend
    print("\n2. Iniciando backend...")
    backend_path = base_dir / "backend" / "unified_backend.py"
    if not backend_path.exists():
        print(f"✗ Arquivo backend não encontrado: {backend_path}")
        return 1
        
    try:
        backend_process = subprocess.Popen(
            [sys.executable, str(backend_path)],
            cwd=str(base_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == "Windows" else 0
        )
        print(f"✓ Backend iniciado (PID: {backend_process.pid})")
    except Exception as e:
        print(f"✗ Erro ao iniciar backend: {e}")
        return 1
    
    # 3. Aguarda backend inicializar
    print("   Aguardando inicialização do backend (5s)...")
    time.sleep(5)
    
    # 4. Inicia o frontend
    print("\n3. Iniciando frontend...")
    frontend_dir = base_dir / "frontend"
    if not frontend_dir.exists():
        print(f"✗ Diretório frontend não encontrado: {frontend_dir}")
        return 1
        
    try:
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(frontend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == "Windows" else 0
        )
        print(f"✓ Frontend iniciado (PID: {frontend_process.pid})")
    except Exception as e:
        print(f"✗ Erro ao iniciar frontend: {e}")
        backend_process.terminate()
        return 1
    
    # 5. Resumo
    print("\n" + "=" * 60)
    print(" Servidores reiniciados com sucesso! ".center(60, "="))
    print("=" * 60)
    print(f"Backend: http://localhost:8000")
    print(f"Frontend: http://localhost:5174")
    print("=" * 60 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
