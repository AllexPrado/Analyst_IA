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
def generate_sample_cobertura_data():
    """Gera dados de cobertura para o frontend"""
    total_entidades = random.randint(150, 200)
    monitoradas = random.randint(int(total_entidades * 0.7), total_entidades)
    
    return {
        "total_entidades": total_entidades,
        "monitoradas": monitoradas,
        "porcentagem": round((monitoradas / total_entidades) * 100, 1),
        "por_dominio": {
            "APM": {
                "total": random.randint(40, 60),
                "monitoradas": random.randint(30, 50),
                "criticas": random.randint(5, 15)
            },
            "BROWSER": {
                "total": random.randint(30, 40),
                "monitoradas": random.randint(20, 30),
                "criticas": random.randint(3, 10)
            },
            "INFRA": {
                "total": random.randint(60, 80),
                "monitoradas": random.randint(50, 70),
                "criticas": random.randint(10, 20)
            },
            "MOBILE": {
                "total": random.randint(10, 20),
                "monitoradas": random.randint(5, 15),
                "criticas": random.randint(2, 8)
            }
        },
        "historico": {
            "labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
            "series": [
                {
                    "name": "Cobertura (%)",
                    "data": [65, 70, 75, 78, 82, round((monitoradas / total_entidades) * 100, 1)]
                }
            ]
        },
        "distribuicao": {
            "recursos": [
                {"dominio": "APM", "count": random.randint(30, 50)},
                {"dominio": "BROWSER", "count": random.randint(20, 30)},
                {"dominio": "INFRA", "count": random.randint(50, 70)},
                {"dominio": "MOBILE", "count": random.randint(5, 15)}
            ],
            "dominios": [
                {"nome": "E-commerce", "count": random.randint(20, 40)},
                {"nome": "CRM", "count": random.randint(15, 30)},
                {"nome": "ERP", "count": random.randint(25, 45)},
                {"nome": "Pagamentos", "count": random.randint(10, 20)},
                {"nome": "Logística", "count": random.randint(15, 25)}
            ]
        },
        "recursos_sem_cobertura": [
            {
                "nome": "API de Pagamentos",
                "dominio": "Financeiro",
                "tipo": "API",
                "status": "Crítico",
                "acao": "Configurar APM"
            },
            {
                "nome": "Frontend Mobile",
                "dominio": "E-commerce",
                "tipo": "MOBILE",
                "status": "Alta",
                "acao": "Implementar RUM"
            },
            {
                "nome": "Servidor de Cache",
                "dominio": "Infraestrutura",
                "tipo": "INFRA",
                "status": "Média",
                "acao": "Instalar agente"
            }
        ],
        "acoes_recomendadas": [
            {
                "titulo": "Implementar APM na API de Pagamentos",
                "prioridade": "Alta",
                "esforco": "Médio",
                "impacto": "Alto",
            },
            {
                "titulo": "Configurar monitoramento de frontend mobile",
                "prioridade": "Alta",
                "esforco": "Baixo",
                "impacto": "Alto",
            },
            {
                "titulo": "Expandir cobertura para servidores de cache",
                "prioridade": "Média",
                "esforco": "Baixo",
                "impacto": "Médio",
            }
        ]
    }

@router.get("/cobertura")
async def get_cobertura():
    try:
        # Lista de possíveis localizações para o arquivo de cobertura
        possible_paths = [
            "dados/cobertura.json",               # Relativo ao diretório atual
            "backend/dados/cobertura.json",       # Relativo ao diretório raiz
            "../dados/cobertura.json",            # Um nível acima (se estamos em backend)
            "../backend/dados/cobertura.json"     # Um nível acima, então em backend
        ]
        
        # Tentar cada caminho
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        logger.info(f"Dados de cobertura carregados do arquivo: {path}")
                        return data
                except Exception as e:
                    logger.error(f"Erro ao ler dados de cobertura do arquivo {path}: {e}")
        
        # Se não encontrou em nenhum lugar, procurar em qualquer lugar usando Path.glob
        root_dir = Path('.').resolve()
        for data_file in root_dir.glob('**/dados/cobertura.json'):
            try:
                with open(data_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    logger.info(f"Dados de cobertura carregados do arquivo (busca global): {data_file}")
                    return data
            except Exception as e:
                logger.error(f"Erro ao ler dados de cobertura do arquivo {data_file}: {e}")
        
        # Se não houver arquivo ou houver erro, gerar dados simulados
        logger.warning("Nenhum arquivo de dados de cobertura encontrado. Gerando dados simulados.")
        data = generate_sample_cobertura_data()
        
        # Tentar salvar os dados simulados para uso futuro (em pelo menos um local)
        try:
            for path in ["dados/cobertura.json", "backend/dados/cobertura.json"]:
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
        logger.error(f"Erro ao processar requisição de cobertura: {e}")
        raise HTTPException(status_code=500, detail=str(e))
