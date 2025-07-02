"""
Script para regenerar e validar os arquivos de cache para a infraestrutura avançada
"""

import os
import json
import random
import logging
import shutil
from datetime import datetime
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("regenerar_cache_avancado")

def create_kubernetes_data():
    """Cria dados simulados de Kubernetes para o cache"""
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

def create_infrastructure_data():
    """Cria dados simulados de infraestrutura para o cache"""
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

def create_topology_data():
    """Cria dados simulados de topologia de serviços para o cache"""
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

def regenerar_cache_avancado():
    """Regenera e valida os arquivos de cache para a infraestrutura avançada"""
    logger.info("=== REGENERANDO CACHE PARA INFRAESTRUTURA AVANÇADA ===")
    
    # Definir os caminhos para os diretórios de cache
    cache_dirs = [
        Path("backend/cache"),
        Path("cache")
    ]
    
    # Criar os diretórios se não existirem
    for dir_path in cache_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Diretório verificado: {dir_path}")
    
    # Criar dados
    logger.info("Gerando dados simulados para Kubernetes...")
    kubernetes_data = create_kubernetes_data()
    
    logger.info("Gerando dados simulados para Infraestrutura...")
    infra_data = create_infrastructure_data()
    
    logger.info("Gerando dados simulados para Topologia de Serviços...")
    topology_data = create_topology_data()
    
    # Salvar dados em arquivos
    files_created = []
    
    try:
        # Diretório principal para os arquivos
        primary_cache_dir = cache_dirs[0]
        
        # Salvar dados de Kubernetes
        kubernetes_file = primary_cache_dir / "kubernetes_metrics.json"
        with open(kubernetes_file, 'w', encoding='utf-8') as f:
            json.dump(kubernetes_data, f, ensure_ascii=False, indent=2)
        files_created.append(str(kubernetes_file))
        logger.info(f"Arquivo criado: {kubernetes_file}")
        
        # Salvar dados de Infraestrutura
        infra_file = primary_cache_dir / "infrastructure_detailed.json"
        with open(infra_file, 'w', encoding='utf-8') as f:
            json.dump(infra_data, f, ensure_ascii=False, indent=2)
        files_created.append(str(infra_file))
        logger.info(f"Arquivo criado: {infra_file}")
        
        # Salvar dados de Topologia
        topology_file = primary_cache_dir / "service_topology.json"
        with open(topology_file, 'w', encoding='utf-8') as f:
            json.dump(topology_data, f, ensure_ascii=False, indent=2)
        files_created.append(str(topology_file))
        logger.info(f"Arquivo criado: {topology_file}")
        
        # Copiar para os diretórios secundários
        if len(cache_dirs) > 1:
            for i in range(1, len(cache_dirs)):
                secondary_cache_dir = cache_dirs[i]
                
                # Copiar arquivos
                for file_name in ["kubernetes_metrics.json", "infrastructure_detailed.json", "service_topology.json"]:
                    source = primary_cache_dir / file_name
                    dest = secondary_cache_dir / file_name
                    
                    if source.exists():
                        shutil.copy(source, dest)
                        files_created.append(str(dest))
                        logger.info(f"Arquivo copiado: {dest}")
        
        logger.info(f"\n✅ {len(files_created)} arquivos de cache criados/atualizados com sucesso!")
        return True, files_created
        
    except Exception as e:
        logger.error(f"❌ Erro ao regenerar arquivos de cache: {e}")
        return False, files_created

if __name__ == "__main__":
    success, files = regenerar_cache_avancado()
    
    if success:
        print("\n=== RESUMO ===")
        print(f"Total de arquivos criados/atualizados: {len(files)}")
        for file in files:
            print(f"- {file}")
    else:
        print("\n❌ Falha na regeneração dos arquivos de cache.")
