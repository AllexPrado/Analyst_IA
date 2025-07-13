"""
Script para detectar e corrigir erros de sintaxe em arquivos Python.
Este script analisa todos os arquivos .py no diretório backend e reporta erros de sintaxe.
"""
import os
import sys
import ast
import re
import logging
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def check_syntax_errors(file_path):
    """
    Verifica se um arquivo Python contém erros de sintaxe.
    
    Args:
        file_path (str): Caminho para o arquivo Python
        
    Returns:
        tuple: (tem_erro, mensagem_erro)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
            
        # Tentar compilar o código para detectar erros de sintaxe
        ast.parse(source_code)
        return False, None
    except SyntaxError as e:
        error_msg = f"Linha {e.lineno}, coluna {e.offset}: {e.msg}"
        
        # Tentar obter a linha específica
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if e.lineno <= len(lines):
                    line_content = lines[e.lineno - 1].rstrip()
                    error_msg += f"\n{line_content}"
                    if e.offset:
                        error_msg += f"\n{' ' * (e.offset - 1)}^"
        except Exception:
            pass
            
        return True, error_msg
    except Exception as e:
        return True, str(e)

def fix_common_syntax_errors(file_path):
    """
    Tenta corrigir erros comuns de sintaxe em um arquivo Python.
    
    Args:
        file_path (str): Caminho para o arquivo Python
        
    Returns:
        bool: True se alterações foram feitas, False caso contrário
    """
    fixed = False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        new_lines = []
        for i, line in enumerate(lines):
            # Corrigir string literais com problemas de aspas
            if re.search(r'["\'].*["\'].*["\']', line):
                # Linha potencialmente problemática com aspas
                fixed_line = line
                
                # Corrigir padrão comum de erro: if char in '"' sem escape
                fixed_line = re.sub(
                    r"if\s+char\s+in\s+['\"][\"\']['\"]",
                    "if char in '\"'",
                    fixed_line
                )
                
                # Corrigir outros padrões de aspas sem escape
                fixed_line = re.sub(
                    r"(['\"])([\"'])(['\"])",
                    r"\1\\\2\3",
                    fixed_line
                )
                
                if fixed_line != line:
                    logger.info(f"Corrigindo linha {i+1} com problemas de aspas")
                    logger.info(f"Original: {line.strip()}")
                    logger.info(f"Corrigida: {fixed_line.strip()}")
                    line = fixed_line
                    fixed = True
            
            # Adicionar a linha (original ou corrigida) ao resultado
            new_lines.append(line)
        
        if fixed:
            # Salvar alterações
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            logger.info(f"Arquivo corrigido: {file_path}")
    except Exception as e:
        logger.error(f"Erro ao tentar corrigir {file_path}: {e}")
        return False
        
    return fixed

def scan_directory_for_errors(directory):
    """
    Escaneia um diretório em busca de erros de sintaxe em arquivos Python.
    
    Args:
        directory (str): Caminho para o diretório a ser escaneado
        
    Returns:
        dict: Dicionário com resultados do scan
    """
    results = {
        "total_files": 0,
        "error_files": 0,
        "fixed_files": 0,
        "errors": []
    }
    
    # Converter para Path se for string
    if isinstance(directory, str):
        directory = Path(directory)
    
    # Encontrar todos os arquivos Python
    python_files = list(directory.glob("**/*.py"))
    results["total_files"] = len(python_files)
    
    logger.info(f"Escaneando {len(python_files)} arquivos Python em {directory}")
    
    # Analisar cada arquivo
    for file_path in python_files:
        has_error, error_msg = check_syntax_errors(file_path)
        
        if has_error:
            results["error_files"] += 1
            error_entry = {
                "file": str(file_path),
                "error": error_msg,
                "fixed": False
            }
            
            # Tentar corrigir erros comuns
            if fix_common_syntax_errors(file_path):
                # Verificar se a correção resolveu o problema
                has_error_after_fix, _ = check_syntax_errors(file_path)
                if not has_error_after_fix:
                    error_entry["fixed"] = True
                    results["fixed_files"] += 1
                    logger.info(f"✅ Arquivo corrigido com sucesso: {file_path}")
                else:
                    logger.warning(f"⚠️ Tentativa de correção não resolveu todos os erros: {file_path}")
            
            results["errors"].append(error_entry)
            logger.error(f"❌ Erro de sintaxe em {file_path}: {error_msg}")
    
    return results

def main():
    """Função principal"""
    logger.info("=" * 80)
    logger.info("ESCANEANDO ARQUIVOS PYTHON EM BUSCA DE ERROS DE SINTAXE")
    logger.info("=" * 80)
    
    # Determinar o diretório base
    base_dir = Path(__file__).parent.absolute()
    
    # Escanear o diretório
    results = scan_directory_for_errors(base_dir)
    
    # Exibir resumo
    logger.info("\n--- RESUMO DO SCAN ---")
    logger.info(f"Total de arquivos escaneados: {results['total_files']}")
    logger.info(f"Arquivos com erros: {results['error_files']}")
    logger.info(f"Arquivos corrigidos: {results['fixed_files']}")
    
    if results["errors"]:
        logger.info("\n--- DETALHES DOS ERROS ---")
        for i, error in enumerate(results["errors"], 1):
            status = "✅ CORRIGIDO" if error["fixed"] else "❌ NÃO CORRIGIDO"
            logger.info(f"{i}. {error['file']} - {status}")
            if not error["fixed"]:
                logger.info(f"   Erro: {error['error']}")
    
    logger.info("=" * 80)
    
    # Retornar True se não há erros ou todos foram corrigidos
    return results["error_files"] == results["fixed_files"]

if __name__ == "__main__":
    try:
        success = main()
        if success:
            logger.info("✅ Todos os erros de sintaxe foram corrigidos!")
            sys.exit(0)
        else:
            logger.warning("⚠️ Ainda existem erros de sintaxe não corrigidos.")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operação interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Erro não tratado: {e}")
        sys.exit(1)
