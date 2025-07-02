from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import random

# Tentativa de importação das funções de processamento de entidade
try:
    from backend.utils.entity_processor import is_entity_valid, process_entity_details
    from backend.utils.data_loader import load_json_data
except ImportError:
    from utils.entity_processor import is_entity_valid, process_entity_details
    from utils.data_loader import load_json_data

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
    """
    Endpoint para obter dados de cobertura.
    Carrega dados do arquivo cobertura.json e processa para garantir que apenas dados válidos sejam retornados.
    """
    try:
        # Carregar dados usando a função centralizada
        cobertura_data = load_json_data("cobertura.json")
        
        # Verificar se houve erro na carga
        if cobertura_data.get("erro"):
            return cobertura_data
            
        # Processar dados com base na estrutura (lista ou dicionário)
        valid_cobertura = []
        if isinstance(cobertura_data, list):
            valid_cobertura = [process_entity_details(item) for item in cobertura_data if is_entity_valid(item)]
        elif isinstance(cobertura_data, dict):
            # Para dados de cobertura que geralmente são um único objeto com estatísticas
            # não precisamos processar como entidade, apenas retornar diretamente
            if 'total_entidades' in cobertura_data and 'monitoradas' in cobertura_data:
                logger.info("Dados de cobertura já estão no formato correto")
                return cobertura_data
            else:
                valid_cobertura = [process_entity_details(cobertura_data)] if is_entity_valid(cobertura_data) else []
        
        # Remover campos vazios/nulos
        valid_cobertura = [i for i in valid_cobertura if i and i != {}]
        
        # Verificar se temos dados de cobertura válidos
        if valid_cobertura:
            logger.info(f"Retornando {len(valid_cobertura)} dados de cobertura válidos")
            return valid_cobertura[0] if len(valid_cobertura) == 1 else valid_cobertura
            
        # Se não encontrou dados válidos, retornar mensagem de erro
        logger.warning("Nenhum dado de cobertura válido encontrado após processamento")
        return {
            "erro": True,
            "mensagem": "Não foram encontrados dados reais de cobertura válidos no cache. Execute generate_unified_data.py para criar dados de teste ou atualize o cache com dados do New Relic.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao processar requisição de cobertura: {e}")
        raise HTTPException(status_code=500, detail=str(e))
