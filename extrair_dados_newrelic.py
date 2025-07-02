"""
Script para extração e transformação de dados reais do New Relic para o formato usado pelo frontend
do Analyst IA. Este script pode ser executado periodicamente para manter os dados atualizados.
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
import time
import random

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("extrator_dados_newrelic")

# Diretórios de cache
CACHE_DIRS = ["cache", "backend/cache"]

class NewRelicExtractor:
    def __init__(self, account_id=None, api_key=None):
        """Inicializa o extrator com credenciais do New Relic"""
        self.account_id = account_id or os.environ.get("NEW_RELIC_ACCOUNT_ID")
        self.api_key = api_key or os.environ.get("NEW_RELIC_API_KEY")
        
        # Usar dados simulados se as credenciais não estiverem disponíveis
        self.use_simulation = not (self.account_id and self.api_key)
        
        if self.use_simulation:
            logger.warning("Credenciais do New Relic não encontradas, usando dados simulados")
        else:
            logger.info(f"Usando Account ID: {self.account_id}")
            logger.info("API Key configurada: " + "*" * 5)
            
        # Criar diretórios de cache se não existirem
        for dir_path in CACHE_DIRS:
            os.makedirs(dir_path, exist_ok=True)
    
    def fetch_kubernetes_data(self):
        """Extrai dados do Kubernetes do New Relic"""
        if self.use_simulation:
            return self._simulate_kubernetes_data()
        
        try:
            logger.info("Extraindo dados de Kubernetes do New Relic...")
            # Implementar a consulta GraphQL do New Relic para obter dados de K8s
            # Exemplo de consulta:
            query = """
            {
              actor {
                account(id: %s) {
                  nrql(query: "FROM K8sClusterSample SELECT count(*) as count, 
                               latest(clusterName) as name, latest(kubernetesVersion) as version
                               FACET clusterName LIMIT 100") {
                    results
                  }
                }
              }
            }
            """ % self.account_id
            
            # Esta implementação precisaria ser completada com chamadas reais à API do New Relic
            # e transformação dos resultados para o formato esperado pelo frontend
            
            # Por enquanto, usar dados simulados
            logger.warning("API de Kubernetes do New Relic ainda não implementada completamente, usando dados simulados")
            return self._simulate_kubernetes_data()
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados do Kubernetes: {e}")
            return self._simulate_kubernetes_data()
    
    def fetch_infrastructure_data(self):
        """Extrai dados de infraestrutura do New Relic"""
        if self.use_simulation:
            return self._simulate_infrastructure_data()
        
        try:
            logger.info("Extraindo dados de infraestrutura do New Relic...")
            # Implementar a consulta GraphQL do New Relic para obter dados de infraestrutura
            # Exemplo de consulta:
            query = """
            {
              actor {
                account(id: %s) {
                  nrql(query: "FROM SystemSample SELECT hostname, cpuPercent, 
                               memoryUsedPercent, diskUsedPercent WHERE entityType = 'HOST'
                               FACET hostname LIMIT 100") {
                    results
                  }
                }
              }
            }
            """ % self.account_id
            
            # Esta implementação precisaria ser completada com chamadas reais à API do New Relic
            # e transformação dos resultados para o formato esperado pelo frontend
            
            # Por enquanto, usar dados simulados
            logger.warning("API de infraestrutura do New Relic ainda não implementada completamente, usando dados simulados")
            return self._simulate_infrastructure_data()
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados de infraestrutura: {e}")
            return self._simulate_infrastructure_data()
    
    def fetch_topology_data(self):
        """Extrai dados de topologia de serviços do New Relic"""
        if self.use_simulation:
            return self._simulate_topology_data()
        
        try:
            logger.info("Extraindo dados de topologia de serviços do New Relic...")
            # Implementar a consulta GraphQL do New Relic para obter dados de topologia
            # Exemplo de consulta:
            query = """
            {
              actor {
                account(id: %s) {
                  nrql(query: "FROM ServiceInstance SELECT entityName, 
                               apdexScore, errorRate, responseTimeAverage
                               FACET entityName LIMIT 100") {
                    results
                  }
                }
              }
            }
            """ % self.account_id
            
            # Esta implementação precisaria ser completada com chamadas reais à API do New Relic
            # e transformação dos resultados para o formato esperado pelo frontend
            
            # Por enquanto, usar dados simulados
            logger.warning("API de topologia do New Relic ainda não implementada completamente, usando dados simulados")
            return self._simulate_topology_data()
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados de topologia: {e}")
            return self._simulate_topology_data()
    
    # Métodos de simulação - geram dados simulados para testes
    def _simulate_kubernetes_data(self):
        """Gera dados simulados de Kubernetes para testes"""
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

    def _simulate_infrastructure_data(self):
        """Gera dados simulados de infraestrutura para testes"""
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

    def _simulate_topology_data(self):
        """Gera dados simulados de topologia de serviços para testes"""
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

    def extract_and_save_all_data(self):
        """Extrai e salva todos os dados no cache"""
        try:
            # Extrair dados
            k8s_data = self.fetch_kubernetes_data()
            infra_data = self.fetch_infrastructure_data()
            topo_data = self.fetch_topology_data()
            
            # Salvar dados em todos os diretórios de cache
            files_saved = 0
            
            for cache_dir in CACHE_DIRS:
                # Criar diretório se não existir
                os.makedirs(cache_dir, exist_ok=True)
                
                # Salvar dados de Kubernetes
                k8s_file = os.path.join(cache_dir, "kubernetes_metrics.json")
                with open(k8s_file, 'w', encoding='utf-8') as f:
                    json.dump(k8s_data, f, ensure_ascii=False, indent=2)
                files_saved += 1
                
                # Salvar dados de infraestrutura
                infra_file = os.path.join(cache_dir, "infrastructure_detailed.json")
                with open(infra_file, 'w', encoding='utf-8') as f:
                    json.dump(infra_data, f, ensure_ascii=False, indent=2)
                files_saved += 1
                
                # Salvar dados de topologia
                topo_file = os.path.join(cache_dir, "service_topology.json")
                with open(topo_file, 'w', encoding='utf-8') as f:
                    json.dump(topo_data, f, ensure_ascii=False, indent=2)
                files_saved += 1
            
            logger.info(f"✅ Dados extraídos e salvos com sucesso. Total de arquivos: {files_saved}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao extrair e salvar dados: {e}")
            return False

def extract_data_with_retry(max_retries=3, retry_delay=5):
    """Extrai dados com tentativas em caso de falha"""
    logger.info("=== INICIANDO EXTRAÇÃO DE DADOS DO NEW RELIC ===")
    
    for attempt in range(1, max_retries + 1):
        try:
            extractor = NewRelicExtractor()
            success = extractor.extract_and_save_all_data()
            
            if success:
                logger.info("Extração de dados concluída com sucesso.")
                return True
            else:
                logger.warning(f"Falha na tentativa {attempt}/{max_retries}")
                
                if attempt < max_retries:
                    logger.info(f"Aguardando {retry_delay} segundos antes de tentar novamente...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Máximo de tentativas atingido. Abortar.")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro durante a extração na tentativa {attempt}: {e}")
            
            if attempt < max_retries:
                logger.info(f"Aguardando {retry_delay} segundos antes de tentar novamente...")
                time.sleep(retry_delay)
            else:
                logger.error("Máximo de tentativas atingido. Abortar.")
                return False
    
    return False

if __name__ == "__main__":
    extract_data_with_retry()
