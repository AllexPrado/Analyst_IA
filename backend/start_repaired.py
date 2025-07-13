"""
Script para iniciar o backend do Analyst IA com verificações completas.
Este script:
1. Verifica e instala dependências faltantes
2. Corrige problemas conhecidos
3. Inicia o servidor backend
"""
import sys
import os
import subprocess
import time
import logging
import importlib
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Diretório base
BASE_DIR = Path(__file__).parent.absolute()

def install_dependencies():
    """Instala dependências faltantes"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "requests",
        "markdown",
        "aiohttp"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            logger.info(f"✓ Dependência {package} já está instalada")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"✗ Dependência {package} não está instalada")
    
    if missing_packages:
        logger.info(f"Instalando {len(missing_packages)} dependências faltantes: {', '.join(missing_packages)}")
        
        try:
            subprocess.check_call([
                sys.executable, 
                "-m", "pip", 
                "install", 
                *missing_packages
            ])
            logger.info("✓ Dependências instaladas com sucesso")
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Erro ao instalar dependências: {e}")
            return False
    else:
        logger.info("✓ Todas as dependências estão instaladas")
    
    return True

def fix_check_and_fix_cache():
    """Verifica e corrige o módulo check_and_fix_cache.py"""
    file_path = BASE_DIR / "check_and_fix_cache.py"
    
    if not file_path.exists():
        logger.warning(f"✗ Arquivo {file_path} não existe, criando...")
        
        content = """
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def check_and_fix(cache_file=None):
    \"\"\"
    Verifica e corrige problemas no arquivo de cache.
    
    Args:
        cache_file (str, optional): Caminho para o arquivo de cache. Se None, usa o padrão.
        
    Returns:
        bool: True se o cache está OK ou foi corrigido, False se há problemas não corrigíveis.
    \"\"\"
    # Determinar o arquivo de cache
    if cache_file is None:
        base_dir = Path(__file__).parent
        cache_file = base_dir / "historico" / "cache_completo.json"
    else:
        cache_file = Path(cache_file)
    
    # Verificar se o arquivo existe
    if not cache_file.exists():
        logger.warning(f"Arquivo de cache não encontrado: {cache_file}")
        return False
    
    try:
        # Tentar carregar o cache
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Verificar estrutura básica
        if not isinstance(cache_data, dict):
            logger.warning("Cache não é um dicionário válido")
            return False
            
        # Verificar campos obrigatórios
        required_fields = ["timestamp", "entidades"]
        for field in required_fields:
            if field not in cache_data:
                logger.warning(f"Campo obrigatório '{field}' não encontrado no cache")
                return False
        
        # Verificar entidades
        entidades = cache_data.get("entidades", [])
        if not isinstance(entidades, list):
            logger.warning("Campo 'entidades' não é uma lista")
            return False
        
        for i, entidade in enumerate(entidades):
            if not isinstance(entidade, dict):
                logger.warning(f"Entidade {i} não é um dicionário")
                continue
            
            # Garantir que todas as entidades tenham um ID
            if "id" not in entidade:
                entidade["id"] = f"entity_{i}"
                logger.info(f"Adicionado ID para entidade {i}: {entidade['id']}")
            
            # Garantir que todas as entidades tenham um nome
            if "name" not in entidade:
                entidade["name"] = f"Entidade {i}"
                logger.info(f"Adicionado nome para entidade {i}: {entidade['name']}")
        
        # Salvar o cache corrigido
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Cache verificado e corrigido: {cache_file}")
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar/corrigir cache: {e}")
        return False

if __name__ == "__main__":
    # Configuração de logging quando executado diretamente
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    
    result = check_and_fix()
    if result:
        print("Cache verificado e corrigido com sucesso!")
    else:
        print("Não foi possível verificar/corrigir o cache.")
"""
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"✓ Arquivo {file_path} criado com sucesso")
        except Exception as e:
            logger.error(f"✗ Erro ao criar arquivo {file_path}: {e}")
            return False
    else:
        logger.info(f"✓ Arquivo {file_path} já existe")
    
    return True

def start_server(max_attempts=3):
    """Inicia o servidor backend"""
    logger.info("Iniciando servidor backend...")
    
    # Tentar diferentes scripts de inicialização
    start_scripts = [
        "start_with_endpoints.py",
        "start_simple.py", 
        "analyst_ia_start.py",
        "unified_backend.py",
        "main.py"
    ]
    
    for script_name in start_scripts:
        script_path = BASE_DIR / script_name
        
        if not script_path.exists():
            logger.warning(f"Script {script_name} não encontrado, tentando próximo...")
            continue
        
        logger.info(f"Tentando iniciar com {script_name}...")
        
        for attempt in range(1, max_attempts + 1):
            try:
                process = subprocess.Popen(
                    [sys.executable, str(script_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=BASE_DIR
                )
                
                # Aguardar um pouco para verificar se o servidor iniciou
                time.sleep(5)
                
                # Verificar se o processo ainda está em execução
                if process.poll() is None:
                    logger.info(f"✓ Servidor iniciado com sucesso usando {script_name}")
                    
                    # Executar teste de acessibilidade
                    test_script = BASE_DIR / "test_server_accessibility.py"
                    if test_script.exists():
                        logger.info("Testando acessibilidade do servidor...")
                        subprocess.run([sys.executable, str(test_script)], cwd=BASE_DIR)
                    
                    # Manter o processo em execução
                    logger.info("Servidor em execução. Pressione Ctrl+C para encerrar.")
                    try:
                        process.wait()
                    except KeyboardInterrupt:
                        process.terminate()
                        logger.info("Servidor encerrado pelo usuário")
                    
                    return True
                else:
                    stdout, stderr = process.communicate()
                    logger.warning(f"✗ Servidor encerrou imediatamente com {script_name} (tentativa {attempt}/{max_attempts})")
                    logger.warning(f"ERRO: {stderr.decode('utf-8')[:500]}")
                    
                    if attempt < max_attempts:
                        logger.info(f"Aguardando 2 segundos antes da próxima tentativa...")
                        time.sleep(2)
            except Exception as e:
                logger.error(f"✗ Erro ao iniciar servidor com {script_name}: {e}")
                if attempt < max_attempts:
                    logger.info(f"Aguardando 2 segundos antes da próxima tentativa...")
                    time.sleep(2)
    
    logger.error("✗ Não foi possível iniciar o servidor com nenhum dos scripts disponíveis")
    return False

def main():
    """Função principal"""
    logger.info("=" * 80)
    logger.info("INICIANDO ANALYST IA - SCRIPT DE VERIFICAÇÃO E REPARO COMPLETO")
    logger.info("=" * 80)
    
    # Instalar dependências
    if not install_dependencies():
        logger.error("✗ Falha ao instalar dependências. Abortando.")
        return False
    
    # Verificar e corrigir módulos problemáticos
    if not fix_check_and_fix_cache():
        logger.warning("⚠️ Falha ao verificar/corrigir o módulo check_and_fix_cache.py")
        # Continuar mesmo com falha
    
    # Iniciar o servidor
    if not start_server():
        logger.error("✗ Falha ao iniciar o servidor. Abortando.")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operação interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Erro não tratado: {e}")
        sys.exit(1)
