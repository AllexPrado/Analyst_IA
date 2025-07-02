"""
Script para atualizar a API e garantir que o Frontend tenha acesso a todas as entidades do cache.
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretórios ao path
current_dir = Path(__file__).parent
if current_dir.name != "backend":
    sys.path.append(str(current_dir))
    backend_dir = current_dir / "backend"
    if backend_dir.exists():
        sys.path.append(str(backend_dir))

class FrontendCacheIntegrator:
    """Classe para integrar o cache com o Frontend"""
    
    def __init__(self):
        self.cache_path = Path("backend") / "cache.json"
        self.endpoints_dir = Path("backend") / "endpoints"
        
    async def atualizar_endpoints_cobertura(self):
        """
        Atualiza o endpoint de cobertura para usar dados reais do cache.
        """
        try:
            # Verificar se o arquivo de cache existe
            if not self.cache_path.exists():
                logger.error(f"Arquivo de cache não encontrado: {self.cache_path}")
                return False
            
            # Ler dados do cache
            with open(self.cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
            
            # Contar entidades por domínio
            contagem_dominios = {}
            total_entidades = 0
            
            for dominio, entidades in cache.items():
                if dominio != "timestamp" and isinstance(entidades, list):
                    contagem_dominios[dominio.upper()] = len(entidades)
                    total_entidades += len(entidades)
            
            logger.info(f"Total de {total_entidades} entidades encontradas no cache")
            
            # Verificar e criar pasta para dados de API
            dados_dir = Path("backend") / "dados"
            dados_dir.mkdir(exist_ok=True)
            
            # Criar arquivo de dados de cobertura
            dados_cobertura = {
                "timestamp": datetime.now().isoformat(),
                "total_entidades": total_entidades,
                "monitoradas": total_entidades,
                "porcentagem": 100.0,
                "por_dominio": {}
            }
            
            # Preencher dados por domínio
            for dominio, contagem in contagem_dominios.items():
                criticas = max(1, int(contagem * 0.2))  # Considerar 20% como críticas
                dados_cobertura["por_dominio"][dominio] = {
                    "total": contagem,
                    "monitoradas": contagem,
                    "criticas": criticas
                }
            
            # Salvar dados
            cobertura_path = dados_dir / "cobertura.json"
            with open(cobertura_path, "w", encoding="utf-8") as f:
                json.dump(dados_cobertura, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Dados de cobertura atualizados em: {cobertura_path}")
            
            # Exportar lista de entidades para o frontend
            self.exportar_entidades_para_frontend(cache)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar endpoints de cobertura: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def exportar_entidades_para_frontend(self, cache):
        """
        Exporta a lista de entidades em um formato adequado para o frontend.
        """
        try:
            # Criar estrutura para entidades
            entidades_frontend = []
            
            # Processar cada domínio
            for dominio, entidades in cache.items():
                if dominio != "timestamp" and isinstance(entidades, list):
                    for entidade in entidades:
                        entidade_frontend = {
                            "id": entidade.get("guid", ""),
                            "name": entidade.get("name", "Unknown"),
                            "domain": dominio.upper(),
                            "metrics": {}
                        }
                        
                        # Processar métricas importantes
                        metricas = entidade.get("metricas", {})
                        if metricas:
                            # Selecionar métricas relevantes baseado no domínio
                            if dominio == "apm":
                                if "apdex" in metricas:
                                    entidade_frontend["metrics"]["apdex"] = metricas["apdex"]
                                if "response_time" in metricas:
                                    entidade_frontend["metrics"]["responseTime"] = metricas["response_time"]
                                if "error_rate" in metricas:
                                    entidade_frontend["metrics"]["errorRate"] = metricas["error_rate"]
                                if "throughput" in metricas:
                                    entidade_frontend["metrics"]["throughput"] = metricas["throughput"]
                            
                            elif dominio == "browser":
                                if "page_load_time" in metricas:
                                    entidade_frontend["metrics"]["pageLoadTime"] = metricas["page_load_time"]
                                if "ajax_error_rate" in metricas:
                                    entidade_frontend["metrics"]["ajaxErrorRate"] = metricas["ajax_error_rate"]
                                if "js_errors" in metricas:
                                    entidade_frontend["metrics"]["jsErrors"] = metricas["js_errors"]
                            
                            elif dominio == "infra":
                                if "cpu_usage" in metricas:
                                    entidade_frontend["metrics"]["cpuUsage"] = metricas["cpu_usage"]
                                if "memory_usage" in metricas:
                                    entidade_frontend["metrics"]["memoryUsage"] = metricas["memory_usage"]
                                if "disk_usage" in metricas:
                                    entidade_frontend["metrics"]["diskUsage"] = metricas["disk_usage"]
                        
                        entidades_frontend.append(entidade_frontend)
            
            # Salvar dados para o frontend
            dados_dir = Path("backend") / "dados"
            dados_dir.mkdir(exist_ok=True)
            
            # Arquivo principal de entidades
            entidades_path = dados_dir / "entidades.json"
            with open(entidades_path, "w", encoding="utf-8") as f:
                json.dump(entidades_frontend, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Lista de {len(entidades_frontend)} entidades exportada para o frontend em: {entidades_path}")
            
            # Também salvar entidades por domínio
            for dominio in ["apm", "browser", "infra", "db", "mobile"]:
                entidades_dominio = [e for e in entidades_frontend if e["domain"].lower() == dominio]
                
                if entidades_dominio:
                    dominio_path = dados_dir / f"entidades_{dominio}.json"
                    with open(dominio_path, "w", encoding="utf-8") as f:
                        json.dump(entidades_dominio, f, indent=2, ensure_ascii=False)
                        
                    logger.info(f"Exportadas {len(entidades_dominio)} entidades do domínio {dominio}")
            
            # Criar arquivo de insights para o frontend
            self.gerar_insights_para_frontend(entidades_frontend)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar entidades para frontend: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def gerar_insights_para_frontend(self, entidades):
        """
        Gera insights baseados nas entidades para o frontend.
        """
        try:
            insights = []
            
            # Verificar entidades com erros
            entidades_com_erros = []
            for entidade in entidades:
                error_rate = entidade.get("metrics", {}).get("errorRate")
                if error_rate and float(error_rate) > 1.0:  # Taxa de erro acima de 1%
                    entidades_com_erros.append({
                        "name": entidade["name"],
                        "domain": entidade["domain"],
                        "errorRate": error_rate
                    })
            
            if entidades_com_erros:
                insights.append({
                    "id": "error_rates",
                    "title": "Taxas de erro elevadas",
                    "description": f"Detectamos {len(entidades_com_erros)} entidades com taxas de erro acima do normal.",
                    "severity": "warning",
                    "data": entidades_com_erros
                })
            
            # Verificar tempo de resposta
            entidades_lentas = []
            for entidade in entidades:
                response_time = entidade.get("metrics", {}).get("responseTime")
                if response_time and float(response_time) > 1000:  # Mais de 1 segundo
                    entidades_lentas.append({
                        "name": entidade["name"],
                        "domain": entidade["domain"],
                        "responseTime": response_time
                    })
            
            if entidades_lentas:
                insights.append({
                    "id": "slow_response",
                    "title": "Tempos de resposta elevados",
                    "description": f"Detectamos {len(entidades_lentas)} entidades com tempos de resposta acima do ideal.",
                    "severity": "info",
                    "data": entidades_lentas
                })
            
            # Salvar insights
            dados_dir = Path("backend") / "dados"
            dados_dir.mkdir(exist_ok=True)
            
            insights_path = dados_dir / "insights.json"
            with open(insights_path, "w", encoding="utf-8") as f:
                json.dump(insights, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Gerados {len(insights)} insights para o frontend")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao gerar insights para frontend: {e}")
            return False

async def main():
    """Função principal"""
    logger.info("=== ATUALIZANDO INTEGRAÇÃO DO CACHE COM O FRONTEND ===")
    
    integrator = FrontendCacheIntegrator()
    success = await integrator.atualizar_endpoints_cobertura()
    
    if success:
        logger.info("✅ Frontend atualizado com dados do cache com sucesso!")
    else:
        logger.error("❌ Falha ao atualizar o frontend com dados do cache")
        
if __name__ == "__main__":
    asyncio.run(main())
