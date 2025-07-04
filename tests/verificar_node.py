#!/usr/bin/env python3
"""
Script para verificar a instalação do Node.js e npm
"""

import subprocess
import sys
import os
import webbrowser
import platform
from pathlib import Path

def print_header(message):
    """Imprime uma mensagem de cabeçalho"""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80)

def check_node_npm():
    """Verifica se Node.js e npm estão instalados"""
    print_header("Verificando Node.js e npm")
    
    try:
        # Verifica Node.js
        node_process = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True
        )
        
        if node_process.returncode == 0:
            node_version = node_process.stdout.strip()
            print(f"✓ Node.js instalado: {node_version}")
        else:
            print("✗ Node.js não está instalado ou não está funcionando corretamente")
            return False
        
        # Verifica npm
        npm_process = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True
        )
        
        if npm_process.returncode == 0:
            npm_version = npm_process.stdout.strip()
            print(f"✓ npm instalado: {npm_version}")
            return True
        else:
            print("✗ npm não está instalado ou não está funcionando corretamente")
            return False
    
    except FileNotFoundError:
        print("✗ Node.js/npm não está instalado ou não está no PATH")
        return False

def install_frontend_deps():
    """Tenta instalar as dependências do frontend"""
    print_header("Instalando dependências do frontend")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists() or not frontend_dir.is_dir():
        print(f"✗ Diretório do frontend não encontrado: {frontend_dir}")
        return False
    
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print(f"✗ Arquivo package.json não encontrado: {package_json}")
        return False
    
    try:
        print("Executando 'npm install'...")
        process = subprocess.run(
            ["npm", "install"],
            cwd=str(frontend_dir),
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            print("✓ Dependências do frontend instaladas com sucesso")
            
            # Verifica se o Vite foi instalado
            vite_check = subprocess.run(
                ["npx", "vite", "--version"],
                cwd=str(frontend_dir),
                capture_output=True,
                text=True
            )
            
            if vite_check.returncode == 0:
                vite_version = vite_check.stdout.strip()
                print(f"✓ Vite instalado: {vite_version}")
            else:
                print("✗ Vite não está disponível. Verificando node_modules...")
                
                vite_dir = frontend_dir / "node_modules" / "vite"
                if vite_dir.exists():
                    print("✓ Vite encontrado em node_modules, mas não está disponível no PATH")
                else:
                    print("✗ Vite não foi instalado. Tente instalar manualmente:")
                    print("  cd frontend")
                    print("  npm install vite")
            
            return True
        else:
            print(f"✗ Erro ao instalar dependências: {process.stderr}")
            return False
    
    except Exception as e:
        print(f"✗ Erro ao instalar dependências: {e}")
        return False

def main():
    """Função principal"""
    print_header("Verificação do Ambiente Node.js")
    
    node_installed = check_node_npm()
    
    if not node_installed:
        print_header("Node.js não encontrado")
        print("Para executar o frontend, você precisa instalar o Node.js.")
        print("")
        print("1. Baixe e instale o Node.js de https://nodejs.org/")
        print("2. Reinicie seu terminal/prompt de comando após a instalação")
        print("3. Execute este script novamente para verificar a instalação")
        
        # Pergunta se quer abrir o site do Node.js
        response = input("\nDeseja abrir o site do Node.js agora? (s/n): ")
        if response.lower() in ["s", "sim", "y", "yes"]:
            webbrowser.open("https://nodejs.org/")
        
        return 1
    
    # Se Node.js estiver instalado, tenta instalar as dependências do frontend
    deps_installed = install_frontend_deps()
    
    if deps_installed:
        print_header("Próximos passos")
        print("Para iniciar o frontend:")
        print("1. Navegue até o diretório frontend:")
        print("   cd frontend")
        print("2. Execute o servidor de desenvolvimento:")
        print("   npm run dev")
        print("3. Acesse o aplicativo em http://localhost:5173")
    else:
        print_header("Problemas encontrados")
        print("Não foi possível instalar as dependências do frontend.")
        print("Tente instalar manualmente:")
        print("1. Navegue até o diretório frontend:")
        print("   cd frontend")
        print("2. Instale as dependências:")
        print("   npm install")
    
    return 0 if deps_installed else 1

if __name__ == "__main__":
    sys.exit(main())
