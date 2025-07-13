"""
Módulo para integração avançada dos agentes com sistemas externos.
Este módulo adiciona capacidades de integração com Azure, Kubernetes,
Grafana, Prometheus e outros sistemas de monitoramento.
"""

import os
import sys
import logging
import json
import requests
import importlib
import traceback
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExternalIntegrations:
    """
    Gerencia integrações entre os agentes e sistemas externos.
    """
    
    def __init__(self, config_path=None):
        """
        Inicializa o gerenciador de integrações.
        
        Args:
            config_path (str, optional): Caminho para o arquivo de configuração
        """
        if config_path is None:
            # Tentar localizar o arquivo de configuração padrão
            default_paths = [
                "config/integrations.json", 
                "core_inteligente/config/integrations.json",
                "integrations.json"
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    config_path = path
                    break
        
        self.config = self._load_config(config_path)
        self.integrations = {}
        self._initialize_integrations()
    
    def _load_config(self, config_path):
        """
        Carrega as configurações de integração.
        
        Args:
            config_path (str): Caminho para o arquivo de configuração
            
        Returns:
            dict: Configurações carregadas ou configuração padrão
        """
        default_config = {
            "enabled_integrations": ["newrelic", "azure"],
            "integration_settings": {
                "newrelic": {
                    "api_key": os.environ.get("NEW_RELIC_API_KEY", ""),
                    "account_id": os.environ.get("NEW_RELIC_ACCOUNT_ID", "")
                },
                "azure": {
                    "tenant_id": os.environ.get("AZURE_TENANT_ID", ""),
                    "client_id": os.environ.get("AZURE_CLIENT_ID", ""),
                    "client_secret": os.environ.get("AZURE_CLIENT_SECRET", "")
                },
                "kubernetes": {
                    "kubeconfig": os.environ.get("KUBECONFIG", "~/.kube/config"),
                    "namespace": os.environ.get("K8S_NAMESPACE", "default")
                },
                "prometheus": {
                    "url": os.environ.get("PROMETHEUS_URL", "http://localhost:9090"),
                    "username": os.environ.get("PROMETHEUS_USERNAME", ""),
                    "password": os.environ.get("PROMETHEUS_PASSWORD", "")
                },
                "grafana": {
                    "url": os.environ.get("GRAFANA_URL", "http://localhost:3000"),
                    "api_key": os.environ.get("GRAFANA_API_KEY", "")
                }
            }
        }
        
        if not config_path or not os.path.exists(config_path):
            logger.warning(f"Arquivo de configuração não encontrado: {config_path}")
            logger.info("Usando configuração padrão")
            return default_config
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Mesclar com configurações padrão para garantir que todos os campos existam
            merged_config = default_config.copy()
            if "enabled_integrations" in config:
                merged_config["enabled_integrations"] = config["enabled_integrations"]
                
            if "integration_settings" in config:
                for integration, settings in config["integration_settings"].items():
                    if integration in merged_config["integration_settings"]:
                        merged_config["integration_settings"][integration].update(settings)
                    else:
                        merged_config["integration_settings"][integration] = settings
                        
            return merged_config
            
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {str(e)}")
            return default_config
    
    def _initialize_integrations(self):
        """
        Inicializa as integrações habilitadas na configuração.
        """
        enabled = self.config.get("enabled_integrations", [])
        
        for integration in enabled:
            try:
                method_name = f"_init_{integration}"
                if hasattr(self, method_name):
                    init_method = getattr(self, method_name)
                    self.integrations[integration] = init_method()
                    if self.integrations[integration]:
                        logger.info(f"Integração {integration} inicializada com sucesso")
                    else:
                        logger.warning(f"Falha ao inicializar integração {integration}")
                else:
                    logger.warning(f"Método de inicialização não encontrado para {integration}")
            except Exception as e:
                logger.error(f"Erro ao inicializar integração {integration}: {str(e)}")
    
    def _init_newrelic(self):
        """
        Inicializa a integração com New Relic.
        
        Returns:
            dict: Objeto de integração ou None se falhar
        """
        settings = self.config.get("integration_settings", {}).get("newrelic", {})
        api_key = settings.get("api_key", "")
        account_id = settings.get("account_id", "")
        
        if not api_key or not account_id:
            logger.warning("API key ou account ID do New Relic não configurados")
            return None
        
        # Verificar conexão com New Relic
        try:
            headers = {
                "Api-Key": api_key,
                "Content-Type": "application/json"
            }
            url = f"https://api.newrelic.com/v2/applications.json"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Erro ao conectar com New Relic: {response.status_code}")
                logger.error(response.text)
                return None
            
            return {
                "api_key": api_key,
                "account_id": account_id,
                "headers": headers,
                "base_url": "https://api.newrelic.com/v2",
                "graph_url": "https://api.newrelic.com/graphql"
            }
            
        except Exception as e:
            logger.error(f"Erro ao inicializar integração com New Relic: {str(e)}")
            return None
    
    def _init_azure(self):
        """
        Inicializa a integração com Azure.
        
        Returns:
            dict: Objeto de integração ou None se falhar
        """
        settings = self.config.get("integration_settings", {}).get("azure", {})
        tenant_id = settings.get("tenant_id", "")
        client_id = settings.get("client_id", "")
        client_secret = settings.get("client_secret", "")
        
        if not tenant_id or not client_id or not client_secret:
            logger.warning("Credenciais do Azure não configuradas completamente")
            return None
        
        # Verificar se as bibliotecas do Azure estão disponíveis
        try:
            from azure.identity import ClientSecretCredential
            from azure.mgmt.compute import ComputeManagementClient
            
            # Tentar autenticar no Azure
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            
            return {
                "tenant_id": tenant_id,
                "client_id": client_id,
                "credential": credential
            }
            
        except ImportError:
            logger.error("Bibliotecas Azure não estão instaladas. Instale azure-identity e azure-mgmt-compute")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao inicializar integração com Azure: {str(e)}")
            return None
    
    def _init_kubernetes(self):
        """
        Inicializa a integração com Kubernetes.
        
        Returns:
            dict: Objeto de integração ou None se falhar
        """
        settings = self.config.get("integration_settings", {}).get("kubernetes", {})
        kubeconfig = settings.get("kubeconfig", "~/.kube/config")
        namespace = settings.get("namespace", "default")
        
        kubeconfig = os.path.expanduser(kubeconfig)
        
        if not os.path.exists(kubeconfig):
            logger.warning(f"Arquivo kubeconfig não encontrado: {kubeconfig}")
            return None
        
        # Verificar se as bibliotecas do Kubernetes estão disponíveis
        try:
            from kubernetes import client, config
            
            # Carregar configuração do Kubernetes
            config.load_kube_config(kubeconfig)
            v1 = client.CoreV1Api()
            
            # Testar conexão
            try:
                v1.list_namespaced_pod(namespace=namespace, limit=1)
                
                return {
                    "api": v1,
                    "namespace": namespace,
                    "apps_api": client.AppsV1Api(),
                    "batch_api": client.BatchV1Api()
                }
                
            except Exception as e:
                logger.error(f"Erro ao conectar com Kubernetes: {str(e)}")
                return None
                
        except ImportError:
            logger.error("Biblioteca do Kubernetes não está instalada. Instale kubernetes")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao inicializar integração com Kubernetes: {str(e)}")
            return None
    
    def _init_prometheus(self):
        """
        Inicializa a integração com Prometheus.
        
        Returns:
            dict: Objeto de integração ou None se falhar
        """
        settings = self.config.get("integration_settings", {}).get("prometheus", {})
        url = settings.get("url", "http://localhost:9090")
        username = settings.get("username", "")
        password = settings.get("password", "")
        
        # Verificar conexão com Prometheus
        try:
            auth = None
            if username and password:
                auth = (username, password)
                
            response = requests.get(f"{url}/api/v1/status/buildinfo", auth=auth)
            
            if response.status_code != 200:
                logger.error(f"Erro ao conectar com Prometheus: {response.status_code}")
                return None
            
            return {
                "url": url,
                "auth": auth
            }
            
        except Exception as e:
            logger.error(f"Erro ao inicializar integração com Prometheus: {str(e)}")
            return None
    
    def _init_grafana(self):
        """
        Inicializa a integração com Grafana.
        
        Returns:
            dict: Objeto de integração ou None se falhar
        """
        settings = self.config.get("integration_settings", {}).get("grafana", {})
        url = settings.get("url", "http://localhost:3000")
        api_key = settings.get("api_key", "")
        
        if not api_key:
            logger.warning("API key do Grafana não configurada")
            return None
        
        # Verificar conexão com Grafana
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(f"{url}/api/health", headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Erro ao conectar com Grafana: {response.status_code}")
                return None
            
            return {
                "url": url,
                "headers": headers
            }
            
        except Exception as e:
            logger.error(f"Erro ao inicializar integração com Grafana: {str(e)}")
            return None
    
    def get_integration(self, name):
        """
        Obtém uma integração pelo nome.
        
        Args:
            name (str): Nome da integração
            
        Returns:
            dict: Objeto de integração ou None se não encontrado
        """
        return self.integrations.get(name)
    
    def list_integrations(self):
        """
        Lista todas as integrações disponíveis.
        
        Returns:
            dict: Dicionário com status das integrações
        """
        result = {}
        
        for name in self.config.get("enabled_integrations", []):
            result[name] = {
                "enabled": True,
                "initialized": name in self.integrations and self.integrations[name] is not None
            }
            
        return result
    
    def query_newrelic(self, nrql_query):
        """
        Executa uma consulta NRQL no New Relic.
        
        Args:
            nrql_query (str): Consulta NRQL
            
        Returns:
            dict: Resultados da consulta ou erro
        """
        if "newrelic" not in self.integrations or not self.integrations["newrelic"]:
            return {"error": "Integração com New Relic não inicializada"}
        
        integration = self.integrations["newrelic"]
        account_id = integration["account_id"]
        
        try:
            headers = integration["headers"]
            payload = {
                "query": f"{{actor {{account(id: {account_id}) {{nrql(query: \"{nrql_query}\") {{results}}}}}}}}"
            }
            
            response = requests.post(integration["graph_url"], json=payload, headers=headers)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Erro HTTP {response.status_code}",
                    "details": response.text
                }
            
            data = response.json()
            
            if "errors" in data:
                return {
                    "success": False,
                    "error": "Erro na consulta NRQL",
                    "details": data["errors"]
                }
            
            try:
                results = data["data"]["actor"]["account"]["nrql"]["results"]
                return {
                    "success": True,
                    "results": results
                }
            except (KeyError, TypeError):
                return {
                    "success": False,
                    "error": "Formato de resposta inesperado",
                    "details": data
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao executar consulta: {str(e)}"
            }
    
    def get_azure_resources(self, resource_type=None, resource_group=None, subscription_id=None):
        """
        Obtém recursos do Azure.
        
        Args:
            resource_type (str, optional): Tipo de recurso para filtrar
            resource_group (str, optional): Grupo de recursos para filtrar
            subscription_id (str, optional): ID da assinatura
            
        Returns:
            dict: Recursos do Azure ou erro
        """
        if "azure" not in self.integrations or not self.integrations["azure"]:
            return {"error": "Integração com Azure não inicializada"}
        
        integration = self.integrations["azure"]
        
        try:
            from azure.mgmt.resource import ResourceManagementClient
            
            if not subscription_id:
                # Tentar obter a primeira assinatura
                from azure.mgmt.subscription import SubscriptionClient
                subscription_client = SubscriptionClient(integration["credential"])
                subscriptions = list(subscription_client.subscriptions.list())
                
                if not subscriptions:
                    return {
                        "success": False,
                        "error": "Nenhuma assinatura encontrada"
                    }
                    
                subscription_id = subscriptions[0].subscription_id
            
            # Criar cliente de recursos
            resource_client = ResourceManagementClient(integration["credential"], subscription_id)
            
            # Filtrar recursos
            filters = ""
            if resource_type:
                filters = f"resourceType eq '{resource_type}'"
                
            if resource_group:
                resources = resource_client.resources.list_by_resource_group(resource_group, filter=filters)
            else:
                resources = resource_client.resources.list(filter=filters)
                
            # Converter para lista
            result = []
            for resource in resources:
                result.append({
                    "id": resource.id,
                    "name": resource.name,
                    "type": resource.type,
                    "location": resource.location,
                    "tags": resource.tags
                })
                
            return {
                "success": True,
                "subscription_id": subscription_id,
                "count": len(result),
                "resources": result
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "Bibliotecas Azure não estão instaladas"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao obter recursos do Azure: {str(e)}"
            }
    
    def query_prometheus(self, query, time=None):
        """
        Executa uma consulta no Prometheus.
        
        Args:
            query (str): Consulta PromQL
            time (str, optional): Timestamp para a consulta
            
        Returns:
            dict: Resultados da consulta ou erro
        """
        if "prometheus" not in self.integrations or not self.integrations["prometheus"]:
            return {"error": "Integração com Prometheus não inicializada"}
        
        integration = self.integrations["prometheus"]
        
        try:
            params = {"query": query}
            if time:
                params["time"] = time
                
            response = requests.get(
                f"{integration['url']}/api/v1/query",
                params=params,
                auth=integration["auth"]
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Erro HTTP {response.status_code}",
                    "details": response.text
                }
            
            data = response.json()
            
            if data["status"] != "success":
                return {
                    "success": False,
                    "error": "Erro na consulta PromQL",
                    "details": data
                }
                
            return {
                "success": True,
                "data": data["data"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao executar consulta: {str(e)}"
            }
    
    def list_kubernetes_pods(self, namespace=None, label_selector=None):
        """
        Lista pods no Kubernetes.
        
        Args:
            namespace (str, optional): Namespace para filtrar (padrão: configurado)
            label_selector (str, optional): Seletor de labels
            
        Returns:
            dict: Lista de pods ou erro
        """
        if "kubernetes" not in self.integrations or not self.integrations["kubernetes"]:
            return {"error": "Integração com Kubernetes não inicializada"}
        
        integration = self.integrations["kubernetes"]
        
        try:
            if not namespace:
                namespace = integration["namespace"]
                
            pods = integration["api"].list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            result = []
            for pod in pods.items:
                result.append({
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "ip": pod.status.pod_ip,
                    "node": pod.spec.node_name,
                    "containers": [
                        {"name": container.name, "image": container.image}
                        for container in pod.spec.containers
                    ],
                    "created_at": pod.metadata.creation_timestamp.isoformat()
                })
                
            return {
                "success": True,
                "count": len(result),
                "pods": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao listar pods: {str(e)}"
            }
    
    def get_grafana_dashboards(self):
        """
        Obtém dashboards do Grafana.
        
        Returns:
            dict: Lista de dashboards ou erro
        """
        if "grafana" not in self.integrations or not self.integrations["grafana"]:
            return {"error": "Integração com Grafana não inicializada"}
        
        integration = self.integrations["grafana"]
        
        try:
            response = requests.get(
                f"{integration['url']}/api/search?type=dash-db",
                headers=integration["headers"]
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Erro HTTP {response.status_code}",
                    "details": response.text
                }
                
            dashboards = response.json()
            
            return {
                "success": True,
                "count": len(dashboards),
                "dashboards": dashboards
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao obter dashboards: {str(e)}"
            }
    
    def register_with_agents(self):
        """
        Registra as integrações com os agentes.
        
        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        try:
            # Tentar localizar o módulo de agentes
            agent_modules = [
                "core_inteligente.agno_agent",
                "agent_s",
                "core_inteligente.agent"
            ]
            
            for module_name in agent_modules:
                try:
                    module = importlib.import_module(module_name)
                    
                    if hasattr(module, 'register_integration'):
                        module.register_integration('external_systems', self)
                        logger.info(f"Integrações registradas com o módulo {module_name}")
                        return True
                    elif hasattr(module, 'AgnoAgent'):
                        # Se for o módulo agno_agent, tentar registrar diretamente
                        if hasattr(module.AgnoAgent, 'register_integration'):
                            instance = None
                            
                            # Tentar obter uma instância existente
                            if hasattr(module, 'agent_instance'):
                                instance = module.agent_instance
                            
                            if instance:
                                instance.register_integration('external_systems', self)
                                logger.info(f"Integrações registradas com instância existente de AgnoAgent")
                                return True
                        
                        logger.warning(f"Módulo {module_name} encontrado mas não tem método register_integration")
                        
                except ImportError:
                    continue
                    
            logger.warning("Nenhum módulo de agente encontrado para registro de integrações")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao registrar integrações com agentes: {str(e)}")
            return False

# Instância global para uso fácil
try:
    integrations = ExternalIntegrations()
except Exception as e:
    logger.error(f"Erro ao inicializar integrações: {str(e)}")
    integrations = None

def main():
    """
    Função principal para uso como script.
    """
    logger.info("Inicializando integrações externas")
    
    # Criar instância das integrações
    integrations = ExternalIntegrations()
    
    # Listar integrações disponíveis
    status = integrations.list_integrations()
    logger.info(f"Status das integrações: {json.dumps(status, indent=2)}")
    
    # Registrar com agentes
    result = integrations.register_with_agents()
    logger.info(f"Registro com agentes: {'Sucesso' if result else 'Falha'}")
    
    return integrations

if __name__ == "__main__":
    main()
