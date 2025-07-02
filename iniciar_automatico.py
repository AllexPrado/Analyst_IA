#!/usr/bin/env python3
"""
Script para inicializar o sistema Analyst IA de forma robusta
"""

import os
import sys
import subprocess
import time
import platform
from pathlib import Path

def run_command(cmd, shell=True, cwd=None):
    """Executa um comando e retorna o resultado"""
    try:
        result = subprocess.run(cmd, shell=shell, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_python_env():
    """Verifica se o ambiente Python está configurado"""
    print("🔍 Verificando ambiente Python...")
    
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("❌ Ambiente virtual não encontrado!")
        return False
    
    # Verifica se o uvicorn está instalado
    if platform.system() == "Windows":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    if not python_exe.exists():
        print("❌ Python não encontrado no ambiente virtual!")
        return False
        
    print("✅ Ambiente virtual encontrado")
    return True

def install_dependencies():
    """Instala dependências necessárias"""
    print("📦 Verificando dependências...")
    
    if platform.system() == "Windows":
        pip_exe = Path(".venv/Scripts/pip.exe")
        python_exe = Path(".venv/Scripts/python.exe")
    else:
        pip_exe = Path(".venv/bin/pip")
        python_exe = Path(".venv/bin/python")
    
    # Lista de dependências essenciais
    dependencies = [
        "fastapi",
        "uvicorn[standard]", 
        "python-dotenv",
        "openai",
        "requests",
        "aiohttp",
        "pydantic"
    ]
    
    for dep in dependencies:
        print(f"Verificando {dep}...")
        dep_name = dep.split('[')[0].replace('-', '_')
        success, _, _ = run_command(f'"{python_exe}" -c "import {dep_name}"')
        if not success:
            print(f"Instalando {dep}...")
            run_command(f'"{pip_exe}" install {dep}')
    
    print("✅ Dependências verificadas")

def check_node_env():
    """Verifica se o Node.js está configurado"""
    print("🔍 Verificando ambiente Node.js...")
    
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print("❌ Pasta frontend não encontrada!")
        return False
    
    package_json = frontend_path / "package.json"
    if not package_json.exists():
        print("❌ package.json não encontrado!")
        return False
        
    node_modules = frontend_path / "node_modules"
    if not node_modules.exists():
        print("📦 Instalando dependências do frontend...")
        success, _, _ = run_command("npm install", cwd=frontend_path)
        if not success:
            print("❌ Falha ao instalar dependências do frontend!")
            return False
    
    print("✅ Ambiente Node.js configurado")
    return True

def start_backend():
    """Inicia o backend"""
    print("🚀 Iniciando backend...")
    
    if platform.system() == "Windows":
        python_exe = Path(".venv/Scripts/python.exe")
        uvicorn_exe = Path(".venv/Scripts/uvicorn.exe")
    else:
        python_exe = Path(".venv/bin/python")
        uvicorn_exe = Path(".venv/bin/uvicorn")
    
    backend_path = Path("backend")
    
    if uvicorn_exe.exists():
        cmd = f'"{uvicorn_exe}" main:app --reload --host 0.0.0.0 --port 8000'
    else:
        cmd = f'"{python_exe}" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000'
    
    # Inicia em uma nova janela no Windows
    if platform.system() == "Windows":
        subprocess.Popen(f'start "Backend Analyst IA" cmd /k "cd backend && {cmd}"', shell=True)
    else:
        subprocess.Popen(f'gnome-terminal -- bash -c "cd backend && {cmd}"', shell=True)
    
    print("✅ Backend iniciado em nova janela")
    return True

def start_frontend():
    """Inicia o frontend"""
    print("🚀 Iniciando frontend...")
    
    frontend_path = Path("frontend")
    
    # Inicia em uma nova janela no Windows
    if platform.system() == "Windows":
        subprocess.Popen(f'start "Frontend Analyst IA" cmd /k "cd frontend && npm run dev"', shell=True)
    else:
        subprocess.Popen(f'gnome-terminal -- bash -c "cd frontend && npm run dev"', shell=True)
    
    print("✅ Frontend iniciado em nova janela")
    return True

def main():
    """Função principal"""
    print("="*50)
    print("🔧 INICIALIZAÇÃO AUTOMÁTICA - ANALYST IA")
    print("="*50)
    
    # Verifica se estamos na pasta correta
    if not Path("backend").exists() or not Path("frontend").exists():
        print("❌ Execute este script na pasta raiz do projeto!")
        sys.exit(1)
    
    try:
        # Verifica ambiente Python
        if not check_python_env():
            print("❌ Ambiente Python não configurado!")
            sys.exit(1)
        
        # Instala dependências Python
        install_dependencies()
        
        # Verifica ambiente Node.js
        if not check_node_env():
            print("❌ Ambiente Node.js não configurado!")
            sys.exit(1)
        
        print("\n🚀 Iniciando serviços...")
        
        # Inicia backend
        start_backend()
        
        # Aguarda um pouco
        print("⏳ Aguardando backend inicializar...")
        time.sleep(5)
        
        # Inicia frontend
        start_frontend()
        
        print("\n" + "="*50)
        print("✅ SISTEMA INICIADO COM SUCESSO!")
        print("="*50)
        print("📡 Backend: http://localhost:8000")
        print("🌐 Frontend: http://localhost:5173")
        print("💬 Chat IA: http://localhost:5173/chat")
        print("📊 Dashboard: http://localhost:5173/dashboard")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n❌ Inicialização cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante inicialização: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
