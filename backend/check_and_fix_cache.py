"""
Módulo para verificação e reparo do cache.
Este módulo verifica a integridade do cache e corrige problemas encontrados.
"""

import os
import sys
import json
import logging
import traceback
import time
from pathlib import Path
from typing import Dict, Any, List, Union

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_cache_path() -> str:
    """
    Obtém o caminho para o arquivo principal de cache.
    
    Returns:
        str: Caminho para o arquivo de cache
    """
    # Primeiro verificar se existe cache.json na pasta atual
    if os.path.exists("cache.json"):
        return "cache.json"
    
    # Verificar caminho comum para arquivos de cache
    if os.path.exists("historico/cache_completo.json"):
        return "historico/cache_completo.json"
    
    # Verificar na pasta cache
    if os.path.exists("cache/cache.json"):
        return "cache/cache.json"
    
    # Retornar o padrão mesmo que não exista
    return "cache.json"

def load_cache(cache_path: str) -> Dict[str, Any]:
    """
    Carrega o cache do disco.
    
    Args:
        cache_path (str): Caminho para o arquivo de cache
        
    Returns:
        Dict[str, Any]: Conteúdo do cache ou dicionário vazio se falhar
    """
    if not os.path.exists(cache_path):
        logger.warning(f"Arquivo de cache não encontrado: {cache_path}")
        return {}
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        logger.info(f"Cache carregado com sucesso: {cache_path}")
        return cache_data
    
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON do cache: {cache_path}")
        
        # Tentar fazer um backup do arquivo corrompido
        backup_path = f"{cache_path}.corrupted.{int(time.time())}"
        try:
            import shutil
            shutil.copy2(cache_path, backup_path)
            logger.info(f"Backup do cache corrompido criado: {backup_path}")
        except:
            logger.error(f"Não foi possível criar backup do cache corrompido")
        
        return {}
    
    except Exception as e:
        logger.error(f"Erro desconhecido ao carregar cache: {str(e)}")
        return {}

def save_cache(cache_data: Dict[str, Any], cache_path: str) -> bool:
    """
    Salva o cache no disco.
    
    Args:
        cache_data (Dict[str, Any]): Dados do cache
        cache_path (str): Caminho para o arquivo de cache
        
    Returns:
        bool: True se sucesso, False se falha
    """
    try:
        # Garantir que o diretório exista
        os.makedirs(os.path.dirname(cache_path) or '.', exist_ok=True)
        
        # Salvar o cache com formatação bonita
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Cache salvo com sucesso: {cache_path}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao salvar cache: {str(e)}")
        return False

