#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from pprint import pprint

# Configurar path para importar módulos do backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Verificar se as credenciais do New Relic estão configuradas
api_key = os.environ.get("NEW_RELIC_API_KEY")
query_key = os.environ.get("NEW_RELIC_QUERY_KEY") 
account_id = os.environ.get("NEW_RELIC_ACCOUNT_ID")

# Verificar .env no diretório atual
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Carregando credenciais via dotenv")
    
    # Verificar novamente se as credenciais foram carregadas
    api_key = os.environ.get("NEW_RELIC_API_KEY") or api_key
    query_key = os.environ.get("NEW_RELIC_QUERY_KEY") or query_key
    account_id = os.environ.get("NEW_RELIC_ACCOUNT_ID") or account_id
    
    if api_key:
        print("✓ API Key do New Relic encontrada")
    if query_key:
        print("✓ Query Key do New Relic encontrada")
    if account_id:
        print("✓ Account ID do New Relic encontrado")
except ImportError:
    # Fallback para leitura manual do arquivo .env se dotenv não estiver disponível
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        print("Carregando credenciais do arquivo .env manualmente")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        if key == 'NEW_RELIC_API_KEY':
                            api_key = value
                        elif key == 'NEW_RELIC_QUERY_KEY':
                            query_key = value
                        elif key == 'NEW_RELIC_ACCOUNT_ID':
                            account_id = value
                    except ValueError:
                        continue

# Importar o coletor avançado
from utils.advanced_newrelic_collector import AdvancedNewRelicCollector

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("advanced_collector_test.log")
    ]
)

logger = logging.getLogger(__name__)

