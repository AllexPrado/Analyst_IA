#!/usr/bin/env python3
"""
Script para instalar todas as dependências necessárias para o Analyst-IA
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def print_step(message):
    """Imprime uma mensagem de passo com formatação destacada"""
    print(f"\n{'=' * 80}")
    print(f">>> {message}")
    print(f"{'=' * 80}\n")

def run_command(command, cwd=None):
    """Executa um comando e imprime a saída"""
    print(f"Executando: {' '.join(command)}")
    try:
        subprocess.run(command, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o comando: {e}")
        return False

def main():
    """Função principal para instalar dependências"""
    print_step("Verificando ambiente")
    
    # Verificar Python
    python_version = platform.python_version()
    print(f"Versão do Python: {python_version}")
    
    if int(python_version.split('.')[0]) < 3 or (int(python_version.split('.')[0]) == 3 and int(python_version.split('.')[1]) < 8):
        print("Erro: Python 3.8 ou superior é necessário")
        return 1
    
    # Verificar pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True)
    except subprocess.CalledProcessError:
        print("Erro: pip não está instalado ou não está funcionando corretamente")
        return 1
    
    # Verificar Node.js para o frontend
    try:
        node_version = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True).stdout.strip()
        print(f"Versão do Node.js: {node_version}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Aviso: Node.js não encontrado. O frontend não será instalado automaticamente.")
        node_installed = False
    else:
        node_installed = True
    
    # Instalar dependências do backend
    print_step("Instalando dependências do backend")
    
    # Verificar se requirements.txt existe
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        print("Arquivo requirements.txt não encontrado. Criando...")
        with open(requirements_path, "w") as f:
            f.write("""fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
python-dotenv>=1.0.0
httpx>=0.24.1
openai>=1.0.0
tiktoken>=0.4.0
aiofiles>=23.1.0
asyncio>=3.4.3
psutil>=5.9.5
rich>=13.4.2
""")
    
    # Instalar dependências do Python
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]):
        print("Erro: Falha ao instalar dependências do backend")
        return 1
    
    # Instalar dependências do frontend se Node.js estiver disponível
    if node_installed:
        print_step("Instalando dependências do frontend")
        
        frontend_path = Path("frontend")
        if frontend_path.exists() and frontend_path.is_dir():
            # Verificar package.json
            package_json_path = frontend_path / "package.json"
            if package_json_path.exists():
                if not run_command(["npm", "install"], cwd=str(frontend_path)):
                    print("Erro: Falha ao instalar dependências do frontend")
                    return 1
            else:
                print("Aviso: package.json não encontrado no diretório do frontend")
        else:
            print("Aviso: Diretório do frontend não encontrado")
    
    print_step("Verificando instalação")
    
    # Verificar se as principais bibliotecas foram instaladas
    try:
        import fastapi
        import uvicorn
        import pydantic
        import openai
        print("✓ Dependências principais do backend verificadas com sucesso")
    except ImportError as e:
        print(f"Erro: Falha ao importar biblioteca: {e}")
        print("Tente instalar manualmente: pip install fastapi uvicorn pydantic openai")
        return 1
    
    print_step("Instalação concluída com sucesso!")
    print("""
Para iniciar o sistema:

1. Inicie o backend unificado:
   python start_unified_backend.py

2. Inicie o frontend (em outro terminal):
   cd frontend
   npm run dev

3. Acesse o sistema em: http://localhost:5173
""")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
