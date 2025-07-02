#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir as entidades e garantir que todos os campos necessários estejam presentes
"""

import json
import os
from pathlib import Path
import logging

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def corrigir_entidades():
    """
    Corrige as entidades para garantir que todos os campos necessários estejam presentes
    """
    # Caminho do arquivo de entidades
    entidades_file = Path("backend/dados/entidades.json")
    
    # Verificar se o arquivo existe
    if not entidades_file.exists():
        logger.error(f"Arquivo de entidades não encontrado: {entidades_file}")
        return False
    
    try:
        # Carregar o arquivo de entidades
        with open(entidades_file, 'r', encoding='utf-8') as file:
            entidades = json.load(file)
        
        logger.info(f"Carregado arquivo de entidades com {len(entidades)} entidades")
        
        # Lista das entidades principais que queremos garantir que existam
        entidades_principais = [
            {
                "name": "API-Pagamentos",
                "domain": "APM",
                "status": "ATENÇÃO",
                "entityType": "APPLICATION",
                "metricas": {
                    "24h": {
                        "apdex": 0.9,
                        "response_time": 180.2,
                        "error_rate": 1.5,
                        "throughput": 1100.0
                    }
                }
            },
            {
                "name": "API-Autenticacao",
                "domain": "APM",
                "status": "OK",
                "entityType": "APPLICATION",
                "metricas": {
                    "24h": {
                        "apdex": 0.89,
                        "response_time": 150.1,
                        "error_rate": 1.2,
                        "throughput": 2200.0
                    }
                }
            },
            {
                "name": "Database-Principal",
                "domain": "INFRA",
                "status": "OK",
                "entityType": "DATABASE",
                "metricas": {
                    "24h": {
                        "apdex": 0.82,
                        "response_time": 380.5,
                        "error_rate": 0.3,
                        "throughput": 700.0
                    }
                }
            }
        ]
        
        # Encontrar e atualizar as entidades existentes ou adicionar novas
        entidades_atualizadas = []
        entidades_principais_names = [e["name"] for e in entidades_principais]
        
        # Primeiro, adicionar as entidades principais
        for entidade_principal in entidades_principais:
            # Verificar se a entidade já existe
            entidade_existente = next(
                (e for e in entidades if e.get("name") == entidade_principal["name"]), 
                None
            )
            
            if entidade_existente:
                # Atualizar campos faltantes
                for key, value in entidade_principal.items():
                    if key not in entidade_existente or entidade_existente[key] is None:
                        entidade_existente[key] = value
                    elif key == "metricas" and isinstance(value, dict):
                        # Garantir que as métricas também estão completas
                        for periodo, metricas in value.items():
                            if periodo not in entidade_existente["metricas"]:
                                entidade_existente["metricas"][periodo] = metricas
                            elif isinstance(metricas, dict):
                                for metrica_key, metrica_value in metricas.items():
                                    if metrica_key not in entidade_existente["metricas"][periodo]:
                                        entidade_existente["metricas"][periodo][metrica_key] = metrica_value
                
                entidades_atualizadas.append(entidade_existente)
                logger.info(f"Entidade atualizada: {entidade_existente['name']}")
            else:
                # Adicionar nova entidade
                entidades_atualizadas.append(entidade_principal)
                logger.info(f"Entidade adicionada: {entidade_principal['name']}")
        
        # Adicionar outras entidades que não são principais
        for entidade in entidades:
            if entidade.get("name") not in entidades_principais_names:
                # Garantir que a entidade tem um campo status
                if "status" not in entidade or entidade["status"] is None:
                    entidade["status"] = "OK"  # Valor padrão
                
                entidades_atualizadas.append(entidade)
        
        # Salvar o arquivo atualizado
        with open(entidades_file, 'w', encoding='utf-8') as file:
            json.dump(entidades_atualizadas, file, indent=2)
        
        logger.info(f"Arquivo de entidades atualizado com {len(entidades_atualizadas)} entidades")
        
        # Agora, vamos verificar se precisamos atualizar o cache completo também
        cache_file = Path("historico/cache_completo.json")
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as file:
                    cache = json.load(file)
                
                if "entidades" in cache:
                    # Atualizar o cache com as entidades corrigidas
                    cache["entidades"] = entidades_atualizadas
                    
                    # Salvar o cache atualizado
                    with open(cache_file, 'w', encoding='utf-8') as file:
                        json.dump(cache, file, indent=2)
                    
                    logger.info(f"Cache atualizado com {len(entidades_atualizadas)} entidades")
            except Exception as e:
                logger.error(f"Erro ao atualizar cache: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao corrigir entidades: {e}")
        return False

if __name__ == "__main__":
    print("Corrigindo entidades...")
    sucesso = corrigir_entidades()
    if sucesso:
        print("✅ Entidades corrigidas com sucesso!")
    else:
        print("❌ Falha ao corrigir entidades.")
