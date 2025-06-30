#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para verificar a integridade da integração entre frontend e backend,
validando se todos os arquivos de dados necessários existem e se os endpoints
estão funcionando corretamente.
"""

import os
import sys
import json
import logging
from pathlib import Path
import requests
import time
from typing import List, Dict, Any, Optional

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# URL base da API (quando o backend estiver rodando)
BASE_URL = "http://localhost:8000"
TIMEOUT = 10  # segundos

def verificar_arquivos_dados():
    """Verifica se todos os arquivos de dados necessários existem"""
    logger.info("Verificando arquivos de dados...")
    
    # Arquivos de dados necessários
    arquivos_necessarios = [
        "kpis.json",
        "tendencias.json",
        "cobertura.json",
        "insights.json",
        "entidades.json",
        "chat_history.json",
        "status.json",
        "resumo-geral.json"
    ]
    
    # Diretórios onde os arquivos podem estar
    diretorios_possiveis = [
        "dados",
        "backend/dados",
        "../dados",
        "../backend/dados"
    ]
    
    # Verificar cada arquivo em cada diretório possível
    arquivos_encontrados = []
    for arquivo in arquivos_necessarios:
        encontrado = False
        for diretorio in diretorios_possiveis:
            caminho = os.path.join(diretorio, arquivo)
            if os.path.exists(caminho):
                encontrado = True
                arquivos_encontrados.append(arquivo)
                logger.info(f"Arquivo {arquivo} encontrado em {caminho}")
                break
        
        if not encontrado:
            logger.warning(f"Arquivo {arquivo} não encontrado em nenhum diretório")
    
    # Verificar se todos os arquivos foram encontrados
    todos_encontrados = all(arquivo in arquivos_encontrados for arquivo in arquivos_necessarios)
    if todos_encontrados:
        logger.info("✅ Todos os arquivos de dados estão presentes")
    else:
        arquivos_faltando = [arquivo for arquivo in arquivos_necessarios if arquivo not in arquivos_encontrados]
        logger.warning(f"❌ Faltam os seguintes arquivos: {', '.join(arquivos_faltando)}")
    
    return todos_encontrados

def verificar_endpoints(esperar_backend: bool = False):
    """Verifica se todos os endpoints necessários estão respondendo corretamente"""
    logger.info("Verificando endpoints...")
    
    # Endpoints necessários
    endpoints = [
        "/health", 
        "/kpis", 
        "/tendencias", 
        "/cobertura", 
        "/insights",
        "/entidades",
        "/status"
    ]
    
    # Esperar o backend iniciar se necessário
    if esperar_backend:
        logger.info("Aguardando o backend iniciar...")
        for _ in range(10):  # Tenta por até 10 segundos
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
                if response.status_code == 200:
                    logger.info("Backend iniciado com sucesso!")
                    break
            except requests.RequestException:
                pass
            time.sleep(1)
    
    # Verificar cada endpoint
    endpoints_funcionando = []
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
            if response.status_code == 200:
                # Verifica se o JSON retornado não é vazio
                try:
                    data = response.json()
                    if data:
                        endpoints_funcionando.append(endpoint)
                        logger.info(f"✅ Endpoint {endpoint} respondendo com dados válidos")
                    else:
                        logger.warning(f"❌ Endpoint {endpoint} respondeu com JSON vazio")
                except json.JSONDecodeError:
                    logger.warning(f"❌ Endpoint {endpoint} não retornou JSON válido")
            else:
                logger.warning(f"❌ Endpoint {endpoint} respondeu com status {response.status_code}")
        except requests.RequestException as e:
            logger.warning(f"❌ Erro ao acessar endpoint {endpoint}: {e}")
    
    # Verificar se todos os endpoints estão funcionando
    todos_funcionando = len(endpoints_funcionando) == len(endpoints)
    if todos_funcionando:
        logger.info("✅ Todos os endpoints estão funcionando corretamente")
    else:
        endpoints_com_problema = [endpoint for endpoint in endpoints if endpoint not in endpoints_funcionando]
        logger.warning(f"❌ Os seguintes endpoints têm problemas: {', '.join(endpoints_com_problema)}")
    
    return todos_funcionando

def verificar_estrutura_dados():
    """Verifica se os dados retornados pelos endpoints têm a estrutura esperada"""
    logger.info("Verificando estrutura dos dados...")
    
    # Mapa de endpoints e campos esperados
    estrutura_esperada = {
        "/kpis": ["disponibilidade", "performance", "erros", "throughput", "cpu", "ram"],
        "/tendencias": ["apdex", "disponibilidade", "erros", "throughput", "anomalias"],
        "/cobertura": ["total_entidades", "monitoradas", "porcentagem", "por_dominio"],
        "/insights": ["roiMonitoramento", "aumentoProdutividade", "economiaTotal", "recomendacoes"],
        "/entidades": ["entidades"]
    }
    
    # Verificar cada endpoint
    endpoints_validos = []
    for endpoint, campos_esperados in estrutura_esperada.items():
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Verifica se pelo menos um dos campos esperados está presente
                    campos_presentes = [campo for campo in campos_esperados if campo in data]
                    if campos_presentes:
                        endpoints_validos.append(endpoint)
                        logger.info(f"✅ Endpoint {endpoint} tem estrutura válida com campos: {', '.join(campos_presentes)}")
                    else:
                        logger.warning(f"❌ Endpoint {endpoint} não tem nenhum dos campos esperados: {', '.join(campos_esperados)}")
                except json.JSONDecodeError:
                    logger.warning(f"❌ Endpoint {endpoint} não retornou JSON válido")
            else:
                logger.warning(f"❌ Endpoint {endpoint} respondeu com status {response.status_code}")
        except requests.RequestException as e:
            logger.warning(f"❌ Erro ao acessar endpoint {endpoint}: {e}")
    
    # Verificar se todos os endpoints têm estrutura válida
    todos_validos = len(endpoints_validos) == len(estrutura_esperada)
    if todos_validos:
        logger.info("✅ Todos os endpoints têm estrutura de dados válida")
    else:
        endpoints_invalidos = [endpoint for endpoint in estrutura_esperada.keys() if endpoint not in endpoints_validos]
        logger.warning(f"❌ Os seguintes endpoints têm estrutura inválida: {', '.join(endpoints_invalidos)}")
    
    return todos_validos

def main():
    """Função principal"""
    logger.info("Iniciando verificação da integração frontend-backend...")
    
    # Verificar arquivos de dados
    arquivos_ok = verificar_arquivos_dados()
    
    # Verificar se o backend está rodando
    backend_rodando = False
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        backend_rodando = response.status_code == 200
    except:
        backend_rodando = False
    
    if backend_rodando:
        logger.info("Backend está rodando. Verificando endpoints...")
        endpoints_ok = verificar_endpoints()
        estrutura_ok = verificar_estrutura_dados()
        
        # Resumo final
        logger.info("\n--- RESUMO DA VERIFICAÇÃO ---")
        logger.info(f"Arquivos de dados: {'✅ OK' if arquivos_ok else '❌ Problemas encontrados'}")
        logger.info(f"Endpoints funcionando: {'✅ OK' if endpoints_ok else '❌ Problemas encontrados'}")
        logger.info(f"Estrutura de dados: {'✅ OK' if estrutura_ok else '❌ Problemas encontrados'}")
        
        if arquivos_ok and endpoints_ok and estrutura_ok:
            logger.info("\n✅ INTEGRAÇÃO COMPLETA E FUNCIONANDO CORRETAMENTE!")
        else:
            logger.warning("\n❌ EXISTEM PROBLEMAS NA INTEGRAÇÃO. Verifique os logs acima.")
    else:
        logger.warning("Backend não está rodando. Impossível verificar endpoints.")
        logger.info("\n--- RESUMO DA VERIFICAÇÃO ---")
        logger.info(f"Arquivos de dados: {'✅ OK' if arquivos_ok else '❌ Problemas encontrados'}")
        logger.info(f"Backend: ❌ Não está rodando")
        logger.info("\nInicie o backend antes de continuar a verificação.")

if __name__ == "__main__":
    main()
