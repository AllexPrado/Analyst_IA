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
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar {path}: {e}")
    
    return default_value

# Dados simulados para desenvolvimento
def generate_sample_kubernetes_data():
    """Gera dados simulados de Kubernetes para o frontend"""
    clusters = ['production-cluster', 'staging-cluster', 'development-cluster']
    namespaces = ['default', 'kube-system', 'app-namespace', 'monitoring']
    
    kubernetes_data = {
        "clusters": [],
        "nodes": [],
        "pods": [],
        "summary": {
            "total_clusters": len(clusters),
            "total_nodes": random.randint(5, 15),
            "total_pods": random.randint(30, 150),
            "healthy_pods_percent": random.randint(85, 99),
            "resource_usage": {
                "cpu": random.randint(30, 85),
                "memory": random.randint(40, 90),
                "storage": random.randint(20, 70)
            }
        }
    }
    
    # Gerar dados de clusters
    for cluster in clusters:
        node_count = random.randint(2, 6)
        pod_count = random.randint(10, 50)
        
        kubernetes_data["clusters"].append({
            "name": cluster,
            "version": f"1.{random.randint(20, 28)}.{random.randint(0, 9)}",
            "status": random.choice(["healthy", "healthy", "healthy", "warning", "critical"]),
            "nodes": node_count,
            "pods": pod_count,
            "cpu_usage": random.randint(30, 85),
            "memory_usage": random.randint(40, 90),
            "issues": random.randint(0, 5)
        })
    
    # Gerar dados de nós
    for i in range(kubernetes_data["summary"]["total_nodes"]):
        cluster = random.choice(clusters)
        kubernetes_data["nodes"].append({
            "name": f"node-{cluster}-{i+1}",
            "cluster": cluster,
            "status": random.choice(["ready", "ready", "ready", "not-ready", "cordoned"]),
            "cpu": {
                "capacity": random.choice([2, 4, 8, 16]),
                "usage_percent": random.randint(10, 95)
            },
            "memory": {
                "capacity_gb": random.choice([8, 16, 32, 64]),
                "usage_percent": random.randint(10, 95)
            },
            "pods": random.randint(5, 30),
            "conditions": [
                {
                    "type": "DiskPressure",
                    "status": random.choice(["False", "False", "False", "True"])
                },
                {
                    "type": "MemoryPressure",
                    "status": random.choice(["False", "False", "False", "True"])
                }
            ]
        })
    
    # Gerar dados de pods
    statuses = ["Running", "Running", "Running", "Running", "Pending", "Failed", "CrashLoopBackOff"]
    for i in range(10):  # Limitamos a 10 pods para não sobrecarregar a UI
        cluster = random.choice(clusters)
        namespace = random.choice(namespaces)
        status = random.choice(statuses)
        
        kubernetes_data["pods"].append({
            "name": f"pod-{namespace}-{i+1}",
            "namespace": namespace,
            "cluster": cluster,
            "status": status,
            "containers": random.randint(1, 5),
            "restarts": 0 if status == "Running" else random.randint(1, 10),
            "age_hours": random.randint(1, 720),
            "cpu_usage": random.randint(10, 95) if status == "Running" else 0,
            "memory_usage": random.randint(10, 95) if status == "Running" else 0,
            "issues": [] if status == "Running" else [random.choice(["ImagePullBackOff", "CrashLoopBackOff", "OOMKilled"])]
        })
    
    return kubernetes_data

def generate_sample_infrastructure_data():
    """Gera dados simulados de infraestrutura detalhada para o frontend"""
    server_types = ['web-server', 'api-server', 'database-server', 'cache-server', 'worker']
    regions = ['us-east', 'us-west', 'eu-central', 'ap-southeast']
    
    infra_data = {
        "servers": [],
        "summary": {
            "total_servers": random.randint(20, 50),
            "healthy_percent": random.randint(85, 99),
            "regions": len(regions),
            "resource_usage": {
                "cpu": random.randint(30, 85),
                "memory": random.randint(40, 90),
                "disk": random.randint(20, 70),
                "network": random.randint(25, 75)
            }
        },
        "alerts": []
    }
    
    # Gerar dados de servidores
    for i in range(10):  # Limitamos a 10 servidores para não sobrecarregar a UI
        server_type = random.choice(server_types)
        region = random.choice(regions)
        status = random.choice(["healthy", "healthy", "healthy", "warning", "critical"])
        
        infra_data["servers"].append({
            "id": f"srv-{region}-{i+1}",
            "name": f"{server_type}-{region}-{i+1}",
            "type": server_type,
            "region": region,
            "status": status,
            "cpu": {
                "cores": random.choice([2, 4, 8, 16, 32]),
                "usage_percent": random.randint(10, 95)
            },
            "memory": {
                "total_gb": random.choice([8, 16, 32, 64, 128]),
                "usage_percent": random.randint(10, 95)
            },
            "disk": {
                "total_gb": random.choice([100, 200, 500, 1000]),
                "usage_percent": random.randint(10, 95)
            },
            "network": {
                "throughput_mbps": random.randint(10, 1000),
                "packets_per_second": random.randint(1000, 50000)
            },
            "uptime_days": random.randint(1, 365),
            "issues": [] if status == "healthy" else [random.choice(["high_cpu", "memory_leak", "disk_full", "network_latency"])]
        })
    
    # Gerar alguns alertas
    for i in range(random.randint(1, 5)):
        server = random.choice(infra_data["servers"])
        alert_type = random.choice(["cpu", "memory", "disk", "network", "service"])
        
        infra_data["alerts"].append({
            "id": f"alert-{i+1}",
            "server_id": server["id"],
            "server_name": server["name"],
            "type": alert_type,
            "severity": random.choice(["warning", "critical"]),
            "message": f"High {alert_type} usage on {server['name']}",
            "timestamp": (datetime.now().isoformat()).split('.')[0],
            "duration_minutes": random.randint(5, 120)
        })
    
    return infra_data

def generate_sample_topology_data():
    """Gera dados simulados de topologia de serviços para o frontend"""
    services = ['frontend', 'api-gateway', 'auth-service', 'user-service', 'product-service', 'payment-service', 
               'notification-service', 'search-service', 'recommendation-engine', 'analytics-service']
    
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
            # Se não houver dados reais, gerar dados simulados
            k8s_data = generate_sample_kubernetes_data()
        
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
            # Se não houver dados reais, gerar dados simulados
            infra_data = generate_sample_infrastructure_data()
        
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
            # Se não houver dados reais, gerar dados simulados
            topo_data = generate_sample_topology_data()
        
        return topo_data
    except Exception as e:
        logger.error(f"Erro ao obter dados de topologia: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados de topologia: {str(e)}")
