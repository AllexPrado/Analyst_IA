#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
import importlib.util
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def importar_modulo_dinamico(nome_arquivo):
    """Importa um módulo Python dinamicamente a partir do caminho do arquivo"""
    try:
        # Normalizando o caminho
        caminho_absoluto = os.path.abspath(nome_arquivo)
        nome_modulo = os.path.splitext(os.path.basename(nome_arquivo))[0]
        
        # Carregando o módulo
        spec = importlib.util.spec_from_file_location(nome_modulo, caminho_absoluto)
        if not spec:
            logger.error(f"Não foi possível carregar o arquivo {nome_arquivo}")
            return None
            
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    except Exception as e:
        logger.error(f"Erro ao importar {nome_arquivo}: {e}")
        return None

def garantir_diretorio_dados():
    """Garante que o diretório de dados existe"""
    diretorios = ["dados", "backend/dados", "../dados", "../backend/dados"]
    for diretorio in diretorios:
        os.makedirs(diretorio, exist_ok=True)
        logger.info(f"Diretório {diretorio} verificado/criado")

def gerar_todos_dados():
    """Gera todos os arquivos de dados necessários para o funcionamento do sistema"""
    # Lista com info de cada endpoint
    endpoints = [
        {"arquivo": "kpis_endpoints.py", "funcao_geradora": "generate_sample_kpis_data", "arquivo_saida": "kpis.json"},
        {"arquivo": "tendencias_endpoints.py", "funcao_geradora": "generate_sample_tendencias_data", "arquivo_saida": "tendencias.json"},
        {"arquivo": "cobertura_endpoints.py", "funcao_geradora": "generate_sample_cobertura_data", "arquivo_saida": "cobertura.json"},
        {"arquivo": "insights_endpoints.py", "funcao_geradora": "generate_sample_insights_data", "arquivo_saida": "insights.json"},
        {"arquivo": "entidades_endpoints.py", "funcao_geradora": "generate_sample_entidades_data", "arquivo_saida": "entidades.json"},
        {"arquivo": "chat_endpoints.py", "funcao_geradora": "generate_sample_chat_history", "arquivo_saida": "chat_history.json"},
    ]
    
    # Garantir que o diretório de dados existe
    garantir_diretorio_dados()
    
    # Encontrar diretório de endpoints
    diretorios_possiveis = [
        "endpoints",
        "backend/endpoints",
        "../endpoints",
        "../backend/endpoints"
    ]
    
    diretorio_endpoints = None
    for diretorio in diretorios_possiveis:
        if os.path.exists(diretorio) and os.path.isdir(diretorio):
            diretorio_endpoints = diretorio
            logger.info(f"Diretório de endpoints encontrado: {diretorio_endpoints}")
            break
    
    if not diretorio_endpoints:
        logger.error("Não foi possível encontrar o diretório de endpoints")
        return False

    # Gerar e salvar dados para cada endpoint
    for endpoint in endpoints:
        arquivo_endpoint = os.path.join(diretorio_endpoints, endpoint["arquivo"])
        
        # Verificar se o arquivo do endpoint existe
        if not os.path.exists(arquivo_endpoint):
            logger.warning(f"Arquivo {arquivo_endpoint} não encontrado")
            continue
        
        # Carregar o módulo
        modulo = importar_modulo_dinamico(arquivo_endpoint)
        if not modulo:
            continue
        
        # Verificar se a função geradora existe no módulo
        if not hasattr(modulo, endpoint["funcao_geradora"]):
            logger.warning(f"Função {endpoint['funcao_geradora']} não encontrada no módulo {arquivo_endpoint}")
            continue
        
        # Executar função geradora
        try:
            funcao_geradora = getattr(modulo, endpoint["funcao_geradora"])
            dados_gerados = funcao_geradora()
            
            # Salvar em todos os diretórios possíveis de dados
            for diretorio in ["dados", "backend/dados"]:
                try:
                    os.makedirs(diretorio, exist_ok=True)
                    arquivo_saida = os.path.join(diretorio, endpoint["arquivo_saida"])
                    
                    with open(arquivo_saida, 'w', encoding='utf-8') as f:
                        json.dump(dados_gerados, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Dados salvos em {arquivo_saida}")
                except Exception as e:
                    logger.error(f"Erro ao salvar dados em {arquivo_saida}: {e}")
        except Exception as e:
            logger.error(f"Erro ao gerar dados com {endpoint['funcao_geradora']}: {e}")
    
    logger.info("Geração de dados concluída")
    return True

if __name__ == "__main__":
    logger.info("Iniciando geração de todos os arquivos de dados")
    sucesso = gerar_todos_dados()
    if sucesso:
        logger.info("Todos os dados foram gerados com sucesso!")
    else:
        logger.error("Houve problemas na geração de dados")
