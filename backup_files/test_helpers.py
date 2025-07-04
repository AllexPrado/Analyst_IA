"""
Helpers para testes do sistema Analyst IA.
Este módulo contém classes e funções para auxiliar em testes, 
especialmente quando as credenciais reais não estão disponíveis.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MockNewRelicCollector:
    """
    Mock do AdvancedNewRelicCollector para uso em testes quando não há API Key disponível.
    Simula as respostas do New Relic com dados de exemplo.
    """
    
    def __init__(self):
        """
        Inicializa o coletor mock com dados de exemplo.
        """
        self.mock_data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "mock_data")
        os.makedirs(self.mock_data_dir, exist_ok=True)
        
        # Dados simulados de entidades
        self.entities = {
            "APM": self._generate_mock_entities("APM", 5),
            "BROWSER": self._generate_mock_entities("BROWSER", 3),
            "INFRA": self._generate_mock_entities("INFRA", 7),
            "MOBILE": self._generate_mock_entities("MOBILE", 2),
            "KUBERNETES": self._generate_mock_entities("KUBERNETES", 2),
            "LAMBDA": self._generate_mock_entities("LAMBDA", 3),
            "DASHBOARD": self._generate_mock_entities("DASHBOARD", 4)
        }
        
        logger.info(f"MockNewRelicCollector inicializado com {sum(len(v) for v in self.entities.values())} entidades simuladas")
    
    def _generate_mock_entities(self, domain: str, count: int) -> List[Dict]:
        """
        Gera entidades simuladas para um domínio específico.
        
        Args:
            domain: Domínio das entidades
            count: Número de entidades a gerar
            
        Returns:
            Lista de entidades simuladas
        """
        entities = []
        
        for i in range(1, count + 1):
            entity_type = self._get_entity_type_for_domain(domain)
            
            entity = {
                "guid": f"mock-{domain.lower()}-{i}",
                "name": f"Mock {entity_type} {i}",
                "domain": domain,
                "entityType": entity_type,
                "reporting": True,
                "account": {
                    "id": 12345678,
                    "name": "Mock Account"
                }
            }
            
            if domain == "APM":
                entity["language"] = "python"
                entity["apmSummary"] = {
                    "apdexScore": 0.95,
                    "errorRate": 0.02,
                    "hostCount": 2,
                    "instanceCount": 3,
                    "responseTimeAverage": 250,
                    "throughput": 100
                }
            
            entities.append(entity)
            
        return entities
    
    def _get_entity_type_for_domain(self, domain: str) -> str:
        """
        Retorna um tipo de entidade apropriado para o domínio.
        
        Args:
            domain: Domínio da entidade
            
        Returns:
            Tipo de entidade
        """
        domain_type_map = {
            "APM": "APPLICATION",
            "BROWSER": "BROWSER_APPLICATION",
            "INFRA": "HOST",
            "MOBILE": "MOBILE_APPLICATION",
            "KUBERNETES": "KUBERNETES_CLUSTER",
            "LAMBDA": "AWSLAMBDAFUNCTION",
            "DASHBOARD": "DASHBOARD"
        }
        
        return domain_type_map.get(domain, "APPLICATION")
    
    def _save_mock_data(self, filename: str, data: Any) -> None:
        """
        Salva dados simulados em um arquivo para referência.
        
        Args:
            filename: Nome do arquivo
            data: Dados a serem salvos
        """
        filepath = os.path.join(self.mock_data_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Dados mock salvos em {filepath}")
        except Exception as e:
            logger.warning(f"Erro ao salvar dados mock: {e}")
    
    async def fetch_entities(self, entity_type: str = None) -> List[Dict]:
        """
        Simula a busca de entidades por tipo.
        
        Args:
            entity_type: Tipo de entidade a buscar
            
        Returns:
            Lista de entidades simuladas
        """
        if entity_type:
            # Procurar em todas as entidades por tipo
            entities = []
            for domain_entities in self.entities.values():
                for entity in domain_entities:
                    if entity["entityType"] == entity_type:
                        entities.append(entity)
            return entities
        else:
            # Retornar todas as entidades
            all_entities = []
            for domain_entities in self.entities.values():
                all_entities.extend(domain_entities)
            return all_entities
    
    async def fetch_entities_by_domain(self, domain: str) -> List[Dict]:
        """
        Simula a busca de entidades por domínio.
        
        Args:
            domain: Domínio das entidades
            
        Returns:
            Lista de entidades simuladas
        """
        return self.entities.get(domain, [])
    
    async def execute_nrql_query(self, query: str) -> Dict:
        """
        Simula a execução de uma query NRQL.
        
        Args:
            query: Query NRQL
            
        Returns:
            Resultado simulado
        """
        logger.info(f"Mock: Executando query NRQL simulada: {query}")
        
        # Diferentes resultados dependendo do tipo de query
        if "FROM SystemSample" in query:
            return {
                "results": [
                    {"hostname": "host1", "cpuPercent": 45.2, "memoryUsedBytes": 4096000000},
                    {"hostname": "host2", "cpuPercent": 32.8, "memoryUsedBytes": 3072000000}
                ]
            }
        elif "FROM Transaction" in query:
            return {
                "results": [
                    {"appName": "app1", "error_rate": 1.2, "avg_duration": 245, "p99_duration": 980},
                    {"appName": "app2", "error_rate": 0.5, "avg_duration": 125, "p99_duration": 450}
                ]
            }
        elif "FROM ContainerSample" in query:
            return {
                "results": [
                    {"containerName": "container1", "cpuPercent": 35.2, "memoryUsageBytes": 256000000},
                    {"containerName": "container2", "cpuPercent": 22.8, "memoryUsageBytes": 512000000}
                ]
            }
        elif "FROM Log" in query:
            return {
                "results": [
                    {"timestamp": 1688730000000, "message": "Application started", "level": "INFO"},
                    {"timestamp": 1688730060000, "message": "Request processed successfully", "level": "INFO"},
                    {"timestamp": 1688730120000, "message": "Database connection error", "level": "ERROR"}
                ]
            }
        else:
            # Resultado genérico
            return {
                "results": [
                    {"timestamp": 1688730000000, "value": 42.5},
                    {"timestamp": 1688730060000, "value": 43.2},
                    {"timestamp": 1688730120000, "value": 41.8}
                ]
            }
    
    async def execute_graphql_query(self, query: str, variables: Dict = None) -> Dict:
        """
        Simula a execução de uma query GraphQL.
        
        Args:
            query: Query GraphQL
            variables: Variáveis da query
            
        Returns:
            Resultado simulado
        """
        logger.info(f"Mock: Executando query GraphQL simulada")
        
        # Determinar o tipo de query baseado no conteúdo
        if "entitySearch" in query and "DASHBOARD" in query:
            return {
                "data": {
                    "actor": {
                        "entitySearch": {
                            "results": {
                                "entities": [
                                    {
                                        "guid": "mock-dashboard-1",
                                        "name": "Mock Dashboard 1",
                                        "dashboardParentGuid": None,
                                        "owner": {"email": "mock@example.com"},
                                        "permissions": "PUBLIC_READ_WRITE"
                                    },
                                    {
                                        "guid": "mock-dashboard-2",
                                        "name": "Mock Dashboard 2",
                                        "dashboardParentGuid": None,
                                        "owner": {"email": "mock@example.com"},
                                        "permissions": "PUBLIC_READ_ONLY"
                                    }
                                ],
                                "nextCursor": None
                            }
                        }
                    }
                }
            }
        elif "alertViolations" in query:
            return {
                "data": {
                    "actor": {
                        "entity": {
                            "alertViolations": {
                                "violations": [
                                    {
                                        "violationId": "mock-violation-1",
                                        "label": "High CPU Usage",
                                        "level": "CRITICAL",
                                        "openedAt": datetime.now().isoformat(),
                                        "closedAt": None,
                                        "violationUrl": "https://mock.newrelic.com/violation/1"
                                    }
                                ]
                            },
                            "alertSeverity": "CRITICAL",
                            "alertConditions": [
                                {
                                    "name": "High CPU Usage Condition",
                                    "enabled": True,
                                    "id": "mock-condition-1",
                                    "type": "STATIC"
                                }
                            ]
                        }
                    }
                }
            }
        elif "ServiceTopologyQuery" in query:
            return {
                "data": {
                    "actor": {
                        "entity": {
                            "name": "Mock Service",
                            "guid": variables.get("guid", "mock-service-1"),
                            "relatedEntities": {
                                "source": {
                                    "entity": {
                                        "name": "Source Service",
                                        "guid": "mock-service-source",
                                        "entityType": "APM_APPLICATION_ENTITY"
                                    },
                                    "relationships": []
                                },
                                "target": {
                                    "entity": {
                                        "name": "Target Service",
                                        "guid": "mock-service-target",
                                        "entityType": "APM_APPLICATION_ENTITY"
                                    },
                                    "relationships": []
                                }
                            }
                        }
                    }
                }
            }
        else:
            # Resposta genérica
            return {
                "data": {
                    "actor": {
                        "entity": {
                            "name": "Mock Entity",
                            "guid": variables.get("guid", "mock-entity-1") if variables else "mock-entity-1"
                        }
                    }
                }
            }
    
    async def get_entity_metrics(self, entity_guid: str) -> Dict:
        """
        Simula a obtenção de métricas para uma entidade.
        
        Args:
            entity_guid: GUID da entidade
            
        Returns:
            Métricas simuladas
        """
        return {
            "metrics": {
                "apdex": 0.95,
                "response_time": 235.5,
                "throughput": 105.2,
                "error_rate": 1.5
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_service_topology(self, entity_guid: str) -> Dict:
        """
        Simula a obtenção de topologia de serviço.
        
        Args:
            entity_guid: GUID da entidade
            
        Returns:
            Topologia simulada
        """
        return {
            "topologia": {
                "source": {
                    "entity": {
                        "name": "Frontend Service",
                        "guid": "mock-service-frontend"
                    }
                },
                "target": {
                    "entity": {
                        "name": "Backend Service",
                        "guid": "mock-service-backend"
                    }
                }
            },
            "dependencies_metrics": [
                {
                    "name": "api/users",
                    "spanCategory": "http",
                    "callCount": 120,
                    "avgDuration": 45.2,
                    "errorRate": 1.2
                },
                {
                    "name": "database/query",
                    "spanCategory": "datastore",
                    "callCount": 350,
                    "avgDuration": 15.7,
                    "errorRate": 0.5
                }
            ]
        }
    
    async def collect_kubernetes_metrics(self, cluster_guid: str) -> Dict:
        """
        Simula a coleta de métricas de Kubernetes.
        
        Args:
            cluster_guid: GUID do cluster
            
        Returns:
            Métricas simuladas
        """
        return {
            "cluster": {
                "overview": [
                    {
                        "clusterName": "mock-k8s-cluster",
                        "podCount": 25,
                        "deploymentCount": 8,
                        "nodeCount": 3
                    }
                ],
                "resources": [
                    {
                        "cpuUsedCores": 12.5,
                        "cpuRequestedCores": 16.0,
                        "cpuLimitCores": 20.0,
                        "memoryUsedBytes": 16000000000,
                        "memoryRequestedBytes": 20000000000,
                        "memoryLimitBytes": 32000000000
                    }
                ]
            },
            "pods": [
                {
                    "metric": "cpu_usage",
                    "data": [
                        {"podName": "app-pod-1", "cpuUsedCores": 0.8, "cpuRequestedCores": 1.0},
                        {"podName": "app-pod-2", "cpuUsedCores": 0.6, "cpuRequestedCores": 1.0}
                    ]
                },
                {
                    "metric": "memory_usage",
                    "data": [
                        {"podName": "app-pod-1", "memoryUsageBytes": 512000000, "memoryLimitBytes": 1024000000},
                        {"podName": "app-pod-2", "memoryUsageBytes": 768000000, "memoryLimitBytes": 1024000000}
                    ]
                }
            ],
            "nodes": [
                {"nodeName": "node-1", "cpuUsedCores": 4.2, "memoryUsedBytes": 6000000000, "diskUsedBytes": 120000000000},
                {"nodeName": "node-2", "cpuUsedCores": 3.8, "memoryUsedBytes": 5000000000, "diskUsedBytes": 100000000000}
            ]
        }
    
    async def collect_infrastructure_details(self) -> Dict:
        """
        Simula a coleta de dados de infraestrutura.
        
        Args:
            None
            
        Returns:
            Dados de infraestrutura simulados
        """
        return {
            "hosts": {
                "mock-host-1": {
                    "details": {"guid": "mock-host-1", "name": "server1.example.com", "entityType": "HOST"},
                    "metrics": [{"cpuPercent": 45.2, "memoryUsedPercent": 68.5, "diskUsedPercent": 72.0}],
                    "top_processes": [
                        {"process": "java", "cpuPercent": 25.6, "memoryResidentSizeBytes": 1200000000},
                        {"process": "python", "cpuPercent": 12.3, "memoryResidentSizeBytes": 800000000}
                    ]
                },
                "mock-host-2": {
                    "details": {"guid": "mock-host-2", "name": "server2.example.com", "entityType": "HOST"},
                    "metrics": [{"cpuPercent": 32.7, "memoryUsedPercent": 54.2, "diskUsedPercent": 65.8}],
                    "top_processes": [
                        {"process": "nginx", "cpuPercent": 18.9, "memoryResidentSizeBytes": 300000000},
                        {"process": "mysql", "cpuPercent": 15.4, "memoryResidentSizeBytes": 1500000000}
                    ]
                }
            },
            "containers": {
                "mock-container-1": {
                    "details": {"guid": "mock-container-1", "name": "web-frontend", "entityType": "CONTAINER"},
                    "metrics": [{"cpuPercent": 35.2, "memoryUsageBytes": 512000000, "status": "running"}]
                },
                "mock-container-2": {
                    "details": {"guid": "mock-container-2", "name": "api-backend", "entityType": "CONTAINER"},
                    "metrics": [{"cpuPercent": 28.6, "memoryUsageBytes": 768000000, "status": "running"}]
                }
            },
            "services_topology": {
                "mock-service-1": {
                    "entity": {"guid": "mock-service-1", "name": "WebFrontend", "entityType": "APPLICATION"},
                    "topologia": {"connections": 2, "dependencies": 3}
                },
                "mock-service-2": {
                    "entity": {"guid": "mock-service-2", "name": "APIService", "entityType": "APPLICATION"},
                    "topologia": {"connections": 3, "dependencies": 4}
                }
            }
        }
    
    async def generate_capacity_report(self) -> Dict:
        """
        Simula a geração de relatório de capacidade.
        
        Args:
            None
            
        Returns:
            Relatório de capacidade simulado
        """
        return {
            "cpu_usage": {
                "timeseries": [
                    {"hostname": "server1.example.com", "values": [35.2, 42.6, 38.9, 45.2]},
                    {"hostname": "server2.example.com", "values": [28.5, 32.7, 30.4, 33.8]}
                ],
                "stats": [
                    {"hostname": "server1.example.com", "avg_cpu": 40.5, "max_cpu": 65.8},
                    {"hostname": "server2.example.com", "avg_cpu": 31.3, "max_cpu": 52.4}
                ]
            },
            "memory_usage": {
                "timeseries": [
                    {"hostname": "server1.example.com", "values": [62.5, 68.2, 65.7, 70.3]},
                    {"hostname": "server2.example.com", "values": [48.9, 52.3, 50.7, 54.2]}
                ],
                "stats": [
                    {"hostname": "server1.example.com", "avg_memory": 66.7, "max_memory": 78.9},
                    {"hostname": "server2.example.com", "avg_memory": 51.5, "max_memory": 65.2}
                ]
            },
            "scaling_recommendations": {
                "high_usage_hosts": [
                    {
                        "hostname": "server1.example.com",
                        "resource_type": "CPU",
                        "avg_usage": 80.5,
                        "max_usage": 92.7,
                        "recommendation": "Consider scaling up CPU resources or distributing workload"
                    }
                ]
            }
        }
    
    async def analyze_dashboard(self, dashboard_guid: str) -> Dict:
        """
        Simula a análise de um dashboard.
        
        Args:
            dashboard_guid: GUID do dashboard
            
        Returns:
            Análise simulada
        """
        return {
            "details": {
                "guid": dashboard_guid,
                "name": f"Mock Dashboard {dashboard_guid[-1]}",
                "description": "Mock dashboard for testing",
                "owner": {"email": "mock@example.com", "userId": 12345}
            },
            "widgets_analysis": [
                {
                    "id": "widget-1",
                    "title": "Application Performance",
                    "type": "viz.line",
                    "nrql": "SELECT average(duration) FROM Transaction FACET appName TIMESERIES"
                },
                {
                    "id": "widget-2",
                    "title": "Error Rate",
                    "type": "viz.area",
                    "nrql": "SELECT percentage(count(*), WHERE error is true) FROM Transaction FACET appName TIMESERIES"
                }
            ],
            "all_nrql_queries": [
                "SELECT average(duration) FROM Transaction FACET appName TIMESERIES",
                "SELECT percentage(count(*), WHERE error is true) FROM Transaction FACET appName TIMESERIES",
                "SELECT count(*) FROM TransactionError FACET errorMessage LIMIT 10"
            ],
            "pages": [
                {
                    "name": "Overview",
                    "widgets": 2
                }
            ]
        }
    
    async def extract_all_dashboard_nrql(self) -> Dict:
        """
        Simula a extração de NRQL de todos os dashboards.
        
        Args:
            None
            
        Returns:
            NRQL extraído simulado
        """
        return {
            "mock-dashboard-1": {
                "name": "Mock Dashboard 1",
                "queries": [
                    "SELECT average(duration) FROM Transaction FACET appName TIMESERIES",
                    "SELECT percentage(count(*), WHERE error is true) FROM Transaction FACET appName TIMESERIES"
                ]
            },
            "mock-dashboard-2": {
                "name": "Mock Dashboard 2",
                "queries": [
                    "SELECT count(*) FROM TransactionError FACET errorMessage LIMIT 10",
                    "SELECT average(cpuPercent) FROM SystemSample FACET hostname TIMESERIES"
                ]
            }
        }
    
    async def collect_full_entity_data(self) -> Dict:
        """
        Simula a coleta completa de dados.
        
        Args:
            None
            
        Returns:
            Dados completos simulados
        """
        all_entities = await self.fetch_entities()
        entity_count = len(all_entities)
        
        result = {
            "collected_at": datetime.now().isoformat(),
            "entities": {
                "APM": await self.fetch_entities_by_domain("APM"),
                "BROWSER": await self.fetch_entities_by_domain("BROWSER"),
                "INFRA": await self.fetch_entities_by_domain("INFRA"),
                "MOBILE": await self.fetch_entities_by_domain("MOBILE")
            },
            "metrics": {},
            "logs": {"sample": [
                {"timestamp": 1688730000000, "message": "Application started", "level": "INFO"},
                {"timestamp": 1688730060000, "message": "Request processed successfully", "level": "INFO"},
                {"timestamp": 1688730120000, "message": "Database connection error", "level": "ERROR"}
            ]},
            "alerts": {"policies": [], "violations": [], "active_violations_count": 1},
            "dashboards": {"list": await self.fetch_entities(entity_type="DASHBOARD")},
            "infrastructure_details": await self.collect_infrastructure_details(),
            "capacity_report": await self.generate_capacity_report(),
            "coverage_report": {
                "total_entities": entity_count,
                "entities_by_domain": {
                    "APM": len(self.entities["APM"]),
                    "BROWSER": len(self.entities["BROWSER"]),
                    "INFRA": len(self.entities["INFRA"]),
                    "MOBILE": len(self.entities["MOBILE"]),
                    "KUBERNETES": len(self.entities["KUBERNETES"]),
                    "LAMBDA": len(self.entities["LAMBDA"])
                }
            }
        }
        
        # Salvar dados simulados para referência
        self._save_mock_data("mock_full_entity_data.json", result)
        
        return result

    async def collect_serverless_metrics(self, function_guid: str) -> Dict:
        """
        Simula a coleta de métricas de funções serverless.
        
        Args:
            function_guid: GUID da função serverless
            
        Returns:
            Métricas simuladas
        """
        return {
            "invocations": {
                "total": 1250,
                "errors": 15,
                "throttles": 3,
                "cold_starts": 42
            },
            "duration": {
                "average_ms": 387.5,
                "p95_ms": 820.3,
                "p99_ms": 1250.8,
                "min_ms": 120.2,
                "max_ms": 2450.6
            },
            "memory": {
                "configured_mb": 1024,
                "used_mb": {
                    "average": 450.8,
                    "p95": 680.2,
                    "max": 920.5
                }
            },
            "cost": {
                "estimated_monthly_usd": 45.80,
                "last_month_usd": 42.35,
                "this_month_usd": 15.20
            },
            "recent_logs": [
                {"timestamp": "2025-07-01T10:15:30Z", "message": "Function execution started", "level": "INFO"},
                {"timestamp": "2025-07-01T10:15:31Z", "message": "Processing 25 items from queue", "level": "INFO"},
                {"timestamp": "2025-07-01T10:15:32Z", "message": "Function execution completed successfully", "level": "INFO"}
            ]
        }
