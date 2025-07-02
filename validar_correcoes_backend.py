#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para validar as correções implementadas no backend do Analyst_IA
"""

import os
import sys
import json
import importlib
import traceback
from pathlib import Path

def print_header(title):
    """Imprime um cabeçalho formatado"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def check_imports(module_name):
    """Verifica se um módulo pode ser importado corretamente"""
    try:
        module = importlib.import_module(module_name)
        print(f"✅ Módulo '{module_name}' importado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao importar módulo '{module_name}': {e}")
        return False

def check_endpoint_imports():
    """Verifica se todos os endpoints podem ser importados corretamente"""
    print_header("VERIFICAÇÃO DE IMPORTAÇÃO DE ENDPOINTS")
    
    endpoint_modules = [
        "endpoints.chat_endpoints",
        "endpoints.kpis_endpoints",
        "endpoints.tendencias_endpoints",
        "endpoints.cobertura_endpoints",
        "endpoints.insights_endpoints"
    ]
    
    success_count = 0
    for module_name in endpoint_modules:
        if check_imports(module_name):
            success_count += 1
    
    print(f"\n{success_count}/{len(endpoint_modules)} módulos de endpoints importados com sucesso")
    return success_count == len(endpoint_modules)

def check_utils_imports():
    """Verifica se todos os módulos de utilidades podem ser importados corretamente"""
    print_header("VERIFICAÇÃO DE IMPORTAÇÃO DE UTILITÁRIOS")
    
    util_modules = [
        "utils.cache",
        "utils.cache_initializer",
        "utils.cache_advanced",
        "utils.cache_collector",
        "utils.cache_integration",
        "utils.data_loader",
        "utils.entity_processor"
    ]
    
    success_count = 0
    for module_name in util_modules:
        if check_imports(module_name):
            success_count += 1
    
    print(f"\n{success_count}/{len(util_modules)} módulos de utilidades importados com sucesso")
    return success_count == len(util_modules)

def check_cache_files():
    """Verifica se os arquivos de cache existem e têm dados válidos"""
    print_header("VERIFICAÇÃO DE ARQUIVOS DE CACHE")
    
    cache_files = [
        ("historico/cache_completo.json", "Cache principal"),
        ("dados/kpis.json", "KPIs"),
        ("dados/tendencias.json", "Tendências"),
        ("dados/cobertura.json", "Cobertura"),
        ("dados/insights.json", "Insights"),
        ("dados/status.json", "Status"),
        ("dados/resumo-geral.json", "Resumo Geral")
    ]
    
    backend_dir = Path(__file__).parent / "backend"
    if not backend_dir.exists():
        backend_dir = Path(__file__).parent
    
    success_count = 0
    for filename, description in cache_files:
        file_path = backend_dir / filename
        if not file_path.exists():
            print(f"❌ Arquivo '{filename}' ({description}) não encontrado")
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and len(data) > 0:
                print(f"✅ Arquivo '{filename}' ({description}) contém dados válidos")
                print(f"   Tamanho: {file_path.stat().st_size / 1024:.2f} KB")
                if "entidades" in data:
                    print(f"   Entidades: {len(data['entidades'])}")
                success_count += 1
            else:
                print(f"❌ Arquivo '{filename}' ({description}) não contém dados válidos")
        except Exception as e:
            print(f"❌ Erro ao ler arquivo '{filename}' ({description}): {e}")
    
    print(f"\n{success_count}/{len(cache_files)} arquivos de cache verificados com sucesso")
    return success_count == len(cache_files)

def check_code_duplications():
    """Verifica se há duplicações de código críticas nos arquivos"""
    print_header("VERIFICAÇÃO DE DUPLICAÇÃO DE CÓDIGO")
    
    # Verificar duplicação na classe ChatInput
    chat_endpoint_path = Path(__file__).parent / "backend" / "endpoints" / "chat_endpoints.py"
    if not chat_endpoint_path.exists():
        chat_endpoint_path = Path(__file__).parent / "endpoints" / "chat_endpoints.py"
    
    if not chat_endpoint_path.exists():
        print(f"❌ Arquivo chat_endpoints.py não encontrado")
        return False
    
    try:
        with open(chat_endpoint_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Verificar duplicação de classe ChatInput
        chat_input_count = content.count("class ChatInput")
        if chat_input_count > 1:
            print(f"❌ Encontradas {chat_input_count} definições da classe ChatInput (deveria ser 1)")
            return False
            
        # Verificar duplicação de router.post("/chat")
        chat_route_count = content.count('@router.post("/chat")')
        if chat_route_count > 1:
            print(f"❌ Encontradas {chat_route_count} definições da rota /chat (deveria ser 1)")
            return False
            
        print("✅ Não foram encontradas duplicações críticas no código")
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar duplicações: {e}")
        return False

def run_validation():
    """Função principal que executa todas as validações"""
    print_header("VALIDAÇÃO DE CORREÇÕES DO BACKEND")
    
    # Adicionar diretórios ao path para importação
    backend_dir = Path(__file__).parent / "backend"
    if backend_dir.exists():
        sys.path.insert(0, str(backend_dir))
    
    # Executar as validações
    tests = [
        ("Importação de endpoints", check_endpoint_imports),
        ("Importação de utilitários", check_utils_imports),
        ("Arquivos de cache", check_cache_files),
        ("Duplicações de código", check_code_duplications)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n>> Executando teste: {name}")
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Erro não tratado: {e}")
            traceback.print_exc()
            results.append((name, False))
    
    # Mostrar resumo dos resultados
    print_header("RESUMO DOS RESULTADOS")
    
    success_count = sum(1 for _, success in results if success)
    for name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status}: {name}")
    
    print(f"\n{success_count}/{len(tests)} testes passaram com sucesso")
    
    if success_count == len(tests):
        print("\n✅ TODAS AS CORREÇÕES FORAM VALIDADAS COM SUCESSO!")
        return 0
    else:
        print(f"\n❌ {len(tests) - success_count} validações falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(run_validation())
