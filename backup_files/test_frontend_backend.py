"""
Script para validar a comunicação entre frontend e backend e depurar problemas.
Executa testes e verificações no backend e exibe dados das entidades.
"""

import requests
import json
import sys
import os
from pathlib import Path
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Endpoints a testar
BACKEND_BASE_URL = "http://localhost:8000"
ENDPOINTS = [
    "/api/health",
    "/api/status",
    "/api/entidades",
    "/api/kpis",
]

def test_backend_endpoints():
    """Testa os principais endpoints do backend"""
    logger.info("Verificando endpoints do backend...")
    
    for endpoint in ENDPOINTS:
        url = f"{BACKEND_BASE_URL}{endpoint}"
        try:
            logger.info(f"Testando {url}...")
            response = requests.get(url)
            response.raise_for_status()
            
            logger.info(f"✅ {endpoint}: {response.status_code} OK")
            
            # Análise adicional para entidades
            if endpoint == "/api/entidades":
                analyze_entities_response(response.json())
                
        except requests.RequestException as e:
            logger.error(f"❌ {endpoint}: {str(e)}")
            
def analyze_entities_response(entities):
    """Analisa a resposta de entidades para detectar problemas"""
    if not entities:
        logger.warning("⚠️ Nenhuma entidade retornada!")
        return
    
    logger.info(f"📊 Total de entidades: {len(entities)}")
    
    # Contagem por domínio
    domains = {}
    for entity in entities:
        domain = entity.get('domain', 'unknown')
        domains[domain] = domains.get(domain, 0) + 1
    
    logger.info(f"🔍 Distribuição por domínio: {domains}")
    
    # Verificar dados nas entidades
    entities_with_metrics = 0
    entities_with_partial_data = 0
    
    for entity in entities:
        metrics = entity.get('metricas', {})
        has_partial = entity.get('dados_parciais', False)
        
        if metrics:
            entities_with_metrics += 1
        
        if has_partial:
            entities_with_partial_data += 1
            
    logger.info(f"📈 Entidades com métricas: {entities_with_metrics}/{len(entities)}")
    logger.info(f"⚠️ Entidades com dados parciais: {entities_with_partial_data}")
    
    # Se tivermos entidades, analisar a primeira para demonstração
    if entities:
        sample_entity = entities[0]
        logger.info("\n--- EXEMPLO DE ENTIDADE ---")
        logger.info(f"Nome: {sample_entity.get('name')}")
        logger.info(f"Domínio: {sample_entity.get('domain')}")
        logger.info(f"Tipo: {sample_entity.get('type')}")
        
        # Verificar a estrutura de métricas
        if 'metricas' in sample_entity:
            logger.info("Períodos disponíveis:")
            for period, metrics in sample_entity['metricas'].items():
                logger.info(f"  - {period}: {len(metrics)} métricas")
                # Mostrar algumas métricas de exemplo
                for i, (metric_name, metric_data) in enumerate(metrics.items()):
                    if i >= 3:  # Limite para não sobrecarregar o log
                        break
                    logger.info(f"    - {metric_name}: {'Tem dados' if metric_data else 'Sem dados'}")

def test_cache_file():
    """Verifica o arquivo de cache para dados"""
    cache_path = Path("historico/cache_completo.json")
    if not cache_path.exists():
        logger.error(f"❌ Arquivo de cache não encontrado: {cache_path}")
        return
    
    logger.info(f"📂 Verificando arquivo de cache: {cache_path}")
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            
        if not cache_data:
            logger.error("❌ Cache vazio!")
            return
        
        logger.info(f"✅ Cache carregado corretamente")
        
        # Analisar entidades do cache
        entities = cache_data.get('entidades', [])
        logger.info(f"📊 Entidades no cache: {len(entities)}")
        
        # Verificar dados básicos
        if entities:
            sample_entity = entities[0]
            logger.info("\n--- EXEMPLO DE ENTIDADE DO CACHE ---")
            logger.info(f"Nome: {sample_entity.get('name')}")
            logger.info(f"Domínio: {sample_entity.get('domain')}")
            logger.info(f"Tipo: {sample_entity.get('type')}")
            
            # Verificar se tem métricas
            if 'metricas' in sample_entity:
                logger.info("Métricas disponíveis no cache:")
                for period, metrics in sample_entity.get('metricas', {}).items():
                    logger.info(f"  - {period}: {len(metrics) if metrics else 0} métricas")
            
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"❌ Erro ao ler cache: {str(e)}")

if __name__ == "__main__":
    logger.info("=== TESTE DE INTEGRAÇÃO FRONTEND-BACKEND ===")
    
    # Testar endpoints do backend
    test_backend_endpoints()
    
    # Verificar arquivo de cache
    test_cache_file()
    
    logger.info("=== FIM DOS TESTES ===")
