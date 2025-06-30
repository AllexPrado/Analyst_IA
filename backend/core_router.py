from fastapi import APIRouter, HTTPException, Depends, Header, Request
import logging
import os
import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configurar o logger
logger = logging.getLogger(__name__)

# Tentar adicionar os diretórios de endpoints ao path para importação
endpoints_dir_attempts = [
    Path('endpoints'),         # Relativo ao diretório atual
    Path('../endpoints'),      # Um nível acima (se estamos em backend)
    Path('backend/endpoints')  # Caminho relativo ao diretório raiz
]

endpoints_found = False
for path in endpoints_dir_attempts:
    if path.exists() and path.is_dir():
        # Converter para caminho absoluto
        abs_path = str(path.resolve())
        if abs_path not in sys.path:
            sys.path.insert(0, abs_path)
            logger.info(f"Adicionado ao path: {abs_path}")
            endpoints_found = True
            break

if not endpoints_found:
    logger.warning("Nenhum diretório de endpoints encontrado. A API pode não funcionar corretamente.")

# Função para importar um router de endpoint com fallback
def import_router(module_name, endpoint_path):
    try:
        module = __import__(f"endpoints.{module_name}", fromlist=["router"])
        router = module.router
        logger.info(f"Módulo {module_name} importado com sucesso")
        return router
    except ImportError as e:
        logger.error(f"Erro ao importar módulo {module_name}: {e}")
        # Criar um router vazio para evitar erros
        fallback_router = APIRouter()
        
        @fallback_router.get(f"/{endpoint_path}")
        async def get_fallback():
            return {
                "mensagem": f"Erro ao carregar módulo {module_name}",
                "erro": str(e),
                "status": "fallback"
            }
        
        return fallback_router

# Importar os routers de endpoints específicos
insights_router = import_router("insights_endpoints", "insights")
kpis_router = import_router("kpis_endpoints", "kpis")
tendencias_router = import_router("tendencias_endpoints", "tendencias")
cobertura_router = import_router("cobertura_endpoints", "cobertura")
chat_router = import_router("chat_endpoints", "chat")

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router principal
api_router = APIRouter()

# Incluir os routers de endpoints específicos
api_router.include_router(insights_router, tags=["insights"])
api_router.include_router(kpis_router, tags=["kpis"])
api_router.include_router(tendencias_router, tags=["tendencias"])
api_router.include_router(cobertura_router, tags=["cobertura"])
api_router.include_router(chat_router, tags=["chat"])

# Endpoint de saúde para verificação
@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

# Endpoint genérico para carregar qualquer arquivo de dados
@api_router.get("/data/{filename}", tags=["data"])
async def get_data_file(filename: str):
    try:
        # Adicionar extensão .json se não estiver presente
        if not filename.endswith('.json'):
            filename += '.json'
            
        # Procurar e carregar o arquivo
        data = find_and_load_json_file(filename)
        if data:
            return data
        
        # Se não encontrou, retornar erro
        raise HTTPException(
            status_code=404, 
            detail=f"Arquivo {filename} não encontrado"
        )
    except Exception as e:
        logger.error(f"Erro ao processar requisição para {filename}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno ao processar {filename}: {str(e)}"
        )

# Função para localizar e carregar dados de qualquer arquivo
def find_and_load_json_file(filename):
    """
    Tenta encontrar e carregar um arquivo JSON de várias possíveis localizações
    Args:
        filename: Nome do arquivo (sem o caminho)
    Returns:
        Dict: Conteúdo do arquivo JSON ou None se não encontrado
    """
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
                return data
        except Exception as e:
            logger.error(f"Erro ao ler arquivo {data_file}: {e}")
    
    return None

# Endpoint para obter o status do sistema
@api_router.get("/status", tags=["system"])
async def get_status():
    try:
        # Procurar e carregar arquivo de status
        status_data = find_and_load_json_file("status.json")
        if status_data:
            return status_data
            
        # Status simulado se não encontrou arquivo
        return {
            "servidor": "online",
            "cache": "atualizado",
            "ultima_atualizacao": "2025-06-29T10:15:30Z",
            "servicos": {
                "coleta": "ativo",
                "analise": "ativo",
                "alerta": "ativo"
            },
            "metricas": {
                "entidades_monitoradas": 157,
                "dados_coletados_mb": 1230,
                "alertas_ativos": 3
            }
        }
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao verificar status: {str(e)}")

# Endpoint para obter dados de cobertura
@api_router.get("/cobertura", tags=["metrics"])
async def get_cobertura():
    try:
        # Verificar se existe arquivo de cobertura
        cobertura_path = "dados/cobertura.json"
        if os.path.exists(cobertura_path):
            try:
                with open(cobertura_path, 'r') as file:
                    cobertura_data = json.load(file)
                    return cobertura_data
            except Exception as e:
                logger.error(f"Erro ao ler arquivo de cobertura: {e}")
        
        # Gerar dados simulados de cobertura
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
            }
        }
    except Exception as e:
        logger.error(f"Erro ao obter dados de cobertura: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao obter dados de cobertura: {str(e)}")

