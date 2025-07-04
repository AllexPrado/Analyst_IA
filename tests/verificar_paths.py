"""
Script para verificar se todos os caminhos necessários estão acessíveis e
se os arquivos de dados podem ser encontrados independente do diretório de trabalho.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Configurar o logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def verificar_diretorio(caminho, descricao):
    """Verifica se um diretório existe e é acessível"""
    path = Path(caminho)
    if path.exists() and path.is_dir():
        logger.info(f"✅ {descricao} encontrado: {path.absolute()}")
        return True
    else:
        logger.error(f"❌ {descricao} não encontrado: {path.absolute()}")
        return False

def verificar_arquivo(caminho, descricao):
    """Verifica se um arquivo existe e é acessível"""
    path = Path(caminho)
    if path.exists() and path.is_file():
        logger.info(f"✅ {descricao} encontrado: {path.absolute()}")
        return True
    else:
        logger.error(f"❌ {descricao} não encontrado: {path.absolute()}")
        return False

def encontrar_arquivo_dados(nome_arquivo):
    """Tenta encontrar um arquivo de dados em todos os locais possíveis"""
    possible_paths = [
        f"dados/{nome_arquivo}",
        f"backend/dados/{nome_arquivo}",
        f"../dados/{nome_arquivo}",
        f"../backend/dados/{nome_arquivo}"
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            logger.info(f"✅ Arquivo {nome_arquivo} encontrado em: {Path(path).absolute()}")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"  - Arquivo lido com sucesso, contém dados válidos")
                    return True
            except Exception as e:
                logger.error(f"  - Erro ao ler o arquivo: {e}")
    
    # Busca global
    root_dir = Path('.').resolve()
    for data_file in root_dir.glob(f'**/dados/{nome_arquivo}'):
        logger.info(f"✅ Arquivo {nome_arquivo} encontrado (busca global) em: {data_file}")
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"  - Arquivo lido com sucesso, contém dados válidos")
                return True
        except Exception as e:
            logger.error(f"  - Erro ao ler o arquivo: {e}")
    
    logger.error(f"❌ Arquivo {nome_arquivo} não encontrado em nenhum local esperado")
    return False

def main():
    """Função principal"""
    logger.info("=== VERIFICAÇÃO DE DIRETÓRIOS E ARQUIVOS ===")
    
    # Verificar diretórios principais
    backend_ok = verificar_diretorio("backend", "Diretório backend")
    frontend_ok = verificar_diretorio("frontend", "Diretório frontend")
    
    # Verificar diretórios de dados
    dados_raiz_ok = verificar_diretorio("dados", "Diretório de dados (raiz)")
    dados_backend_ok = verificar_diretorio("backend/dados", "Diretório de dados (backend)")
    
    # Verificar diretórios de endpoints
    endpoints_ok = verificar_diretorio("backend/endpoints", "Diretório de endpoints")
    
    # Verificar scripts principais
    main_ok = verificar_arquivo("backend/main.py", "Script main.py")
    start_backend_ok = verificar_arquivo("backend/start_with_endpoints.py", "Script start_with_endpoints.py")
    iniciar_sistema_ok = verificar_arquivo("iniciar_sistema.py", "Script iniciar_sistema.py")
    
    # Verificar arquivos de dados críticos
    logger.info("\n=== VERIFICAÇÃO DE ARQUIVOS DE DADOS ===")
    insights_ok = encontrar_arquivo_dados("insights.json")
    kpis_ok = encontrar_arquivo_dados("kpis.json")
    cobertura_ok = encontrar_arquivo_dados("cobertura.json")
    entidades_ok = encontrar_arquivo_dados("entidades.json")
    
    # Resumo final
    logger.info("\n=== RESUMO DA VERIFICAÇÃO ===")
    
    total = 0
    encontrados = 0
    
    def contar(condition, name):
        nonlocal total, encontrados
        total += 1
        if condition:
            encontrados += 1
        status = "✅" if condition else "❌"
        logger.info(f"{status} {name}")
    
    contar(backend_ok, "Diretório backend")
    contar(frontend_ok, "Diretório frontend") 
    contar(dados_raiz_ok or dados_backend_ok, "Diretório de dados")
    contar(endpoints_ok, "Diretório de endpoints")
    contar(main_ok, "Script main.py")
    contar(start_backend_ok, "Script start_with_endpoints.py")
    contar(iniciar_sistema_ok, "Script iniciar_sistema.py")
    contar(insights_ok, "Arquivo insights.json")
    contar(kpis_ok, "Arquivo kpis.json")
    contar(cobertura_ok, "Arquivo cobertura.json")
    contar(entidades_ok, "Arquivo entidades.json")
    
    logger.info(f"\nTotal encontrados: {encontrados}/{total} ({encontrados/total*100:.1f}%)")
    
    if encontrados == total:
        logger.info("✅ Todos os arquivos e diretórios foram encontrados! O sistema deve funcionar corretamente.")
        return 0
    else:
        logger.warning(f"⚠️ {total-encontrados} arquivos ou diretórios não foram encontrados.")
        if not dados_raiz_ok and dados_backend_ok:
            logger.info("ℹ️ Sugestão: Execute o script iniciar_sistema.py para copiar os dados para o diretório raiz.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
