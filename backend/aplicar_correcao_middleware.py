#!/usr/bin/env python
"""
Script para corrigir o problema dos endpoints /agno
Este script modifica o main.py para adicionar um middleware
que redireciona /agno para /api/agno
"""
import os
import sys
import re

def criar_diretorio_middleware():
    """Cria o diretório middleware se não existir"""
    middleware_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'middleware')
    if not os.path.exists(middleware_dir):
        print(f"Criando diretório middleware...")
        os.makedirs(middleware_dir)
    
    # Criar arquivo __init__.py no diretório middleware
    init_file = os.path.join(middleware_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# Pacote middleware\n')
        print(f"Arquivo {init_file} criado.")

def corrigir_main_py():
    """Adiciona o middleware no arquivo main.py"""
    main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
    
    print(f"Lendo {main_py}...")
    with open(main_py, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se o middleware já está importado
    if "from middleware.agno_proxy import add_agno_middleware" in content:
        print("O middleware já está importado no main.py.")
    else:
        # Adicionar a importação do middleware
        import_pattern = r"from fastapi import FastAPI.*"
        import_replacement = r"\g<0>\nfrom middleware.agno_proxy import add_agno_middleware"
        content = re.sub(import_pattern, import_replacement, content)
        
        # Adicionar a chamada do middleware após a criação do app
        app_pattern = r"app = FastAPI\(.*?\)"
        app_replacement = r"\g<0>\n\n# Adicionar middleware para redirecionar /agno para /api/agno\napp = add_agno_middleware(app)"
        content = re.sub(app_pattern, app_replacement, content, flags=re.DOTALL)
        
        print("Gravando alterações em main.py...")
        with open(main_py, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Middleware adicionado em main.py")
    
    return True

def main():
    print("=== CORREÇÃO DE ENDPOINTS /agno ===")
    
    # Passo 1: Criar diretório middleware
    criar_diretorio_middleware()
    
    # Passo 2: Corrigir main.py
    if corrigir_main_py():
        print("\n✅ Correção aplicada com sucesso!")
        print("\nPara aplicar as alterações:")
        print("1. Reinicie o servidor FastAPI:")
        print("   python -m uvicorn main:app --reload")
        print("\n2. Teste o endpoint com:")
        print("   python teste_curl.py")
        
        return 0
    
    print("\n❌ Falha ao aplicar a correção.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