# Endpoint para obter KPIs gerais
@api_router.get("/kpis", tags=["metrics"])
async def get_kpis():
    try:
        # Verificar se existe arquivo de KPIs
        kpis_path = "dados/kpis.json"
        if os.path.exists(kpis_path):
            try:
                with open(kpis_path, 'r') as file:
                    kpis_data = json.load(file)
                    return kpis_data
            except Exception as e:
                logger.error(f"Erro ao ler arquivo de KPIs: {e}")
        
        # Gerar dados simulados de KPIs
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
                "servicos_disponiveis": lambda: random.randint(int(40 * 0.9), 60),
                "tendencia": round(random.uniform(-1, 1), 2),
                "historico": [98.5, 98.7, 99.1, 99.3, 99.5, 99.7]
            },
            "erros": {
                "taxa_erro": round(random.uniform(0.1, 3.0), 2),
                "tendencia": round(random.uniform(-20, 5), 1),
                "total_requisicoes": random.randint(100000, 500000),
                "requisicoes_com_erro": lambda: random.randint(int(100000 * 0.001), int(500000 * 0.03)),
                "historico": [2.5, 2.2, 1.8, 1.5, 1.2, 0.8]
            },
            "throughput": {
                "requisicoes_por_minuto": random.randint(1000, 5000),
                "tendencia": round(random.uniform(-5, 15), 1),
                "pico": random.randint(5000, 10000),
                "historico": [2200, 2500, 2800, 3100, 3500, 3800]
            }
        }
    except Exception as e:
        logger.error(f"Erro ao obter KPIs: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao obter KPIs: {str(e)}")

# Endpoint para obter dados de tendências
@api_router.get("/tendencias", tags=["metrics"])
async def get_tendencias():
    try:
        # Verificar se existe arquivo de tendências
        tendencias_path = "dados/tendencias.json"
        if os.path.exists(tendencias_path):
            try:
                with open(tendencias_path, 'r') as file:
                    tendencias_data = json.load(file)
                    return tendencias_data
            except Exception as e:
                logger.error(f"Erro ao ler arquivo de tendências: {e}")
        
        # Gerar dados simulados de tendências
        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"]
        return {
            "apdex": {
                "labels": meses,
                "series": [
                    {
                        "name": "Web",
                        "data": [0.72, 0.75, 0.78, 0.82, 0.85, 0.87]
                    },
                    {
                        "name": "Mobile",
                        "data": [0.68, 0.71, 0.75, 0.79, 0.82, 0.84]
                    },
                    {
                        "name": "API",
                        "data": [0.81, 0.83, 0.84, 0.86, 0.88, 0.91]
                    }
                ]
            },
            "erros": {
                "labels": meses,
                "series": [
                    {
                        "name": "Erros por minuto",
                        "data": [42, 38, 35, 30, 25, 18]
                    }
                ]
            },
            "tempos_resposta": {
                "labels": meses,
                "series": [
                    {
                        "name": "Web (ms)",
                        "data": [320, 310, 290, 275, 260, 240]
                    },
                    {
                        "name": "Mobile (ms)",
                        "data": [380, 360, 340, 330, 315, 300]
                    },
                    {
                        "name": "API (ms)",
                        "data": [120, 115, 110, 105, 100, 95]
                    }
                ]
            },
            "throughput": {
                "labels": meses,
                "series": [
                    {
                        "name": "Requisições/min",
                        "data": [2200, 2500, 2800, 3100, 3400, 3800]
                    }
                ]
            },
            "usos_recursos": {
                "labels": meses,
                "series": [
                    {
                        "name": "CPU (%)",
                        "data": [65, 68, 72, 75, 78, 72]
                    },
                    {
                        "name": "Memória (%)",
                        "data": [58, 62, 68, 72, 75, 70]
                    },
                    {
                        "name": "Disco (%)",
                        "data": [45, 48, 52, 55, 58, 62]
                    }
                ]
            }
        }
    except Exception as e:
        logger.error(f"Erro ao obter tendências: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao obter tendências: {str(e)}")

# Endpoint para resumo geral
@api_router.get("/resumo-geral", tags=["dashboard"])
async def get_resumo_geral():
    try:
        # Verificar se existe arquivo de resumo
        resumo_path = "dados/resumo-geral.json"
        if os.path.exists(resumo_path):
            try:
                with open(resumo_path, 'r') as file:
                    resumo_data = json.load(file)
                    return resumo_data
            except Exception as e:
                logger.error(f"Erro ao ler arquivo de resumo: {e}")
        
        # Gerar dados simulados de resumo geral
        return {
            "status_geral": random.choice(["SAUDÁVEL", "ATENÇÃO", "CRÍTICO"]),
            "alertas_ativos": random.randint(0, 5),
            "entidades_monitoradas": random.randint(150, 200),
            "indicadores": {
                "apdex": round(random.uniform(0.7, 0.95), 2),
                "erro": round(random.uniform(0.1, 3.0), 2),
                "latencia": round(random.uniform(0.1, 2.0), 2),
                "throughput": random.randint(1000, 5000),
            },
            "entidades_por_status": {
                "saudaveis": random.randint(100, 150),
                "atencao": random.randint(10, 30),
                "criticas": random.randint(0, 10)
            },
            "principais_alertas": [
                {
                    "entidade": "api-gateway",
                    "severidade": "CRÍTICO",
                    "mensagem": "Latência elevada nas chamadas externas",
                    "desde": "2025-06-29T08:15:30Z"
                },
                {
                    "entidade": "payment-service",
                    "severidade": "ATENÇÃO",
                    "mensagem": "Taxa de erro acima do limiar",
                    "desde": "2025-06-29T09:30:00Z"
                },
                {
                    "entidade": "user-db",
                    "severidade": "ATENÇÃO",
                    "mensagem": "Uso de CPU elevado",
                    "desde": "2025-06-28T23:45:10Z"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao obter resumo geral: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao obter resumo geral: {str(e)}")
