#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script simplificado para inserir dados de exemplo do New Relic no cache.
Este script simula a integração de dados reais para demonstração.
"""

import os
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_cache_file(filename, data, cache_dirs=None):
    """
    Atualiza um arquivo de cache com novos dados
    
    Args:
        filename: Nome do arquivo de cache (sem o caminho)
        data: Dados a serem salvos (objeto que pode ser serializado para JSON)
        cache_dirs: Lista de diretórios de cache onde salvar os dados
                   Se None, usa os diretórios padrão ['backend/cache', 'cache']
                   
    Returns:
        bool: True se o cache foi atualizado com sucesso, False caso contrário
    """
    if cache_dirs is None:
        cache_dirs = ["backend/cache", "cache"]
        
    success = False
    
    for cache_dir in cache_dirs:
        try:
            # Garantir que o diretório existe
            os.makedirs(cache_dir, exist_ok=True)
            
            # Caminho completo para o arquivo de cache
            cache_path = os.path.join(cache_dir, filename)
            
            # Salvar os dados em formato JSON
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"✅ Cache atualizado com sucesso: {cache_path}")
            success = True
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar cache {cache_dir}/{filename}: {e}")
    
    return success

def criar_dados_reais_exemplo():
    """
    Cria dados de exemplo que seriam obtidos de uma integração real com o New Relic
    
    Returns:
        dict: Conjunto de dados de exemplo
    """
    # Dados de Kubernetes
    kubernetes_data = {
        "summary": {
            "clusters": 3,
            "nodes": 15,
            "pods": 67,
            "avg_cpu_usage": 58,
            "avg_memory_usage": 62,
            "issues": 5,
            "status": "warning",
            "timestamp": datetime.now().isoformat()
        },
        "clusters": [
            {
                "name": "prod-east-cluster-1",
                "version": "1.25.3",
                "status": "warning",
                "nodes": 6,
                "pods": 34,
                "cpu_usage": 72,
                "memory_usage": 68,
                "issues": 2,
                "provider": "AWS",
                "region": "us-east-1",
                "last_updated": datetime.now().isoformat()
            },
            {
                "name": "prod-west-cluster-1",
                "version": "1.25.3",
                "status": "healthy",
                "nodes": 5,
                "pods": 22,
                "cpu_usage": 54,
                "memory_usage": 61,
                "issues": 0,
                "provider": "AWS", 
                "region": "us-west-2",
                "last_updated": datetime.now().isoformat()
            },
            {
                "name": "staging-cluster-1",
                "version": "1.26.1",
                "status": "warning",
                "nodes": 4,
                "pods": 11,
                "cpu_usage": 48,
                "memory_usage": 57,
                "issues": 3,
                "provider": "GCP",
                "region": "us-central1",
                "last_updated": datetime.now().isoformat()
            }
        ],
        "nodes": [
            # Nós para prod-east-cluster-1
            {
                "name": "prod-east-node-1",
                "cluster": "prod-east-cluster-1",
                "status": "healthy",
                "cpu_cores": 8,
                "cpu_usage": 65,
                "memory_total": 32,
                "memory_usage": 72,
                "pods_scheduled": 12,
                "pods_capacity": 15,
                "instance_type": "m5.2xlarge",
                "zone": "us-east-1a"
            },
            {
                "name": "prod-east-node-2", 
                "cluster": "prod-east-cluster-1",
                "status": "warning",
                "cpu_cores": 8,
                "cpu_usage": 88,
                "memory_total": 32,
                "memory_usage": 92,
                "pods_scheduled": 14,
                "pods_capacity": 15,
                "instance_type": "m5.2xlarge",
                "zone": "us-east-1b"
            },
            # Alguns nós adicionais para outros clusters
            {
                "name": "prod-west-node-1",
                "cluster": "prod-west-cluster-1",
                "status": "healthy",
                "cpu_cores": 8,
                "cpu_usage": 45,
                "memory_total": 32,
                "memory_usage": 58,
                "pods_scheduled": 8,
                "pods_capacity": 15,
                "instance_type": "m5.2xlarge",
                "zone": "us-west-2a"
            },
            {
                "name": "staging-node-1",
                "cluster": "staging-cluster-1",
                "status": "warning", 
                "cpu_cores": 4,
                "cpu_usage": 78,
                "memory_total": 16,
                "memory_usage": 82,
                "pods_scheduled": 6,
                "pods_capacity": 10,
                "instance_type": "n2-standard-4",
                "zone": "us-central1-a"
            }
        ],
        "pods": [
            # Alguns pods com problemas
            {
                "name": "api-gateway-7d8f9c5b5d-abcd1",
                "namespace": "production",
                "status": "Error",
                "node": "prod-east-node-2",
                "cluster": "prod-east-cluster-1", 
                "cpu_request": 2,
                "cpu_usage": 2.8,
                "memory_request": 4,
                "memory_usage": 3.9,
                "restart_count": 5,
                "age": 72,
                "error": "OOMKilled"
            },
            {
                "name": "order-service-6b7d8f9c5-ef123",
                "namespace": "production",
                "status": "CrashLoopBackOff",
                "node": "prod-east-node-2",
                "cluster": "prod-east-cluster-1",
                "cpu_request": 1,
                "cpu_usage": 0.2,
                "memory_request": 2,
                "memory_usage": 0.8,
                "restart_count": 12,
                "age": 36,
                "error": "Error code 1"
            },
            # Alguns pods normais
            {
                "name": "product-service-5a6b7c8d9-12345",
                "namespace": "production", 
                "status": "Running",
                "node": "prod-east-node-1",
                "cluster": "prod-east-cluster-1",
                "cpu_request": 1,
                "cpu_usage": 0.7,
                "memory_request": 2,
                "memory_usage": 1.8,
                "restart_count": 0,
                "age": 120,
                "error": None
            }
        ]
    }

    # Dados de infraestrutura
    infrastructure_data = {
        "summary": {
            "hosts": 25,
            "services": 42,
            "alerts": 7,
            "avg_cpu": 68,
            "avg_memory": 72,
            "avg_disk": 65,
            "status": "warning",
            "timestamp": datetime.now().isoformat()
        },
        "hosts": [
            {
                "id": "i-0abc123def456789",
                "name": "app-server-01",
                "type": "EC2",
                "status": "warning",
                "cpu": {
                    "cores": 16,
                    "usage_percent": 78
                },
                "memory": {
                    "total_gb": 64,
                    "used_gb": 48.2,
                    "usage_percent": 75.3
                },
                "disk": {
                    "total_gb": 500,
                    "used_gb": 350,
                    "usage_percent": 70
                },
                "network": {
                    "in_mbps": 125.6,
                    "out_mbps": 87.3
                },
                "region": "us-east-1",
                "instance_type": "r5.4xlarge",
                "apps": ["api-gateway", "auth-service"]
            },
            {
                "id": "i-9876543210abcdef",
                "name": "db-server-01",
                "type": "RDS",
                "status": "critical",
                "cpu": {
                    "cores": 32,
                    "usage_percent": 92
                },
                "memory": {
                    "total_gb": 128,
                    "used_gb": 120.5,
                    "usage_percent": 94.1
                },
                "disk": {
                    "total_gb": 2000,
                    "used_gb": 1820,
                    "usage_percent": 91
                },
                "network": {
                    "in_mbps": 75.2,
                    "out_mbps": 120.8
                },
                "region": "us-east-1",
                "instance_type": "db.r5.8xlarge",
                "apps": ["postgres-main"]
            },
            {
                "id": "i-fedcba9876543210",
                "name": "queue-server-01", 
                "type": "EC2",
                "status": "healthy",
                "cpu": {
                    "cores": 8,
                    "usage_percent": 45
                },
                "memory": {
                    "total_gb": 32,
                    "used_gb": 18.6,
                    "usage_percent": 58.1
                },
                "disk": {
                    "total_gb": 250,
                    "used_gb": 120,
                    "usage_percent": 48
                },
                "network": {
                    "in_mbps": 65.3,
                    "out_mbps": 42.8
                },
                "region": "us-east-1",
                "instance_type": "c5.2xlarge",
                "apps": ["rabbitmq", "kafka"]
            }
        ],
        "alerts": [
            {
                "id": "alert-12345",
                "host": "db-server-01",
                "severity": "critical",
                "message": "Database CPU usage above 90% for 15 minutes",
                "time": (datetime.now().timestamp() - 1200),
                "status": "open"
            },
            {
                "id": "alert-12346",
                "host": "app-server-01",
                "severity": "warning",
                "message": "Memory usage above 75% for 30 minutes",
                "time": (datetime.now().timestamp() - 2400),
                "status": "open"
            },
            {
                "id": "alert-12347",
                "host": "db-server-01",
                "severity": "critical",
                "message": "Disk usage above 90%, only 180GB remaining",
                "time": (datetime.now().timestamp() - 600),
                "status": "open"
            }
        ]
    }
    
    # Dados de topologia de serviços
    topology_data = {
        "summary": {
            "nodes": 12,
            "edges": 18,
            "critical_services": 2,
            "warning_services": 3,
            "healthy_services": 7,
            "timestamp": datetime.now().isoformat()
        },
        "nodes": [
            {
                "id": "api-gateway",
                "name": "API Gateway",
                "type": "service",
                "status": "warning",
                "metrics": {
                    "apdex": 0.82,
                    "error_rate": 0.03,
                    "response_time": 380,
                    "throughput": 120
                },
                "technology": "Node.js",
                "environment": "production"
            },
            {
                "id": "user-service",
                "name": "User Service",
                "type": "service",
                "status": "healthy",
                "metrics": {
                    "apdex": 0.95,
                    "error_rate": 0.005,
                    "response_time": 125,
                    "throughput": 85
                },
                "technology": "Java",
                "environment": "production"
            },
            {
                "id": "order-service",
                "name": "Order Service",
                "type": "service",
                "status": "critical",
                "metrics": {
                    "apdex": 0.65,
                    "error_rate": 0.08,
                    "response_time": 890,
                    "throughput": 75
                },
                "technology": "Java",
                "environment": "production"
            },
            {
                "id": "payment-service",
                "name": "Payment Service",
                "type": "service",
                "status": "healthy",
                "metrics": {
                    "apdex": 0.92,
                    "error_rate": 0.01,
                    "response_time": 210,
                    "throughput": 60
                },
                "technology": "Go",
                "environment": "production"
            },
            {
                "id": "product-service",
                "name": "Product Service",
                "type": "service",
                "status": "healthy",
                "metrics": {
                    "apdex": 0.94,
                    "error_rate": 0.008,
                    "response_time": 175,
                    "throughput": 95
                },
                "technology": "Python",
                "environment": "production"
            },
            {
                "id": "inventory-service",
                "name": "Inventory Service",
                "type": "service",
                "status": "warning",
                "metrics": {
                    "apdex": 0.78,
                    "error_rate": 0.025,
                    "response_time": 450,
                    "throughput": 50
                },
                "technology": "Java",
                "environment": "production"
            },
            {
                "id": "notification-service",
                "name": "Notification Service",
                "type": "service",
                "status": "healthy",
                "metrics": {
                    "apdex": 0.96,
                    "error_rate": 0.003,
                    "response_time": 95,
                    "throughput": 40
                },
                "technology": "Node.js",
                "environment": "production"
            },
            {
                "id": "analytics-service",
                "name": "Analytics Service",
                "type": "service",
                "status": "healthy",
                "metrics": {
                    "apdex": 0.91,
                    "error_rate": 0.012,
                    "response_time": 320,
                    "throughput": 35
                },
                "technology": "Python",
                "environment": "production"
            },
            {
                "id": "recommendation-service",
                "name": "Recommendation Service",
                "type": "service",
                "status": "critical",
                "metrics": {
                    "apdex": 0.68,
                    "error_rate": 0.065,
                    "response_time": 1250,
                    "throughput": 25
                },
                "technology": "Python",
                "environment": "production"
            }
        ],
        "links": [
            {"source": "api-gateway", "target": "user-service", "calls_per_minute": 75, "error_rate": 0.01, "latency_ms": 45},
            {"source": "api-gateway", "target": "product-service", "calls_per_minute": 90, "error_rate": 0.008, "latency_ms": 55},
            {"source": "api-gateway", "target": "order-service", "calls_per_minute": 60, "error_rate": 0.04, "latency_ms": 75},
            {"source": "order-service", "target": "payment-service", "calls_per_minute": 55, "error_rate": 0.06, "latency_ms": 120},
            {"source": "order-service", "target": "inventory-service", "calls_per_minute": 45, "error_rate": 0.02, "latency_ms": 85},
            {"source": "order-service", "target": "notification-service", "calls_per_minute": 30, "error_rate": 0.005, "latency_ms": 40},
            {"source": "payment-service", "target": "notification-service", "calls_per_minute": 20, "error_rate": 0.002, "latency_ms": 35},
            {"source": "api-gateway", "target": "analytics-service", "calls_per_minute": 30, "error_rate": 0.01, "latency_ms": 60},
            {"source": "product-service", "target": "recommendation-service", "calls_per_minute": 25, "error_rate": 0.05, "latency_ms": 350}
        ]
    }

    return {
        "kubernetes": kubernetes_data,
        "infrastructure": infrastructure_data,
        "topology": topology_data
    }

def main():
    """Função principal para inserir dados de exemplo do New Relic"""
    print("\n" + "="*60)
    print("INSERINDO DADOS DE EXEMPLO DO NEW RELIC")
    print("="*60)
    
    # Criar dados de exemplo
    dados = criar_dados_reais_exemplo()
    
    # Salvar nos arquivos de cache
    update_cache_file("kubernetes_metrics.json", dados["kubernetes"])
    update_cache_file("infrastructure_detailed.json", dados["infrastructure"])
    update_cache_file("service_topology.json", dados["topology"])
    
    # Gerar relatório de integração simulada
    relatorio = {
        "timestamp": datetime.now().isoformat(),
        "modo": "real (simulado para demonstração)",
        "status_cache": {}
    }
    
    # Verificar o status dos arquivos de cache
    cache_files = {
        "kubernetes": "kubernetes_metrics.json",
        "infrastructure": "infrastructure_detailed.json",
        "topology": "service_topology.json"
    }
    
    cache_dirs = ["backend/cache", "cache"]
    
    for tipo, arquivo in cache_files.items():
        status_arquivo = {"existe": False, "tamanho": 0, "ultima_modificacao": None}
        
        for dir_path in cache_dirs:
            caminho_completo = os.path.join(dir_path, arquivo)
            if os.path.exists(caminho_completo):
                status_arquivo["existe"] = True
                status_arquivo["tamanho"] = os.path.getsize(caminho_completo) // 1024  # KB
                status_arquivo["ultima_modificacao"] = datetime.fromtimestamp(
                    os.path.getmtime(caminho_completo)).isoformat()
                break
                
        relatorio["status_cache"][tipo] = status_arquivo
    
    # Salvar o relatório
    try:
        with open("relatorio_integracao_dados_reais.json", 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de integração: {e}")
    
    print("\n✅ Dados de exemplo do New Relic inseridos com sucesso!")
    print("\nOs seguintes arquivos de cache foram atualizados:")
    
    for tipo, status in relatorio["status_cache"].items():
        if status["existe"]:
            print(f"  - {tipo}: {status['tamanho']} KB")
    
    print("\nAgora você pode iniciar o sistema com os dados de exemplo:")
    print("  python iniciar_sistema_com_dados_reais.py")
    
    print("\n" + "="*60)
    
if __name__ == "__main__":
    main()