def check_cache_integrity(cache_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verifica a integridade do cache.
    
    Args:
        cache_data (Dict[str, Any]): Dados do cache
        
    Returns:
        Dict[str, Any]: Resultado da verificação
    """
    issues = {}
    
    # Verificar a estrutura básica do cache
    if not isinstance(cache_data, dict):
        issues["invalid_format"] = {
            "description": "Formato inválido de cache",
            "severity": "high",
            "fixable": False
        }
        return {
            "valid": False,
            "issues": issues
        }
    
    # Verificar se tem campo de timestamp
    if "timestamp" not in cache_data:
        issues["missing_timestamp"] = {
            "description": "Campo de timestamp ausente",
            "severity": "medium",
            "fixable": True
        }
    
    # Verificar se tem dados de entidades
    if "entities" not in cache_data:
        issues["missing_entities"] = {
            "description": "Campo de entidades ausente",
            "severity": "high",
            "fixable": True
        }
    elif not isinstance(cache_data["entities"], list) and not isinstance(cache_data["entities"], dict):
        issues["invalid_entities"] = {
            "description": "Campo de entidades com formato inválido",
            "severity": "high",
            "fixable": False
        }
    
    # Verificar se tem entidades vazias ou inválidas
    if "entities" in cache_data and isinstance(cache_data["entities"], list):
        empty_entities = []
        invalid_entities = []
        
        for i, entity in enumerate(cache_data["entities"]):
            if not entity:
                empty_entities.append(i)
            elif not isinstance(entity, dict):
                invalid_entities.append(i)
            elif "name" not in entity or "guid" not in entity:
                invalid_entities.append(i)
        
        if empty_entities:
            issues["empty_entities"] = {
                "description": f"Entidades vazias encontradas: {len(empty_entities)}",
                "positions": empty_entities,
                "severity": "medium",
                "fixable": True
            }
            
        if invalid_entities:
            issues["invalid_entity_format"] = {
                "description": f"Entidades com formato inválido: {len(invalid_entities)}",
                "positions": invalid_entities,
                "severity": "medium",
                "fixable": True
            }
    
    # Verificar se o cache está vazio
    if len(cache_data) == 0 or (len(cache_data) == 1 and "timestamp" in cache_data):
        issues["empty_cache"] = {
            "description": "Cache está vazio",
            "severity": "high",
            "fixable": False
        }
    
    return {
        "valid": len(issues) == 0,
        "issues": issues
    }

def fix_cache_issues(cache_data: Dict[str, Any], issues: Dict[str, Any]) -> Dict[str, Any]:
    """
    Corrige problemas no cache.
    
    Args:
        cache_data (Dict[str, Any]): Dados do cache
        issues (Dict[str, Any]): Problemas identificados
        
    Returns:
        Dict[str, Any]: Cache corrigido e resultado das correções
    """
    fixed = {}
    
    # Adicionar timestamp se ausente
    if "missing_timestamp" in issues:
        cache_data["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S.%f")
        fixed["missing_timestamp"] = {
            "fixed": True,
            "description": "Timestamp adicionado"
        }
    
    # Adicionar entities se ausente
    if "missing_entities" in issues:
        cache_data["entities"] = []
        fixed["missing_entities"] = {
            "fixed": True,
            "description": "Campo entities vazio adicionado"
        }
    
    # Remover entidades vazias
    if "empty_entities" in issues and "entities" in cache_data and isinstance(cache_data["entities"], list):
        positions = sorted(issues["empty_entities"]["positions"], reverse=True)
        for pos in positions:
            if 0 <= pos < len(cache_data["entities"]):
                del cache_data["entities"][pos]
        
        fixed["empty_entities"] = {
            "fixed": True,
            "description": f"Removidas {len(positions)} entidades vazias"
        }
    
    # Remover entidades inválidas
    if "invalid_entity_format" in issues and "entities" in cache_data and isinstance(cache_data["entities"], list):
        positions = sorted(issues["invalid_entity_format"]["positions"], reverse=True)
        for pos in positions:
            if 0 <= pos < len(cache_data["entities"]):
                del cache_data["entities"][pos]
        
        fixed["invalid_entity_format"] = {
            "fixed": True,
            "description": f"Removidas {len(positions)} entidades inválidas"
        }
    
    # Marcar problemas não corrigidos
    for issue_key, issue in issues.items():
        if issue_key not in fixed and issue["fixable"]:
            fixed[issue_key] = {
                "fixed": False,
                "description": f"Não foi possível corrigir: {issue['description']}"
            }
    
    return {
        "cache_data": cache_data,
        "fixed": fixed
    }

def check_and_fix() -> Dict[str, Any]:
    """
    Verifica e corrige o cache.
    
    Returns:
        Dict[str, Any]: Resultado da operação
    """
    logger.info("Iniciando verificação e reparo do cache")
    
    try:
        # Obter caminho do cache
        cache_path = get_cache_path()
        logger.info(f"Usando arquivo de cache: {cache_path}")
        
        # Carregar cache
        cache_data = load_cache(cache_path)
        
        # Se o cache estiver vazio, tentar localizar um backup
        if not cache_data:
            logger.warning("Cache vazio ou corrompido, procurando por backups")
            
            # Procurar backups na pasta historico
            backup_dir = "historico"
            if os.path.exists(backup_dir):
                backup_files = sorted(
                    [f for f in os.listdir(backup_dir) if f.startswith("cache") and f.endswith(".json")],
                    key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)),
                    reverse=True
                )
                
                # Tentar carregar do backup mais recente
                for backup_file in backup_files:
                    backup_path = os.path.join(backup_dir, backup_file)
                    logger.info(f"Tentando carregar do backup: {backup_path}")
                    backup_data = load_cache(backup_path)
                    
                    if backup_data:
                        cache_data = backup_data
                        logger.info(f"Cache carregado do backup: {backup_path}")
                        break
        
        # Verificar integridade
        integrity_result = check_cache_integrity(cache_data)
        
        # Se houver problemas, tentar corrigir
        if not integrity_result["valid"]:
            logger.warning(f"Problemas encontrados no cache: {len(integrity_result['issues'])}")
            
            # Tentar corrigir problemas
            fix_result = fix_cache_issues(cache_data, integrity_result["issues"])
            fixed_cache = fix_result["cache_data"]
            
            # Salvar cache corrigido
            if save_cache(fixed_cache, cache_path):
                logger.info("Cache corrigido salvo com sucesso")
                
                # Verificar integridade novamente após correções
                new_integrity = check_cache_integrity(fixed_cache)
                
                return {
                    "success": new_integrity["valid"],
                    "issues_found": len(integrity_result["issues"]),
                    "issues_fixed": sum(1 for fix in fix_result["fixed"].values() if fix["fixed"]),
                    "issues": integrity_result["issues"],
                    "fixes": fix_result["fixed"],
                    "still_has_issues": not new_integrity["valid"],
                    "remaining_issues": new_integrity["issues"] if not new_integrity["valid"] else {}
                }
            else:
                logger.error("Falha ao salvar cache corrigido")
                return {
                    "success": False,
                    "error": "Falha ao salvar cache corrigido",
                    "issues_found": len(integrity_result["issues"]),
                    "issues": integrity_result["issues"]
                }
        else:
            logger.info("Cache íntegro, nenhuma correção necessária")
            return {
                "success": True,
                "issues_found": 0,
                "message": "Cache íntegro, nenhuma correção necessária"
            }
    
    except Exception as e:
        logger.error(f"Erro ao verificar/corrigir cache: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    result = check_and_fix()
    print(json.dumps(result, indent=2))
