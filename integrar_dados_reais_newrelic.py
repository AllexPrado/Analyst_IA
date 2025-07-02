#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para integrar dados reais do New Relic ao sistema Analyst_IA.

Este script:
1. Verifica a presença das credenciais do New Relic
2. Extrai dados reais usando o coletor avançado
3. Converte os dados para o formato usado pelo frontend
4. Atualiza o cache com os dados reais
5. Gera um relatório de integração
"""

import os
import sys
import json
import logging
import argparse
import traceback
from pathlib import Path
from datetime import datetime
import asyncio
import requests
from typing import Dict, Any, List, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/integracao_dados_reais.log", mode='a')
    ]
)

logger = logging.getLogger(__name__)
os.makedirs("logs", exist_ok=True)

# Importar módulos necessários
sys.path.append("backend")
sys.path.append(".")

try:
    from backend.utils.advanced_newrelic_collector import AdvancedNewRelicCollector
    from backend.utils.cache_integration import update_cache_file
    logger.info("Módulos importados com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar módulos: {e}")
    traceback.print_exc()
    sys.exit(1)

class NewRelicIntegrador:
    def __init__(self, account_id=None, api_key=None, modo_simulado=False):
        """
        Inicializa o integrador de dados reais do New Relic
        
        Args:
            account_id: ID da conta do New Relic
            api_key: Chave de API do New Relic
            modo_simulado: Se True, usa dados simulados em vez de dados reais
        """
        self.account_id = account_id or os.environ.get("NEW_RELIC_ACCOUNT_ID")
        self.api_key = api_key or os.environ.get("NEW_RELIC_API_KEY")
        self.modo_simulado = modo_simulado
        
        if not self.account_id or not self.api_key:
            logger.warning("Credenciais do New Relic não encontradas. Usando modo simulado.")
            self.modo_simulado = True
            
        self.collector = None
        if not self.modo_simulado:
            self.collector = AdvancedNewRelicCollector(
                account_id=self.account_id,
                api_key=self.api_key
            )
            
        # Arquivos de cache para atualizar
        self.cache_files = {
            "kubernetes": "kubernetes_metrics.json",
            "infrastructure": "infrastructure_detailed.json",
            "topology": "service_topology.json",
            "apps": "applications_metrics.json",
            "serverless": "serverless_functions.json"
        }
        
        # Diretórios de cache
        self.cache_dirs = ["backend/cache", "cache"]
            
    async def extrair_dados_kubernetes(self):
        """Extrai dados reais de Kubernetes do New Relic"""
        if self.modo_simulado:
            logger.info("Modo simulado: não extraindo dados reais de Kubernetes")
            return None
            
        try:
            logger.info("Extraindo dados de Kubernetes do New Relic...")
            # Usar o coletor avançado para obter dados de Kubernetes
            dados_k8s = await self.collector.collect_kubernetes_data()
            
            # Transformar para o formato usado pelo frontend
            dados_formatados = self.formatar_dados_kubernetes(dados_k8s)
            
            logger.info(f"Dados de Kubernetes extraídos com sucesso: {len(dados_formatados.get('clusters', []))} clusters")
            return dados_formatados
        except Exception as e:
            logger.error(f"Erro ao extrair dados de Kubernetes: {e}")
            traceback.print_exc()
            return None
            
    def formatar_dados_kubernetes(self, dados_brutos):
        """Formata dados brutos de Kubernetes para o formato usado pelo frontend"""
        if not dados_brutos:
            return None
            
        # Aqui implementamos a lógica para transformar os dados brutos
        # do New Relic para o formato esperado pelo frontend
        try:
            # Esta é uma implementação simplificada
            clusters = []
            nodes = []
            pods = []
            
            # Processar dados de clusters
            for cluster in dados_brutos.get('clusters', []):
                clusters.append({
                    "name": cluster.get('name'),
                    "version": cluster.get('version'),
                    "status": self._determinar_status(cluster),
                    "nodes": cluster.get('nodeCount', 0),
                    "pods": cluster.get('podCount', 0),
                    "cpu_usage": cluster.get('cpuUsagePercent', 0),
                    "memory_usage": cluster.get('memoryUsagePercent', 0),
                    "issues": self._contar_problemas(cluster)
                })
                
            # Processar dados de nodes
            for node in dados_brutos.get('nodes', []):
                nodes.append({
                    "name": node.get('name'),
                    "cluster": node.get('clusterName'),
                    "status": self._determinar_status(node),
                    "cpu_usage": node.get('cpuUsagePercent', 0),
                    "memory_usage": node.get('memoryUsagePercent', 0),
                    "pods_count": node.get('podCount', 0),
                    "instance_type": node.get('instanceType', 'n/a')
                })
                
            # Processar dados de pods
            for pod in dados_brutos.get('pods', []):
                pods.append({
                    "name": pod.get('name'),
                    "namespace": pod.get('namespace'),
                    "cluster": pod.get('clusterName'),
                    "status": pod.get('status', 'unknown'),
                    "cpu_usage": pod.get('cpuUsagePercent', 0),
                    "memory_usage": pod.get('memoryUsagePercent', 0),
                    "restarts": pod.get('restarts', 0)
                })
                
            # Dados de resumo
            summary = {
                "total_clusters": len(clusters),
                "total_nodes": len(nodes),
                "total_pods": len(pods),
                "status": {
                    "healthy": len([c for c in clusters if c["status"] == "healthy"]),
                    "warning": len([c for c in clusters if c["status"] == "warning"]),
                    "critical": len([c for c in clusters if c["status"] == "critical"])
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "clusters": clusters,
                "nodes": nodes,
                "pods": pods,
                "summary": summary
            }
        except Exception as e:
            logger.error(f"Erro ao formatar dados de Kubernetes: {e}")
            traceback.print_exc()
            return None
            
    def _determinar_status(self, entity):
        """Determina o status com base nos dados da entidade"""
        # Lógica para determinar status baseado em métricas
        cpu_usage = entity.get('cpuUsagePercent', 0)
        memory_usage = entity.get('memoryUsagePercent', 0)
        errors = entity.get('errorCount', 0)
        
        if errors > 5 or cpu_usage > 90 or memory_usage > 90:
            return "critical"
        elif errors > 0 or cpu_usage > 75 or memory_usage > 80:
            return "warning"
        else:
            return "healthy"
            
    def _contar_problemas(self, entity):
        """Conta o número de problemas em uma entidade"""
        return entity.get('errorCount', 0) + entity.get('warningCount', 0)
            
    async def extrair_dados_infraestrutura(self):
        """Extrai dados reais de infraestrutura do New Relic"""
        if self.modo_simulado:
            logger.info("Modo simulado: não extraindo dados reais de infraestrutura")
            return None
            
        try:
            logger.info("Extraindo dados de infraestrutura do New Relic...")
            # Usar o coletor avançado para obter dados de infraestrutura
            dados_infra = await self.collector.collect_infrastructure_data()
            
            # Transformar para o formato usado pelo frontend
            dados_formatados = self.formatar_dados_infraestrutura(dados_infra)
            
            logger.info(f"Dados de infraestrutura extraídos com sucesso: {len(dados_formatados.get('hosts', []))} hosts")
            return dados_formatados
        except Exception as e:
            logger.error(f"Erro ao extrair dados de infraestrutura: {e}")
            traceback.print_exc()
            return None
            
    def formatar_dados_infraestrutura(self, dados_brutos):
        """Formata dados brutos de infraestrutura para o formato usado pelo frontend"""
        if not dados_brutos:
            return None
            
        # Implementação da transformação dos dados
        try:
            hosts = []
            services = []
            
            # Processar dados de hosts
            for host in dados_brutos.get('hosts', []):
                hosts.append({
                    "id": host.get('id'),
                    "name": host.get('name'),
                    "type": host.get('type', 'server'),
                    "status": self._determinar_status_host(host),
                    "cpu": {
                        "cores": host.get('cpuCores', 1),
                        "usage_percent": host.get('cpuPercent', 0)
                    },
                    "memory": {
                        "total_gb": host.get('memoryTotalGb', 1),
                        "used_gb": host.get('memoryUsedGb', 0),
                        "usage_percent": host.get('memoryPercent', 0)
                    },
                    "disk": {
                        "total_gb": host.get('diskTotalGb', 1),
                        "used_gb": host.get('diskUsedGb', 0),
                        "usage_percent": host.get('diskPercent', 0)
                    },
                    "services_count": host.get('servicesCount', 0),
                    "alerts": host.get('alertsCount', 0)
                })
                
            # Processar dados de serviços
            for service in dados_brutos.get('services', []):
                services.append({
                    "id": service.get('id'),
                    "name": service.get('name'),
                    "host": service.get('hostName'),
                    "type": service.get('type', 'application'),
                    "status": service.get('status', 'unknown'),
                    "cpu_usage": service.get('cpuPercent', 0),
                    "memory_usage": service.get('memoryPercent', 0),
                    "response_time": service.get('responseTimeMs', 0),
                    "throughput": service.get('throughput', 0),
                    "error_rate": service.get('errorRate', 0)
                })
                
            # Dados de resumo
            summary = {
                "total_hosts": len(hosts),
                "total_services": len(services),
                "status": {
                    "healthy": len([h for h in hosts if h["status"] == "healthy"]),
                    "warning": len([h for h in hosts if h["status"] == "warning"]),
                    "critical": len([h for h in hosts if h["status"] == "critical"])
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "hosts": hosts,
                "services": services,
                "summary": summary
            }
        except Exception as e:
            logger.error(f"Erro ao formatar dados de infraestrutura: {e}")
            traceback.print_exc()
            return None
            
    def _determinar_status_host(self, host):
        """Determina o status do host com base nas métricas"""
        cpu = host.get('cpuPercent', 0)
        memory = host.get('memoryPercent', 0)
        disk = host.get('diskPercent', 0)
        alerts = host.get('alertsCount', 0)
        
        if cpu > 90 or memory > 90 or disk > 90 or alerts > 2:
            return "critical"
        elif cpu > 75 or memory > 80 or disk > 85 or alerts > 0:
            return "warning"
        else:
            return "healthy"
            
    async def extrair_dados_topologia(self):
        """Extrai dados reais de topologia de serviços do New Relic"""
        if self.modo_simulado:
            logger.info("Modo simulado: não extraindo dados reais de topologia")
            return None
            
        try:
            logger.info("Extraindo dados de topologia de serviços do New Relic...")
            # Usar o coletor avançado para obter dados de topologia
            dados_topo = await self.collector.collect_service_topology()
            
            # Transformar para o formato usado pelo frontend
            dados_formatados = self.formatar_dados_topologia(dados_topo)
            
            logger.info(f"Dados de topologia extraídos com sucesso: {len(dados_formatados.get('nodes', []))} nós")
            return dados_formatados
        except Exception as e:
            logger.error(f"Erro ao extrair dados de topologia: {e}")
            traceback.print_exc()
            return None
            
    def formatar_dados_topologia(self, dados_brutos):
        """Formata dados brutos de topologia para o formato usado pelo frontend"""
        if not dados_brutos:
            return None
            
        # Implementação da transformação dos dados
        try:
            nodes = []
            edges = []
            
            # Processar nós
            for node in dados_brutos.get('nodes', []):
                nodes.append({
                    "id": node.get('id'),
                    "name": node.get('name'),
                    "type": node.get('type', 'service'),
                    "status": self._determinar_status_servico(node),
                    "throughput": node.get('throughput', 0),
                    "error_rate": node.get('errorRate', 0),
                    "response_time": node.get('responseTimeMs', 0),
                    "apdex": node.get('apdex', 0.0),
                    "technology": node.get('technology', 'unknown'),
                    "environment": node.get('environment', 'production')
                })
                
            # Processar edges (conexões)
            for edge in dados_brutos.get('edges', []):
                edges.append({
                    "source": edge.get('source'),
                    "target": edge.get('target'),
                    "calls_per_minute": edge.get('callsPerMinute', 0),
                    "error_rate": edge.get('errorRate', 0),
                    "latency_ms": edge.get('latencyMs', 0)
                })
                
            # Dados de resumo
            summary = {
                "total_services": len(nodes),
                "total_connections": len(edges),
                "status": {
                    "healthy": len([n for n in nodes if n["status"] == "healthy"]),
                    "warning": len([n for n in nodes if n["status"] == "warning"]),
                    "critical": len([n for n in nodes if n["status"] == "critical"])
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "nodes": nodes,
                "edges": edges,
                "summary": summary
            }
        except Exception as e:
            logger.error(f"Erro ao formatar dados de topologia: {e}")
            traceback.print_exc()
            return None
            
    def _determinar_status_servico(self, servico):
        """Determina o status do serviço com base nas métricas"""
        error_rate = servico.get('errorRate', 0)
        apdex = servico.get('apdex', 1.0)
        response_time = servico.get('responseTimeMs', 0)
        
        if error_rate > 5 or apdex < 0.7 or response_time > 1000:
            return "critical"
        elif error_rate > 1 or apdex < 0.85 or response_time > 500:
            return "warning"
        else:
            return "healthy"
            
    async def salvar_dados_cache(self, tipo, dados):
        """Salva os dados no arquivo de cache"""
        if not dados:
            logger.warning(f"Sem dados para salvar no cache: {tipo}")
            return False
            
        arquivo = self.cache_files.get(tipo)
        if not arquivo:
            logger.error(f"Tipo de cache desconhecido: {tipo}")
            return False
            
        try:
            # Salvar em todos os diretórios de cache possíveis
            for dir_path in self.cache_dirs:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                    
                caminho_completo = os.path.join(dir_path, arquivo)
                with open(caminho_completo, 'w', encoding='utf-8') as f:
                    json.dump(dados, f, ensure_ascii=False, indent=2)
                    
                logger.info(f"Dados salvos com sucesso em: {caminho_completo}")
                
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar dados no cache: {e}")
            traceback.print_exc()
            return False
            
    async def integrar_dados_reais(self):
        """Integra todos os tipos de dados reais do New Relic"""
        logger.info("Iniciando integração de dados reais do New Relic...")
        
        if self.modo_simulado:
            logger.warning("Modo simulado ativado. Nenhum dado real será coletado.")
            logger.info("Para usar dados reais, forneça as credenciais do New Relic.")
            return False
            
        # Coletar e salvar dados de Kubernetes
        dados_k8s = await self.extrair_dados_kubernetes()
        if dados_k8s:
            await self.salvar_dados_cache("kubernetes", dados_k8s)
            
        # Coletar e salvar dados de Infraestrutura
        dados_infra = await self.extrair_dados_infraestrutura()
        if dados_infra:
            await self.salvar_dados_cache("infrastructure", dados_infra)
            
        # Coletar e salvar dados de Topologia
        dados_topo = await self.extrair_dados_topologia()
        if dados_topo:
            await self.salvar_dados_cache("topology", dados_topo)
            
        logger.info("Integração de dados reais concluída com sucesso!")
        return True
            
    def gerar_relatorio_integracao(self):
        """Gera um relatório detalhado da integração de dados reais"""
        relatorio = {
            "timestamp": datetime.now().isoformat(),
            "modo": "simulado" if self.modo_simulado else "real",
            "status_cache": {}
        }
        
        # Verificar o status dos arquivos de cache
        for tipo, arquivo in self.cache_files.items():
            status_arquivo = {"existe": False, "tamanho": 0, "ultima_modificacao": None}
            
            for dir_path in self.cache_dirs:
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
                
            logger.info("Relatório de integração gerado com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de integração: {e}")
            
        return relatorio

async def main():
    """Função principal para execução do script"""
    parser = argparse.ArgumentParser(description="Integrador de dados reais do New Relic")
    parser.add_argument('--account-id', type=str, help="ID da conta do New Relic")
    parser.add_argument('--api-key', type=str, help="Chave de API do New Relic")
    parser.add_argument('--simulated', action='store_true', help="Usar modo simulado mesmo com credenciais")
    args = parser.parse_args()
    
    # Criar o integrador
    integrador = NewRelicIntegrador(
        account_id=args.account_id,
        api_key=args.api_key,
        modo_simulado=args.simulated
    )
    
    # Executar integração de dados
    await integrador.integrar_dados_reais()
    
    # Gerar relatório
    relatorio = integrador.gerar_relatorio_integracao()
    
    # Imprimir resumo
    print("\n====== RESUMO DA INTEGRAÇÃO DE DADOS ======")
    print(f"Modo: {'SIMULADO' if integrador.modo_simulado else 'REAL'}")
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("\nStatus dos arquivos de cache:")
    
    for tipo, status in relatorio["status_cache"].items():
        status_texto = "✅ PRESENTE" if status["existe"] else "❌ AUSENTE"
        print(f"  - {tipo.upper()}: {status_texto} ({status.get('tamanho', 0)} KB)")
        
    print("\nPara usar dados reais, certifique-se de definir as variáveis de ambiente:")
    print("  - NEW_RELIC_ACCOUNT_ID")
    print("  - NEW_RELIC_API_KEY")
    print("\nOu passe-as como parâmetros: --account-id YOUR_ID --api-key YOUR_KEY")
    
    if integrador.modo_simulado:
        print("\nATENÇÃO: Sistema usando dados SIMULADOS. Defina as credenciais para usar dados reais.")
    else:
        print("\nSucesso! Sistema configurado para usar dados REAIS do New Relic.")

if __name__ == "__main__":
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Executar o script principal de forma assíncrona
    asyncio.run(main())
