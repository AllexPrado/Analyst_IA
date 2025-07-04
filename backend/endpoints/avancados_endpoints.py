from fastapi import APIRouter, HTTPException
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import random

# Configuração do logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Criar o router
router = APIRouter()

# Função para carregar dados de cache
def load_cache_data(file_name, default_value=None):
    """
    Carrega dados do cache
    
    Args:
        file_name: Nome do arquivo de cache
        default_value: Valor padrão se o arquivo não existir
    
    Returns:
        Dados do cache ou valor padrão
    """
    cache_paths = [
        os.path.join("cache", file_name),
        os.path.join("backend", "cache", file_name),
        os.path.join("..", "cache", file_name),
        os.path.join("..", "backend", "cache", file_name)
    ]
    
    for path in cache_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Dados carregados com sucesso de {path}")
                    # Verificar se temos o indicador de dados reais
                    indicator_paths = [
                        os.path.join("cache", "data_source_indicator.json"),
                        os.path.join("backend", "cache", "data_source_indicator.json"),
                        os.path.join("..", "cache", "data_source_indicator.json"),
                        os.path.join("..", "backend", "cache", "data_source_indicator.json")
                    ]
                    
                    # Adicionar timestamp para evitar dados obsoletos
                    data["timestamp"] = datetime.now().isoformat()
                    data["data_source"] = "cache"
                    
                    # Verificar o indicador de dados reais
                    for ind_path in indicator_paths:
                        if os.path.exists(ind_path):
                            try:
                                with open(ind_path, 'r', encoding='utf-8') as f_ind:
                                    indicator = json.load(f_ind)
                                    if indicator.get("using_real_data") == True:
                                        data["data_source"] = "New Relic API"
                                        logger.info("Usando dados REAIS do New Relic")
                                    break
                            except Exception as e:
                                logger.error(f"Erro ao ler indicador de dados reais: {e}")
                    
                    return data
            except Exception as e:
                logger.error(f"Erro ao carregar {path}: {e}")
    
    return default_value


    
    nodes = []
    links = []
    
    # Criar nós para cada serviço
    for service in services:
        status = random.choice(["healthy", "healthy", "healthy", "degraded", "critical"])
        apdex = round(random.uniform(0.7, 1.0), 2) if status != "critical" else round(random.uniform(0.3, 0.7), 2)
        error_rate = round(random.uniform(0, 0.5), 3) if status == "critical" else round(random.uniform(0, 0.05), 3)
        
        nodes.append({
            "id": service,
            "name": service.replace('-', ' ').title(),
            "type": "service",
            "status": status,
            "metrics": {
                "apdex": apdex,
                "response_time": round(random.uniform(10, 500), 1),
                "throughput": random.randint(10, 1000),
                "error_rate": error_rate
            }
        })
    
    # Criar relacionamentos entre serviços
    # Frontend chama API Gateway
    links.append({"source": "frontend", "target": "api-gateway", "calls_per_minute": random.randint(100, 1000), "errors": random.randint(0, 10)})
    
    # API Gateway chama diversos serviços
    for service in ['auth-service', 'user-service', 'product-service', 'search-service']:
        links.append({
            "source": "api-gateway", 
            "target": service, 
            "calls_per_minute": random.randint(50, 500), 
            "errors": random.randint(0, 5)
        })
    
    # Outros relacionamentos
    links.append({"source": "product-service", "target": "recommendation-engine", "calls_per_minute": random.randint(20, 200), "errors": random.randint(0, 3)})
    links.append({"source": "user-service", "target": "notification-service", "calls_per_minute": random.randint(10, 100), "errors": random.randint(0, 2)})
    links.append({"source": "payment-service", "target": "user-service", "calls_per_minute": random.randint(5, 50), "errors": random.randint(0, 1)})
    links.append({"source": "api-gateway", "target": "payment-service", "calls_per_minute": random.randint(30, 300), "errors": random.randint(0, 4)})
    links.append({"source": "recommendation-engine", "target": "analytics-service", "calls_per_minute": random.randint(15, 150), "errors": random.randint(0, 2)})
    
    return {
        "nodes": nodes,
        "links": links,
        "summary": {
            "total_services": len(services),
            "healthy_services": len([n for n in nodes if n["status"] == "healthy"]),
            "degraded_services": len([n for n in nodes if n["status"] == "degraded"]),
            "critical_services": len([n for n in nodes if n["status"] == "critical"]),
            "total_dependencies": len(links),
            "problematic_dependencies": len([l for l in links if l["errors"] > 0])
        }
    }

@router.get("/avancado/kubernetes", tags=["advanced"])
async def get_kubernetes_data():
    """
    Retorna dados avançados de Kubernetes
    """
    try:
        # Tentar carregar dados reais primeiro
        k8s_data = load_cache_data("kubernetes_metrics.json")
        if not k8s_data:
            raise HTTPException(status_code=404, detail="Dados reais de Kubernetes não disponíveis.")
        return k8s_data
    except Exception as e:
        logger.error(f"Erro ao obter dados de Kubernetes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados de Kubernetes: {str(e)}")

@router.get("/avancado/infraestrutura", tags=["advanced"])
async def get_infrastructure_data():
    """
    Retorna dados avançados de infraestrutura
    """
    try:
        # Tentar carregar dados reais primeiro
        infra_data = load_cache_data("infrastructure_detailed.json")
        if not infra_data:
            raise HTTPException(status_code=404, detail="Dados reais de infraestrutura não disponíveis.")
        return infra_data
    except Exception as e:
        logger.error(f"Erro ao obter dados de infraestrutura: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados de infraestrutura: {str(e)}")

@router.get("/avancado/topologia", tags=["advanced"])
async def get_topology_data():
    """
    Retorna dados de topologia de serviços
    """
    try:
        # Tentar carregar dados reais primeiro
        topo_data = load_cache_data("service_topology.json")
        if not topo_data:
            raise HTTPException(status_code=404, detail="Dados reais de topologia não disponíveis.")
        return topo_data
    except Exception as e:
        logger.error(f"Erro ao obter dados de topologia: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados de topologia: {str(e)}")
