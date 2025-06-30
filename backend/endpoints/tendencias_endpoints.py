from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import random
from pathlib import Path

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router
router = APIRouter()

# Dados simulados para desenvolvimento - serão substituídos por dados reais
def generate_sample_tendencias_data():
    """Gera dados de tendências para o frontend"""
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"]
    return {
        "apdex": {
            "labels": meses,
            "series": [
                {
                    "name": "Apdex",
                    "data": [0.82, 0.84, 0.81, 0.83, 0.87, 0.89]
                }
            ]
        },
        "disponibilidade": {
            "labels": meses,
            "series": [
                {
                    "name": "Uptime",
                    "data": [99.2, 99.3, 99.1, 99.5, 99.7, 99.8]
                }
            ]
        },
        "erros": {
            "labels": meses,
            "series": [
                {
                    "name": "Taxa de Erros",
                    "data": [2.5, 2.2, 2.7, 2.0, 1.5, 1.1]
                }
            ]
        },
        "throughput": {
            "labels": meses,
            "series": [
                {
                    "name": "Requisições/min",
                    "data": [1200, 1350, 1500, 1700, 1900, 2100]
                }
            ]
        },
        "previsao_cpu": {
            "labels": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", 
                      "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30"],
            "series": [
                {
                    "name": "Utilização da CPU",
                    "data": [60, 61, 63, 65, 66, 68, 69, 71, 72, 74, 75, 76, 78, 79, 80, 
                            81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 92, 93, 94]
                },
                {
                    "name": "Previsão com otimização",
                    "data": [60, 61, 63, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 
                            77, 78, 79, 80, 81, 81, 82, 82, 83, 83, 84, 84, 84, 85, 85]
                }
            ]
        },
        "anomalias": [
            {
                "data": "2025-06-25",
                "hora": "14:32:15",
                "recurso": "API Gateway",
                "metrica": "Latência",
                "desvio": "+245%",
                "duracao": "12 min",
                "severidade": "Alta",
                "status": "Resolvido"
            },
            {
                "data": "2025-06-26",
                "hora": "08:15:22",
                "recurso": "Database",
                "metrica": "CPU",
                "desvio": "+180%",
                "duracao": "28 min",
                "severidade": "Média",
                "status": "Resolvido"
            },
            {
                "data": "2025-06-27",
                "hora": "19:45:03",
                "recurso": "Auth Service",
                "metrica": "Erros",
                "desvio": "+520%",
                "duracao": "5 min",
                "severidade": "Crítica",
                "status": "Resolvido"
            },
            {
                "data": "2025-06-28",
                "hora": "22:12:48",
                "recurso": "Cache",
                "metrica": "Hit Rate",
                "desvio": "-75%",
                "duracao": "45 min",
                "severidade": "Média",
                "status": "Resolvido"
            }
        ],
        "padroes": {
            "sazonais": {
                "confianca": 87,
                "dados": [
                    {"dia": "Dom", "valor": 0.2},
                    {"dia": "Seg", "valor": 0.8},
                    {"dia": "Ter", "valor": 0.9},
                    {"dia": "Qua", "valor": 0.85},
                    {"dia": "Qui", "valor": 0.95},
                    {"dia": "Sex", "valor": 0.92},
                    {"dia": "Sab", "valor": 0.3}
                ]
            }
        },
        "previsao_texto": "Análise preditiva indica tendência de aumento de 12% na utilização de CPU nos próximos 30 dias. Recomenda-se avaliar escalabilidade dos recursos."
    }

@router.get("/tendencias")
async def get_tendencias():
    try:
        # Lista de possíveis localizações para o arquivo de tendências
        possible_paths = [
            "dados/tendencias.json",               # Relativo ao diretório atual
            "backend/dados/tendencias.json",       # Relativo ao diretório raiz
            "../dados/tendencias.json",            # Um nível acima (se estamos em backend)
            "../backend/dados/tendencias.json"     # Um nível acima, então em backend
        ]
        
        # Tentar cada caminho
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        logger.info(f"Dados de tendências carregados do arquivo: {path}")
                        return data
                except Exception as e:
                    logger.error(f"Erro ao ler dados de tendências do arquivo {path}: {e}")
        
        # Se não encontrou em nenhum lugar, procurar em qualquer lugar usando Path.glob
        root_dir = Path('.').resolve()
        for data_file in root_dir.glob('**/dados/tendencias.json'):
            try:
                with open(data_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    logger.info(f"Dados de tendências carregados do arquivo (busca global): {data_file}")
                    return data
            except Exception as e:
                logger.error(f"Erro ao ler dados de tendências do arquivo {data_file}: {e}")
        
        # Se não houver arquivo ou houver erro, gerar dados simulados
        logger.warning("Nenhum arquivo de dados de tendências encontrado. Gerando dados simulados.")
        data = generate_sample_tendencias_data()
        
        # Tentar salvar os dados simulados para uso futuro (em pelo menos um local)
        try:
            for path in ["dados/tendencias.json", "backend/dados/tendencias.json"]:
                dir_path = os.path.dirname(path)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                    
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f"Dados simulados salvos em {path}")
        except Exception as e:
            logger.error(f"Erro ao salvar dados simulados: {e}")
            
        return data
    except Exception as e:
        logger.error(f"Erro ao processar requisição de tendências: {e}")
        raise HTTPException(status_code=500, detail=str(e))
