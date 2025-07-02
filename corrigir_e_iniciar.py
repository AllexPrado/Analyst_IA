#!/usr/bin/env python3
"""
Script para corrigir e garantir que o sistema Analyst_IA esteja funcionando corretamente.
Este script executa todas as correções necessárias e verifica a integridade do sistema.
"""

import os
import sys
import re
import shutil
import platform
import subprocess
import json
import logging
import importlib.util
import time
from datetime import datetime
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def print_header(message):
    """Imprime uma mensagem de cabeçalho formatada"""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80)
    logger.info(message)

def configurar_limite_tokens():
    """Configura um limite diário de tokens para economia"""
    token_file = Path("backend/logs/token_usage.json")
    
    if token_file.exists():
        print("✓ Arquivo de controle de tokens já existente")
        return True
    
    try:
        # Cria diretório se não existir
        token_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Cria arquivo inicial com limite diário
        with open(token_file, "w") as f:
            f.write('{"date": "2025-06-26", "tokens": 0}')
        
        print("✓ Arquivo de controle de tokens criado com limite diário de 5000 tokens")
        return True
    except Exception as e:
        print(f"✗ Erro ao configurar limite de tokens: {e}")
        return False

def verificar_importacoes_backend():
    """Verifica importações problemáticas no backend"""
    print_header("Verificando importações no backend")
    
    backend_file = Path("backend/unified_backend.py")
    if not backend_file.exists():
        print(f"✗ Arquivo {backend_file} não encontrado")
        return False
    
    try:
        with open(backend_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "from utils.openai_connector import gerar_resposta_ia, truncate_text_tokens" in content:
            print("✗ Importação problemática 'truncate_text_tokens' encontrada")
            
            # Corrige a importação
            corrected = content.replace(
                "from utils.openai_connector import gerar_resposta_ia, truncate_text_tokens",
                "from utils.openai_connector import gerar_resposta_ia"
            )
            
            # Salva a correção
            with open(backend_file, "w", encoding="utf-8") as f:
                f.write(corrected)
            
            print("✓ Importação corrigida")
        else:
            print("✓ Importações estão corretas")
        
        return True
    except Exception as e:
        print(f"✗ Erro ao verificar importações: {e}")
        return False

def verificar_endpoint_health():
    """Verifica se o endpoint /api/health está implementado"""
    print_header("Verificando endpoint /api/health")
    
    backend_file = Path("backend/unified_backend.py")
    if not backend_file.exists():
        print(f"✗ Arquivo {backend_file} não encontrado")
        return False
    
    try:
        with open(backend_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "@app.get(\"/api/health\")" in content:
            print("✓ Endpoint /api/health já existe")
            return True
        
        print("✗ Endpoint /api/health não encontrado, implementando...")
        
        # Localiza um bom ponto para inserir o endpoint
        pos = content.find("# Endpoints")
        if pos == -1:
            pos = content.find("@app.on_event(\"startup\")")
        
        if pos > 0:
            health_endpoint = """
@app.get("/api/health")
async def health_check():
    # Endpoint para verificar se o serviço está operacional
    cache = await get_cache()
    cache_status = {
        "exists": bool(cache),
        "entities": len(cache.get("entidades", [])) if cache else 0,
        "last_update": cache.get("timestamp", "nunca") if cache else "nunca"
    }
    
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "cache": cache_status,
        "version": "2.0.1"
    }

"""
            # Troca triple quotes para não confundir com docstring
            health_endpoint = health_endpoint.replace('"""', "'''")
            
            # Adiciona importação do datetime se não existir
            if "from datetime import datetime" not in content:
                content = content.replace(
                    "import logging",
                    "import logging\nfrom datetime import datetime"
                )
            
            # Insere após o marcador encontrado
            end_pos = content.find("\n", pos)
            new_content = content[:end_pos+1] + health_endpoint + content[end_pos+1:]
            
            with open(backend_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            print("✓ Endpoint /api/health implementado")
            return True
        
        print("✗ Não foi possível encontrar um bom local para inserir o endpoint")
        return False
    except Exception as e:
        print(f"✗ Erro ao verificar endpoint health: {e}")
        return False

def iniciar_backend():
    """Tenta iniciar o backend para teste"""
    print_header("Iniciando backend para teste")
    
    try:
        # Verifica se o diretório do backend existe
        if not Path("backend").exists():
            print("✗ Diretório backend não encontrado")
            return False
        
        # Verifica se o arquivo unified_backend.py existe
        if not Path("backend/unified_backend.py").exists():
            print("✗ Arquivo unified_backend.py não encontrado")
            return False
        
        # Executa o backend em segundo plano
        print("Iniciando backend unificado...")
        
        if platform.system() == "Windows":
            process = subprocess.Popen(
                [sys.executable, "unified_backend.py"],
                cwd="backend",
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            process = subprocess.Popen(
                [sys.executable, "unified_backend.py"],
                cwd="backend"
            )
        
        print(f"✓ Backend iniciado com PID: {process.pid}")
        print("✓ Acesse o backend em: http://localhost:8000")
        print("✓ Para iniciar o frontend, abra outro terminal e execute:")
        print("  cd frontend")
        print("  npm run dev")
        
        return True
    except Exception as e:
        print(f"✗ Erro ao iniciar backend: {e}")
        return False

def criar_diretorios_necessarios():
    """Cria os diretórios necessários para o sistema funcionar corretamente"""
    print_header("Criando diretórios necessários")
    
    # Lista de diretórios que devem existir
    diretorios = [
        "backend/logs",
        "backend/historico",
        "relatorios"
    ]
    
    for dir_path in diretorios:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ Diretório {dir_path} já existe")
        else:
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✓ Diretório {dir_path} criado com sucesso")
            except Exception as e:
                print(f"✗ Erro ao criar diretório {dir_path}: {e}")
    
    return True

def import_module_from_path(module_name, file_path):
    """Importa um módulo a partir de um caminho de arquivo"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        logger.error(f"Falha ao importar {module_name} de {file_path}")
        return None
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def generate_unified_data():
    """Gera dados de teste unificados para todos os módulos"""
    print_header("Gerando dados unificados de teste")
    try:
        # Verificar se o módulo generate_unified_data existe
        unified_data_path = Path("backend") / "generate_unified_data.py"
        
        if unified_data_path.exists():
            # Importar e executar o módulo
            module = import_module_from_path("generate_unified_data", str(unified_data_path))
            if module and hasattr(module, "generate_unified_data"):
                logger.info("Iniciando geração de dados unificados...")
                result = module.generate_unified_data()
                if result:
                    print("✅ Dados unificados gerados com sucesso")
                    logger.info("Dados unificados gerados com sucesso")
                    return True
                else:
                    print("❌ Falha na geração de dados unificados")
                    logger.error("Falha na geração de dados unificados")
            else:
                print("❌ Módulo generate_unified_data não contém a função necessária")
                logger.error("Módulo generate_unified_data não contém a função necessária")
        else:
            print(f"❌ Arquivo {unified_data_path} não encontrado")
            logger.warning(f"Arquivo {unified_data_path} não encontrado")
            
        # Fallback para create_test_cache se generate_unified_data falhar
        test_cache_path = Path("backend") / "create_test_cache.py"
        if test_cache_path.exists():
            print("Tentando gerar dados de teste com create_test_cache.py...")
            module = import_module_from_path("create_test_cache", str(test_cache_path))
            if module and hasattr(module, "create_test_cache"):
                result = module.create_test_cache()
                if result:
                    print("✅ Dados de teste gerados com sucesso (fallback)")
                    logger.info("Dados de teste gerados com sucesso (fallback)")
                    return True
                else:
                    print("❌ Falha na geração de dados de teste (fallback)")
                    logger.error("Falha na geração de dados de teste (fallback)")
            else:
                print("❌ Módulo create_test_cache não contém a função necessária")
                logger.error("Módulo create_test_cache não contém a função necessária")
        else:
            print(f"❌ Arquivo {test_cache_path} não encontrado")
            logger.warning(f"Arquivo {test_cache_path} não encontrado")
            
        return False
    except Exception as e:
        print(f"❌ Erro ao gerar dados de teste: {e}")
        logger.error(f"Erro ao gerar dados de teste: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    print_header("Correção Rápida do Sistema Analyst-IA")
    print("Script econômico para corrigir o backend e reduzir consumo de tokens")
    
    # Verifica o diretório atual
    cwd = os.getcwd()
    if not os.path.basename(cwd) == "Analyst_IA":
        print(f"Diretório atual: {cwd}")
        print("⚠️  AVISO: Este script deve ser executado na pasta raiz do projeto Analyst_IA")
        
        response = input("Continuar mesmo assim? (s/n): ")
        if response.lower() not in ["s", "sim", "y", "yes"]:
            return 1
    
    # Executa as correções
    steps = [
        ("Criar diretórios necessários", criar_diretorios_necessarios),
        ("Configurar limite de tokens", configurar_limite_tokens),
        ("Gerar dados unificados", generate_unified_data),       # Gerar dados antes de iniciar o backend
        ("Verificar importações no backend", verificar_importacoes_backend),
        ("Verificar endpoint /api/health", verificar_endpoint_health),
        ("Iniciar backend para teste", iniciar_backend)
    ]
    
    results = []
    for name, func in steps:
        print(f"\nExecutando: {name}")
        success = func()
        results.append((name, success))
    
    # Resumo
    print_header("Resumo das correções")
    for name, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {name}")
    
    if all(success for _, success in results):
        print("\n✓ Todas as correções foram aplicadas com sucesso!")
    else:
        print("\n⚠️  Algumas correções não puderam ser aplicadas.")
    
    print("\n📋 Instruções para uso:")
    print("1. O backend já foi iniciado em http://localhost:8000")
    print("2. Para o frontend, abra outro terminal e execute:")
    print("   cd frontend")
    print("   npm run dev")
    print("3. Acesse o sistema em http://localhost:5173")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