class TestReport:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
    
    def add_result(self, test_name, passed, details=None, skip_reason=None):
        status = "PASSED" if passed else "FAILED" if skip_reason is None else "SKIPPED"
        
        self.results["tests"][test_name] = {
            "status": status,
            "details": details or {},
        }
        
        if skip_reason:
            self.results["tests"][test_name]["skip_reason"] = skip_reason
            self.results["summary"]["skipped"] += 1
        elif passed:
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
            
        self.results["summary"]["total"] += 1
        
    def save_report(self, filename="advanced_collector_test_results.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
            
    def print_summary(self):
        print("\n" + "="*60)
        print(f"RESUMO DOS TESTES: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print(f"Total de testes: {self.results['summary']['total']}")
        print(f"Testes bem-sucedidos: {self.results['summary']['passed']}")
        print(f"Testes falhos: {self.results['summary']['failed']}")
        print(f"Testes ignorados: {self.results['summary']['skipped']}")
        print("="*60)
        
        # Mostrar detalhes dos testes falhos
        if self.results["summary"]["failed"] > 0:
            print("\nDetalhes dos testes falhos:")
            for test_name, test_result in self.results["tests"].items():
                if test_result["status"] == "FAILED":
                    print(f"- {test_name}")
                    if "error" in test_result["details"]:
                        print(f"  Erro: {test_result['details']['error']}")
            print("="*60)

async def test_kubernetes_metrics(collector, report):
    print("\nTestando coleta de métricas de Kubernetes...")
    
    try:
        # Buscar clusters Kubernetes
        k8s_clusters = await collector.fetch_entities(entity_type="K8S_CLUSTER")
        
        if not k8s_clusters:
            report.add_result("kubernetes_metrics", True, 
                             {"message": "Nenhum cluster Kubernetes encontrado. Teste ignorado."},
                             skip_reason="No Kubernetes clusters found")
            return
            
        # Selecionar o primeiro cluster para teste
        cluster = k8s_clusters[0]
        cluster_guid = cluster.get("guid")
        
        if not cluster_guid:
            report.add_result("kubernetes_metrics", False, 
                             {"error": "Cluster encontrado, mas sem GUID."})
            return
            
        # Coletar métricas de Kubernetes
        metrics = await collector.collect_kubernetes_metrics(cluster_guid)
        
        # Verificar se retornou alguma métrica
        if metrics and isinstance(metrics, dict) and len(metrics) > 0:
            print(f"✓ Métricas de Kubernetes coletadas para o cluster: {cluster.get('name')}")
            report.add_result("kubernetes_metrics", True, 
                             {"metrics_count": len(metrics), 
                              "cluster_name": cluster.get("name"),
                              "metrics_keys": list(metrics.keys())})
        else:
            print("✗ Não foi possível coletar métricas de Kubernetes")
            report.add_result("kubernetes_metrics", False,
                             {"error": "Nenhuma métrica encontrada", 
                              "result": metrics})
    except Exception as e:
        print(f"✗ Erro ao testar métricas de Kubernetes: {e}")
        report.add_result("kubernetes_metrics", False, {"error": str(e)})

async def test_serverless_metrics(collector, report):
    print("\nTestando coleta de métricas de funções serverless...")
    
    try:
        # Buscar funções Lambda
        lambda_functions = await collector.fetch_entities(entity_type="AWSLAMBDAFUNCTION")
        
        if not lambda_functions:
            report.add_result("serverless_metrics", True, 
                             {"message": "Nenhuma função Lambda encontrada. Teste ignorado."},
                             skip_reason="No Lambda functions found")
            return
            
        # Selecionar a primeira função para teste
        function = lambda_functions[0]
        function_guid = function.get("guid")
        
        if not function_guid:
            report.add_result("serverless_metrics", False, 
                             {"error": "Função encontrada, mas sem GUID."})
            return
            
        # Coletar métricas de funções serverless
        metrics = await collector.collect_serverless_metrics(function_guid)
        
        # Verificar se retornou alguma métrica
        if metrics and isinstance(metrics, dict) and len(metrics) > 0:
            print(f"✓ Métricas de serverless coletadas para a função: {function.get('name')}")
            report.add_result("serverless_metrics", True, 
                             {"metrics_count": len(metrics), 
                              "function_name": function.get("name"),
                              "metrics_keys": list(metrics.keys())})
        else:
            print("✗ Não foi possível coletar métricas de funções serverless")
            report.add_result("serverless_metrics", False,
                             {"error": "Nenhuma métrica encontrada", 
                              "result": metrics})
    except Exception as e:
        print(f"✗ Erro ao testar métricas de funções serverless: {e}")
        report.add_result("serverless_metrics", False, {"error": str(e)})

async def test_dashboard_analysis(collector, report):
    print("\nTestando análise de dashboards e extração de NRQL...")
    
    try:
        # Buscar dashboards
        dashboards = await collector.fetch_entities(entity_type="DASHBOARD")
        
        if not dashboards:
            report.add_result("dashboard_analysis", True, 
                             {"message": "Nenhum dashboard encontrado. Teste ignorado."},
                             skip_reason="No dashboards found")
            return
            
        # Selecionar o primeiro dashboard para teste
        dashboard = dashboards[0]
        dashboard_guid = dashboard.get("guid")
        
        if not dashboard_guid:
            report.add_result("dashboard_analysis", False, 
                             {"error": "Dashboard encontrado, mas sem GUID."})
            return
            
        # Analisar dashboard
        analysis = await collector.analyze_dashboard(dashboard_guid)
        
        # Verificar se a análise contém informações úteis
        if analysis and isinstance(analysis, dict):
            has_nrql_queries = "all_nrql_queries" in analysis and len(analysis["all_nrql_queries"]) > 0
            
            if has_nrql_queries:
                print(f"✓ Dashboard analisado com sucesso: {dashboard.get('name')}")
                print(f"  - {len(analysis.get('all_nrql_queries', []))} consultas NRQL extraídas")
                
                report.add_result("dashboard_analysis", True, 
                                 {"dashboard_name": dashboard.get("name"),
                                  "queries_count": len(analysis.get("all_nrql_queries", [])),
                                  "pages_count": len(analysis.get("pages", []))})
            else:
                print(f"✓ Dashboard analisado, mas nenhuma consulta NRQL encontrada: {dashboard.get('name')}")
                report.add_result("dashboard_analysis", True, 
                                 {"dashboard_name": dashboard.get("name"),
                                  "warning": "Nenhuma consulta NRQL encontrada"})
        else:
            print("✗ Não foi possível analisar o dashboard")
            report.add_result("dashboard_analysis", False,
                             {"error": "Análise inválida", 
                              "result": analysis})
    except Exception as e:
        print(f"✗ Erro ao testar análise de dashboard: {e}")
        report.add_result("dashboard_analysis", False, {"error": str(e)})

async def test_all_dashboard_nrql(collector, report):
    print("\nTestando extração de NRQL de todos os dashboards...")
    
    try:
        # Extrair consultas NRQL de todos os dashboards
        all_nrql = await collector.extract_all_dashboard_nrql()
        
        # Verificar se retornou informações úteis
        if all_nrql and isinstance(all_nrql, dict):
            total_dashboards = len(all_nrql)
            total_queries = sum(len(dash_data.get("queries", [])) for dash_data in all_nrql.values())
            
            print(f"✓ NRQL extraído de {total_dashboards} dashboards (total de {total_queries} consultas)")
            report.add_result("all_dashboard_nrql", True, 
                             {"dashboards_count": total_dashboards,
                              "queries_count": total_queries})
        else:
            print("✗ Não foi possível extrair NRQL dos dashboards")
            report.add_result("all_dashboard_nrql", False,
                             {"error": "Resultado inválido", 
                              "result": all_nrql})
    except Exception as e:
        print(f"✗ Erro ao extrair NRQL de dashboards: {e}")
        report.add_result("all_dashboard_nrql", False, {"error": str(e)})

async def test_infrastructure_details(collector, report):
    print("\nTestando coleta de dados avançados de infraestrutura...")
    
    try:
        # Coletar dados de infraestrutura
        infra_data = await collector.collect_infrastructure_details()
        
        # Verificar se retornou dados
        if infra_data and isinstance(infra_data, dict):
            hosts_count = len(infra_data.get("hosts", {}))
            containers_count = len(infra_data.get("containers", {}))
            topology_count = len(infra_data.get("services_topology", {}))
            
            print(f"✓ Dados de infraestrutura coletados: {hosts_count} hosts, {containers_count} containers")
            report.add_result("infrastructure_details", True, 
                             {"hosts_count": hosts_count,
                              "containers_count": containers_count,
                              "topology_entities": topology_count})
        else:
            print("✗ Não foi possível coletar dados de infraestrutura")
            report.add_result("infrastructure_details", False,
                             {"error": "Dados inválidos", 
                              "result": infra_data})
    except Exception as e:
        print(f"✗ Erro ao coletar dados de infraestrutura: {e}")
        report.add_result("infrastructure_details", False, {"error": str(e)})

async def test_capacity_report(collector, report):
    print("\nTestando geração de relatório de capacidade...")
    
    try:
        # Gerar relatório de capacidade
        capacity = await collector.generate_capacity_report()
        
        # Verificar se retornou dados
        if capacity and isinstance(capacity, dict):
            has_cpu = "cpu_usage" in capacity and len(capacity["cpu_usage"]) > 0
            has_memory = "memory_usage" in capacity and len(capacity["memory_usage"]) > 0
            has_recommendations = "scaling_recommendations" in capacity
            
            if has_cpu or has_memory:
                print(f"✓ Relatório de capacidade gerado com sucesso")
                report.add_result("capacity_report", True, 
                                 {"has_cpu_data": has_cpu,
                                  "has_memory_data": has_memory,
                                  "has_recommendations": has_recommendations})
            else:
                print(f"✓ Relatório de capacidade gerado, mas sem dados principais")
                report.add_result("capacity_report", True, 
                                 {"warning": "Relatório gerado sem dados principais de CPU ou memória"})
        else:
            print("✗ Não foi possível gerar relatório de capacidade")
            report.add_result("capacity_report", False,
                             {"error": "Relatório inválido", 
                              "result": capacity})
    except Exception as e:
        print(f"✗ Erro ao gerar relatório de capacidade: {e}")
        report.add_result("capacity_report", False, {"error": str(e)})

async def test_full_entity_data(collector, report):
    print("\nTestando coleta completa de dados...")
    
    try:
        # Iniciar tempo
        start_time = datetime.now()
        
        # Coletar todos os dados
        full_data = await collector.collect_full_entity_data()
        
        # Calcular tempo decorrido
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        # Verificar se retornou dados
        if full_data and isinstance(full_data, dict) and "error" not in full_data:
            entity_count = full_data.get("coverage_report", {}).get("total_entities", 0)
            
            print(f"✓ Coleta completa executada com sucesso em {elapsed_time:.2f} segundos")
            print(f"  - {entity_count} entidades coletadas")
            
            report.add_result("full_entity_data", True, 
                             {"elapsed_seconds": elapsed_time,
                              "entities_count": entity_count,
                              "coverage": full_data.get("coverage_report", {})})
        else:
            print("✗ Não foi possível executar coleta completa")
            error = full_data.get("error", "Dados inválidos") if isinstance(full_data, dict) else "Dados inválidos"
            report.add_result("full_entity_data", False, {"error": error})
    except Exception as e:
        print(f"✗ Erro ao executar coleta completa: {e}")
        report.add_result("full_entity_data", False, {"error": str(e)})

async def run_tests():
    report = TestReport()
    print("="*60)
    print("INICIANDO TESTES DO COLETOR AVANÇADO DO NEW RELIC")
    print("="*60)
    
    try:
        # Verificar se o usuário deseja usar dados simulados
        use_mock = os.environ.get("USE_MOCK_DATA", "").lower() == "true"
        
        if use_mock:
            print("\n⚠️ Usando coletor mock para testes com dados simulados...\n")
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            try:
                from backend.utils.test_helpers import MockNewRelicCollector
                collector = MockNewRelicCollector()
                print("✓ Coletor mock inicializado com sucesso para testes")
            except ImportError as e:
                print(f"✗ Erro ao importar MockNewRelicCollector: {e}")
                print("Certifique-se de que o arquivo backend/utils/test_helpers.py existe.")
                return
        elif not api_key:
            print("✗ Erro ao executar testes: New Relic API Key não fornecida")
            print("\nPara executar os testes, você precisa configurar as credenciais do New Relic.")
            print("Opções para configurar:")
            print("1. Defina as variáveis de ambiente NEW_RELIC_API_KEY, NEW_RELIC_QUERY_KEY e NEW_RELIC_ACCOUNT_ID")
            print("2. Crie um arquivo .env na raiz do projeto com as seguintes informações:")
            print("   NEW_RELIC_API_KEY=sua_api_key_aqui")
            print("   NEW_RELIC_QUERY_KEY=sua_query_key_aqui")
            print("   NEW_RELIC_ACCOUNT_ID=seu_account_id_aqui")
            print("\n💡 Se quiser executar testes com dados simulados, defina a variável de ambiente USE_MOCK_DATA=true")
            print("   Por exemplo: USE_MOCK_DATA=true python test_advanced_collector.py\n")
            print("   Ou consulte o arquivo ADVANCED_COLLECTOR_README.md para mais detalhes.\n")
            return
        
        if not account_id:
            print("✗ Erro ao executar testes: New Relic Account ID não fornecido")
            print("\nPara executar os testes, você precisa configurar o ID da conta do New Relic.")
            return
        
        # Inicializar o coletor
        collector = AdvancedNewRelicCollector(api_key=api_key, query_key=query_key, account_id=account_id)
        print("✓ Coletor avançado inicializado com sucesso")
        
        # Executar testes individuais
        await test_kubernetes_metrics(collector, report)
        await test_serverless_metrics(collector, report)
        await test_dashboard_analysis(collector, report)
        await test_all_dashboard_nrql(collector, report)
        await test_infrastructure_details(collector, report)
        await test_capacity_report(collector, report)
        
        # Teste de coleta completa (mais demorado, então deixamos por último)
        await test_full_entity_data(collector, report)
        
        # Salvar relatório de testes
        report.save_report()
        report.print_summary()
        
    except Exception as e:
        print(f"✗ Erro ao executar testes: {e}")
        
    print("="*60)
    print("TESTES FINALIZADOS")
    print("="*60)

if __name__ == "__main__":
    # Executar testes de forma assíncrona
    asyncio.run(run_tests())
