#!/usr/bin/env python3
"""
Script para iniciar o sistema Analyst_IA otimizado
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def main():
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = base_dir / "backend"
    frontend_dir = base_dir / "frontend"
    
    print("=== INICIANDO ANALYST IA OTIMIZADO ===")
    print("")
    
    # 1. Verificar cache e dados
    print("1. Verificando cache e dados...")
    os.chdir(backend_dir)
    subprocess.run([sys.executable, "check_and_fix_cache.py"], check=True)
    
    # 2. Iniciar backend
    print("")
    print("2. Iniciando backend...")
    if platform.system() == "Windows":
        backend_process = subprocess.Popen(["start", "cmd", "/c", "python", "main.py"], 
                                          shell=True)
    else:
        backend_process = subprocess.Popen([sys.executable, "main.py"],
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          start_new_session=True)
    
    # 3. Iniciar frontend
    print("")
    print("3. Iniciando frontend...")
    os.chdir(frontend_dir)
    subprocess.run(["npm", "run", "dev"], check=True)

if __name__ == "__main__":
    main()
