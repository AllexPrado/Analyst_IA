"""
Script para corrigir erros no backend e restaurar a funcionalidade.
Este script corrige os problemas identificados e reinicia o backend.
"""

import os
import sys
import subprocess
import logging
import time
import importlib.util

# Configuração de logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("logs/repair_backend.log"),
                        logging.StreamHandler(sys.stdout)
                    ])
logger = logging.getLogger(__name__)

def check_script_exists(script_name):
    """
    Verifica se um script Python existe.
    
    Args:
        script_name (str): Nome do script (com ou sem extensão .py)
        
    Returns:
        bool: True se o script existe, False caso contrário
    """
    if not script_name.endswith('.py'):
        script_name = f"{script_name}.py"
    
    return os.path.exists(script_name)

def run_python_script(script_name):
    """
    Executa um script Python.
    
    Args:
        script_name (str): Nome do script (com ou sem extensão .py)
        
    Returns:
        bool: True se executado com sucesso, False caso contrário
    """
    if not script_name.endswith('.py'):
        script_name = f"{script_name}.py"
    
    if not os.path.exists(script_name):
        logger.error(f"Script não encontrado: {script_name}")
        return False
    
    try:
        logger.info(f"Executando script: {script_name}")
        result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Script {script_name} executado com sucesso")
            if result.stdout:
                logger.info(f"Saída: {result.stdout[:500]}...")
            return True
        else:
            logger.error(f"Erro ao executar {script_name}: {result.returncode}")
            logger.error(f"Saída de erro: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Exceção ao executar {script_name}: {str(e)}")
        return False

def fix_regex_errors():
    """
    Corrige erros nas expressões regulares.
    
    Returns:
        bool: True se corrigido com sucesso, False caso contrário
    """
    file_path = "core_inteligente/agent_tools.py"
    
    if not os.path.exists(file_path):
        logger.error(f"Arquivo não encontrado: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Corrigir expressões regulares
        fixes = [
            (r'position (\d+), unexpected \'([^\']+)\'\'', r'position (\d+), unexpected \'([^\']+)\''),
            (r'Unknown attribute \'([^\']+)\'\'', r'Unknown attribute \'([^\']+)\''),
            (r'Function \'([^\']+)\' requires\'', r'Function \'([^\']+)\' requires')
        ]
        
        fixed = False
        for old, new in fixes:
            if old in content:
                content = content.replace(old, new)
                fixed = True
        
        if fixed:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Expressões regulares corrigidas em {file_path}")
            return True
        else:
            logger.info(f"Nenhuma expressão regular para corrigir em {file_path}")
            return True  # Nenhuma correção necessária é considerado sucesso
    
    except Exception as e:
        logger.error(f"Erro ao corrigir expressões regulares: {str(e)}")
        return False

def install_dependencies():
    """
    Instala as dependências necessárias.
    
    Returns:
        bool: True se instalado com sucesso, False caso contrário
    """
    # Lista de dependências críticas
    dependencies = [
        "markdown",
        "fastapi",
        "uvicorn",
        "openai",
        "aiohttp",
        "pydantic"
    ]
    
    success = True
    for dep in dependencies:
        try:
            # Verificar se já está instalado
            try:
                __import__(dep)
                logger.info(f"Dependência {dep} já instalada")
                continue
            except ImportError:
                pass
            
            logger.info(f"Instalando dependência: {dep}")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Dependência {dep} instalada com sucesso")
            else:
                logger.error(f"Erro ao instalar {dep}: {result.stderr}")
                success = False
        
        except Exception as e:
            logger.error(f"Exceção ao instalar {dep}: {str(e)}")
            success = False
    
    return success

def verify_file_exists_or_create(file_path, content_creator_func=None):
    """
    Verifica se um arquivo existe e o cria se necessário.
    
    Args:
        file_path (str): Caminho do arquivo
        content_creator_func (callable): Função que gera o conteúdo do arquivo
        
    Returns:
        bool: True se o arquivo existe ou foi criado, False caso contrário
    """
    if os.path.exists(file_path):
        logger.info(f"Arquivo {file_path} existe")
        return True
    
    # Se não existe e não temos função para criar conteúdo
    if not content_creator_func:
        logger.warning(f"Arquivo {file_path} não existe e não foi fornecida função para criação")
        return False
    
    try:
        # Garantir que o diretório exista
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        
        # Criar o arquivo
        content = content_creator_func()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Arquivo {file_path} criado com sucesso")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao criar arquivo {file_path}: {str(e)}")
        return False

def create_check_and_fix_cache_content():
    """
    Cria o conteúdo para o arquivo check_and_fix_cache.py.
    
    Returns:
        str: Conteúdo do arquivo
    """
    return '''"""
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
'''

