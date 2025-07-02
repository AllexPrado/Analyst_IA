"""
Módulo para carregamento de dados centralizados.
Este módulo implementa funções para carregar dados de arquivos JSON
de forma consistente em todos os endpoints.
"""

import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configuração de logging
logger = logging.getLogger(__name__)

def load_json_data(filename: str, required_structure: Optional[str] = None) -> Dict:
    """
    Carrega dados de um arquivo JSON de forma consistente.
    Procura o arquivo em várias possíveis localizações.
    
    Args:
        filename: Nome do arquivo (sem caminho)
        required_structure: Tipo de estrutura esperada ('list', 'dict', ou None para qualquer)
        
    Returns:
        Dict: Conteúdo do arquivo JSON ou dicionário com erro se não encontrado
    """
    # Garantir que tem a extensão .json
    if not filename.endswith('.json'):
        filename += '.json'
        
    # Lista de possíveis diretórios para procurar dados
    possible_data_dirs = [
        "dados",                  # Relativo ao diretório atual
        "backend/dados",          # Relativo ao diretório raiz
        "../dados",               # Um nível acima (se estamos em backend)
        "../backend/dados",       # Um nível acima, então em backend
    ]
    
    # Tentar cada diretório possível
    for data_dir in possible_data_dirs:
        file_path = os.path.join(data_dir, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    logger.info(f"Arquivo {filename} carregado de {file_path}")
                    
                    # Verificar estrutura se especificado
                    if required_structure == 'list' and not isinstance(data, list):
                        logger.warning(f"Estrutura inválida no arquivo {filename}: esperava lista, recebeu {type(data)}")
                    elif required_structure == 'dict' and not isinstance(data, dict):
                        logger.warning(f"Estrutura inválida no arquivo {filename}: esperava dicionário, recebeu {type(data)}")
                    else:
                        return data
            except Exception as e:
                logger.error(f"Erro ao ler arquivo {file_path}: {e}")
    
    # Se não encontrou, procurar em qualquer lugar
    root_dir = Path('.').resolve()
    for data_file in root_dir.glob(f'**/dados/{filename}'):
        try:
            with open(data_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                logger.info(f"Arquivo {filename} carregado de {data_file} (busca global)")
                
                # Verificar estrutura se especificado
                if required_structure == 'list' and not isinstance(data, list):
                    logger.warning(f"Estrutura inválida no arquivo {filename}: esperava lista, recebeu {type(data)}")
                elif required_structure == 'dict' and not isinstance(data, dict):
                    logger.warning(f"Estrutura inválida no arquivo {filename}: esperava dicionário, recebeu {type(data)}")
                else:
                    return data
        except Exception as e:
            logger.error(f"Erro ao ler arquivo {data_file}: {e}")
    
    # Se chegou aqui, não encontrou o arquivo
    logger.error(f"Arquivo {filename} não encontrado em nenhum local")
    return {
        "erro": True,
        "mensagem": f"Dados não encontrados para: {filename}. Execute o script generate_unified_data.py para criar dados de teste ou atualize o cache com dados reais."
    }
