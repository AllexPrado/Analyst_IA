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
def generate_sample_kpis_data():
    """Gera dados de KPIs para desenvolvimento"""
    return {
        "performance": {
            "apdex": round(random.uniform(0.7, 0.95), 2),
            "tempo_resposta": round(random.uniform(0.1, 2.0), 2),
            "tendencia": round(random.uniform(-10, 10), 1),
            "historico": [0.72, 0.75, 0.78, 0.82, 0.85, 0.89]
        },
        "disponibilidade": {
            "uptime": round(random.uniform(98, 99.99), 2),
            "total_servicos": random.randint(40, 60),
            "servicos_disponiveis": random.randint(35, 59),
            "tendencia": round(random.uniform(-1, 1), 2),
            "historico": [98.5, 98.7, 99.1, 99.3, 99.5, 99.7]
        },
        "erros": {
            "taxa_erro": round(random.uniform(0.1, 3.0), 2),
            "tendencia": round(random.uniform(-20, 5), 1),
            "total_requisicoes": random.randint(100000, 500000),
            "requisicoes_com_erro": random.randint(100, 5000),
            "historico": [2.5, 2.2, 1.8, 1.5, 1.2, 0.8]
        },
        "throughput": {
            "requisicoes_por_minuto": random.randint(1000, 5000),
            "tendencia": round(random.uniform(-5, 15), 1),
            "pico": random.randint(5000, 10000),
            "historico": [2200, 2500, 2800, 3100, 3500, 3800]
        },
        # Adicionando campos específicos para os KPIs mostrados na interface
        "latencia_media": {
            "valor": round(random.uniform(0.05, 0.5), 2),
            "unidade": "ms",
            "tendencia": round(random.uniform(-20, 20), 1),
            "historico": [0.12, 0.11, 0.10, 0.09, 0.08, 0.07]
        },
        "requisicoes": {
            "valor": random.randint(1000, 5000),
            "unidade": "/seg",
            "tendencia": round(random.uniform(-12, 12), 1),
            "historico": [1200, 1500, 2000, 2500, 3000, 3500]
        },
        "cpu": {
            "valor": round(random.uniform(10, 90), 1),
            "unidade": "%",
            "tendencia": round(random.uniform(-4, 4), 1),
            "historico": [45, 50, 55, 60, 65, 60]
        },
        "ram": {
            "valor": round(random.uniform(20, 85), 1),
            "unidade": "%",
            "tendencia": round(random.uniform(-4, 4), 1),
            "historico": [50, 55, 60, 65, 70, 65]
        },
        # Adicionando detalhamento por serviço
        "servicos": [
            {
                "nome": "API Gateway",
                "disponibilidade": round(random.uniform(99, 99.99), 2),
                "mttr": round(random.uniform(5, 30), 1),
                "latencia": round(random.uniform(0.05, 0.2), 2),
                "taxa_erro": round(random.uniform(0.01, 0.5), 2),
                "status": "normal" if random.random() > 0.1 else "alerta"
            },
            {
                "nome": "Autenticação",
                "disponibilidade": round(random.uniform(99.5, 99.99), 2),
                "mttr": round(random.uniform(5, 20), 1),
                "latencia": round(random.uniform(0.1, 0.3), 2),
                "taxa_erro": round(random.uniform(0.01, 0.3), 2),
                "status": "normal" if random.random() > 0.1 else "alerta"
            },
            {
                "nome": "Processamento",
                "disponibilidade": round(random.uniform(98, 99.9), 2),
                "mttr": round(random.uniform(10, 40), 1),
                "latencia": round(random.uniform(0.2, 0.8), 2),
                "taxa_erro": round(random.uniform(0.05, 1.0), 2),
                "status": "normal" if random.random() > 0.1 else "alerta"
            },
            {
                "nome": "Banco de Dados",
                "disponibilidade": round(random.uniform(99, 99.9), 2),
                "mttr": round(random.uniform(15, 45), 1),
                "latencia": round(random.uniform(0.1, 0.4), 2),
                "taxa_erro": round(random.uniform(0.01, 0.2), 2),
                "status": "normal" if random.random() > 0.1 else "alerta"
            },
            {
                "nome": "Cache",
                "disponibilidade": round(random.uniform(99.5, 99.99), 2),
                "mttr": round(random.uniform(2, 15), 1),
                "latencia": round(random.uniform(0.01, 0.1), 2),
                "taxa_erro": round(random.uniform(0.01, 0.1), 2),
                "status": "normal" if random.random() > 0.1 else "alerta"
            }
        ]
    }

@router.get("/kpis")
async def get_kpis():
    try:
        # Lista de possíveis localizações para o arquivo de kpis
        possible_paths = [
            "dados/kpis.json",               # Relativo ao diretório atual
            "backend/dados/kpis.json",       # Relativo ao diretório raiz
            "../dados/kpis.json",            # Um nível acima (se estamos em backend)
            "../backend/dados/kpis.json"     # Um nível acima, então em backend
        ]
        
        # Tentar cada caminho
        for kpis_path in possible_paths:
            if os.path.exists(kpis_path):
                try:
                    with open(kpis_path, 'r', encoding='utf-8') as file:
                        kpis_data = json.load(file)
                        logger.info(f"Dados de KPIs carregados do arquivo: {kpis_path}")
                        return kpis_data
                except Exception as e:
                    logger.error(f"Erro ao ler dados de KPIs do arquivo {kpis_path}: {e}")
        
        # Se não encontrou em nenhum lugar, procurar em qualquer lugar usando Path.glob
        root_dir = Path('.').resolve()
        for data_file in root_dir.glob('**/dados/kpis.json'):
            try:
                with open(data_file, 'r', encoding='utf-8') as file:
                    kpis_data = json.load(file)
                    logger.info(f"Dados de KPIs carregados do arquivo (busca global): {data_file}")
                    return kpis_data
            except Exception as e:
                logger.error(f"Erro ao ler dados de KPIs do arquivo {data_file}: {e}")
        
        # Não gerar dados simulados, retornar estrutura vazia com informação
        logger.warning("Nenhum arquivo de dados de KPIs encontrado. Retornando dados vazios.")
        kpis_data = {
            "erro": True,
            "mensagem": "Não foram encontrados dados reais de KPIs no cache. Atualize o cache com dados do New Relic.",
            "timestamp": datetime.now().isoformat()
        }
        
        return kpis_data
    except Exception as e:
        logger.error(f"Erro ao processar requisição de KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