def add_collect_entity_dependencies():
    """
    Adiciona o método collect_entity_dependencies ao NewRelicCollector.
    
    Returns:
        bool: True se adicionado com sucesso, False caso contrário
    """
    file_path = "utils/newrelic_collector.py"
    
    if not os.path.exists(file_path):
        logger.error(f"Arquivo não encontrado: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se o método já existe
        if "async def collect_entity_dependencies" in content:
            logger.info("Método collect_entity_dependencies já existe")
            return True
        
        # Encontrar um bom local para adicionar o método
        # Procurar após o método collect_entity_deployments
        marker = "async def collect_entity_deployments"
        if marker not in content:
            logger.error("Não foi possível encontrar um local para adicionar o método")
            return False
        
        # Encontrar o final do método collect_entity_deployments
        method_start = content.find(marker)
        method_block_level = 0
        method_end = method_start
        
        for i in range(method_start, len(content)):
            if content[i] == '{':
                method_block_level += 1
            elif content[i] == '}':
                method_block_level -= 1
                if method_block_level < 0:
                    method_end = i
                    break
        
        # Se não encontrar o final exato, procurar pela próxima definição de método
        if method_end == method_start:
            next_method = content.find("async def", method_start + len(marker))
            if next_method != -1:
                method_end = next_method
            else:
                method_end = len(content)
        
        # Adicionar nosso novo método
        new_method = '''
    
    async def collect_entity_dependencies(self, guid):
        """
        Coleta informações sobre dependências da entidade (serviços externos, bancos de dados, etc.)
        
        Args:
            guid (str): GUID da entidade
            
        Returns:
            dict: Informações sobre as dependências ou None
        """
        try:
            # Consultar dependências da entidade via Service Maps
            query = f"""
            {{
              actor {{
                entity(guid: "{guid}") {{
                  ... on AlertableEntity {{
                    serviceMap: relatedEntities(filter: {{direction: DOWNSTREAM}}) {{
                      source {{
                        entity {{
                          name
                          guid
                          entityType
                          account {{
                            id
                            name
                          }}
                        }}
                      }}
                      target {{
                        entity {{
                          name
                          guid
                          entityType
                          account {{
                            id
                            name
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
            """
            
            response = await self.make_graphql_request(query)
            
            if not response or 'data' not in response or not response['data'].get('actor', {}).get('entity', {}).get('serviceMap'):
                return None
                
            service_map = response['data']['actor']['entity']['serviceMap']
            
            # Processar e formatar dependências
            dependencies = {
                "servicos_externos": [],
                "bancos_dados": [],
                "outros": []
            }
            
            for relation in service_map:
                target = relation.get('target', {}).get('entity', {})
                
                if not target or not target.get('guid'):
                    continue
                
                dependency = {
                    "nome": target.get('name', 'Desconhecido'),
                    "guid": target.get('guid'),
                    "tipo": target.get('entityType')
                }
                
                # Categorizar dependência
                entity_type = target.get('entityType', '').lower()
                if 'database' in entity_type or 'db' in entity_type:
                    dependencies["bancos_dados"].append(dependency)
                elif 'service' in entity_type or 'api' in entity_type or 'application' in entity_type:
                    dependencies["servicos_externos"].append(dependency)
                else:
                    dependencies["outros"].append(dependency)
            
            # Remover categorias vazias
            for key in list(dependencies.keys()):
                if not dependencies[key]:
                    del dependencies[key]
            
            return dependencies if any(dependencies.values()) else None
            
        except Exception as e:
            logger.error(f"Erro ao coletar dependências para entidade {guid}: {str(e)}")
            return None
'''
        
        # Inserir o novo método
        updated_content = content[:method_end] + new_method + content[method_end:]
        
        # Salvar o arquivo atualizado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info("Método collect_entity_dependencies adicionado com sucesso")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao adicionar método collect_entity_dependencies: {str(e)}")
        return False

def main():
    """
    Função principal para corrigir o backend.
    
    Returns:
        int: Código de saída (0 para sucesso, outro valor para falha)
    """
    logger.info("Iniciando processo de reparo do backend")
    
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Fixar erros nas expressões regulares
    logger.info("Corrigindo erros nas expressões regulares...")
    if not fix_regex_errors():
        logger.error("Falha ao corrigir expressões regulares")
        return 1
    
    # Instalar dependências
    logger.info("Instalando dependências...")
    if not install_dependencies():
        logger.warning("Algumas dependências não puderam ser instaladas")
        # Continuar mesmo assim
    
    # Verificar e criar arquivos necessários
    logger.info("Verificando e criando arquivos necessários...")
    if not verify_file_exists_or_create("check_and_fix_cache.py", create_check_and_fix_cache_content):
        logger.error("Falha ao verificar/criar check_and_fix_cache.py")
        return 1
    
    # Adicionar método collect_entity_dependencies
    logger.info("Adicionando método collect_entity_dependencies...")
    if not add_collect_entity_dependencies():
        logger.error("Falha ao adicionar método collect_entity_dependencies")
        return 1
    
    # Executar script de verificação de cache
    logger.info("Verificando e reparando cache...")
    if check_script_exists("check_and_fix_cache"):
        if not run_python_script("check_and_fix_cache"):
            logger.warning("Falha na execução do script de verificação de cache")
            # Continuar mesmo assim
    
    # Tentar iniciar o backend
    logger.info("Iniciando o backend...")
    if check_script_exists("start_backend_safe"):
        if not run_python_script("start_backend_safe"):
            logger.error("Falha ao iniciar o backend")
            return 1
    else:
        logger.info("Script start_backend_safe.py não encontrado, tentando start_backend.py")
        if check_script_exists("start_backend"):
            if not run_python_script("start_backend"):
                logger.error("Falha ao iniciar o backend")
                return 1
        else:
            logger.error("Nenhum script de inicialização encontrado")
            return 1
    
    logger.info("Backend reparado e iniciado com sucesso!")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"Erro fatal durante o reparo do backend: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)
