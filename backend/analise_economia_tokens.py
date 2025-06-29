"""
Script para análise de economia de tokens com a filtragem rigorosa de entidades.

Este script:
1. Carrega o cache atual
2. Processa entidades com o filtro antigo (relaxado) e o novo (rigoroso)
3. Calcula a economia estimada de tokens
4. Gera relatório de impacto
"""

import json
import logging
import sys
from pathlib import Path
import json

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona diretório pai ao path para importações
sys.path.append('.')
from utils.entity_processor import filter_entities_with_data, is_entity_valid, process_entity_details

def calculate_entity_token_size(entity):
    """Calcula o tamanho aproximado em tokens de uma entidade serializada."""
    if not entity:
        return 0
    
    # Serializa a entidade para JSON
    entity_json = json.dumps(entity)
    
    # Estimativa simples: 1 token ~= 4 caracteres
    return len(entity_json) // 4

def criar_entidade_teste(nome, guid, domain, tem_metricas=True, tem_dados_reais=True):
    """Cria uma entidade de teste com ou sem dados reais."""
    entidade = {
        "name": nome,
        "guid": guid,
        "domain": domain,
        "metricas": {}
    }
    
    if tem_metricas:
        # Adiciona métricas simuladas
        entidade["metricas"] = {
            "30min": {},
            "3h": {},
            "24h": {}
        }
        
        if tem_dados_reais:
            # Adiciona dados reais
            entidade["metricas"]["30min"] = {
                "apdex": 0.95,
                "response_time_max": 1.23,
                "error_rate": 0.01,
                "throughput": 150
            }
            entidade["metricas"]["3h"] = {
                "apdex": 0.92,
                "response_time_max": 1.45,
                "error_rate": 0.02,
                "throughput": 130
            }
        else:
            # Adiciona dados vazios ou nulos
            entidade["metricas"]["30min"] = {
                "apdex": None,
                "response_time_max": "",
                "error_rate": [],
                "throughput": None
            }
    
    return entidade

def criar_dataset_teste(n_entidades_com_dados=20, n_entidades_sem_dados=30):
    """Cria um conjunto de teste de entidades."""
    entidades = []
    
    # Entidades com dados reais
    for i in range(n_entidades_com_dados):
        entidades.append(criar_entidade_teste(
            nome=f"App{i+1} com dados", 
            guid=f"guid-{i+1}",
            domain="APM" if i % 3 == 0 else ("BROWSER" if i % 3 == 1 else "INFRA"),
            tem_metricas=True,
            tem_dados_reais=True
        ))
    
    # Entidades sem dados reais
    for i in range(n_entidades_sem_dados):
        entidades.append(criar_entidade_teste(
            nome=f"App{i+n_entidades_com_dados+1} sem dados", 
            guid=f"guid-{i+n_entidades_com_dados+1}",
            domain="APM" if i % 3 == 0 else ("BROWSER" if i % 3 == 1 else "INFRA"),
            tem_metricas=True,
            tem_dados_reais=False
        ))
    
    # Adiciona alguns casos especiais
    entidades.append(criar_entidade_teste("App sem métricas", "guid-especial-1", "APM", False, False))
    entidades.append(criar_entidade_teste("App com problema", "guid-especial-2", "BROWSER", True, True))
    entidades[-1]["problema"] = "NO_DATA"
    entidades.append(criar_entidade_teste("App sem nome", "", "INFRA", True, True))
    
    return entidades

def medir_impacto_filtragem():
    """Mede o impacto da filtragem rigorosa vs relaxada."""
    try:
        # Tenta carregar cache real
        cache_file = Path("historico/cache_completo.json")
        entidades_raw = []
        
        if cache_file.exists():
            # Carrega o cache
            logger.info("Carregando cache real para análise de economia de tokens...")
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                    
                entidades_raw = cache.get("entidades", [])
                if entidades_raw:
                    logger.info(f"Cache carregado com {len(entidades_raw)} entidades")
            except Exception as e:
                logger.error(f"Erro ao carregar cache: {e}")
                entidades_raw = []
        
        # Se não tiver entidades no cache real, cria dataset de teste
        if not entidades_raw:
            logger.info("Criando dataset de teste para simulação...")
            entidades_raw = criar_dataset_teste(20, 30)
            logger.info(f"Dataset de teste criado com {len(entidades_raw)} entidades")
            
        logger.info(f"Analisando {len(entidades_raw)} entidades do cache...")
        
        # Implementação anterior (relaxada)
        def is_entity_valid_relaxed(entity):
            """Versão relaxada da validação, que aceita entidades sem dados reais."""
            if not entity or not isinstance(entity, dict):
                return False
            
            if not entity.get('name'):
                return False
                
            # Relaxado: aceita entidades mesmo sem métricas
            if not entity.get('metricas'):
                return True
                
            # Relaxado: qualquer métrica é aceita mesmo que seja None ou vazia
            return True
        
        # Modificação da função de filtragem para usar a validação relaxada
        def filter_entities_relaxed(entities):
            valid_entities = []
            
            for entity in entities:
                processed = process_entity_details(entity)
                if processed and is_entity_valid_relaxed(processed):
                    valid_entities.append(processed)
            
            return valid_entities
        
        # Análise com filtro relaxado
        entidades_relaxadas = filter_entities_relaxed(entidades_raw)
        
        # Análise com filtro rigoroso
        entidades_rigorosas = filter_entities_with_data(entidades_raw)
        if entidades_rigorosas is None:
            entidades_rigorosas = []
        
        # Cálculo de estatísticas
        n_raw = len(entidades_raw)
        n_relaxado = len(entidades_relaxadas)
        n_rigoroso = len(entidades_rigorosas)
        
        # Calcula tamanho estimado em tokens
        tokens_relaxado = sum(calculate_entity_token_size(e) for e in entidades_relaxadas)
        tokens_rigoroso = sum(calculate_entity_token_size(e) for e in entidades_rigorosas)
        
        # Economia de tokens
        tokens_economia = tokens_relaxado - tokens_rigoroso
        percentual_economia = (tokens_economia / tokens_relaxado * 100) if tokens_relaxado > 0 else 0
        
        # Gera relatório
        logger.info("\n" + "="*50)
        logger.info("RELATÓRIO DE ECONOMIA DE TOKENS")
        logger.info("="*50)
        logger.info(f"Total de entidades no cache: {n_raw}")
        logger.info(f"Entidades após filtro relaxado: {n_relaxado} ({n_relaxado/n_raw*100:.1f}%)")
        logger.info(f"Entidades após filtro rigoroso: {n_rigoroso} ({n_rigoroso/n_raw*100:.1f}%)")
        logger.info("-"*50)
        logger.info(f"Tokens com filtro relaxado: {tokens_relaxado}")
        logger.info(f"Tokens com filtro rigoroso: {tokens_rigoroso}")
        logger.info(f"Economia de tokens: {tokens_economia} ({percentual_economia:.1f}%)")
        logger.info("="*50)
        
        # Análise por domínio
        logger.info("\nDistribuição por domínio após filtragem rigorosa:")
        dominios = {}
        for e in entidades_rigorosas:
            dominio = e.get('domain', 'UNKNOWN')
            dominios[dominio] = dominios.get(dominio, 0) + 1
        
        for dominio, contagem in sorted(dominios.items()):
            logger.info(f"- {dominio}: {contagem} entidades")
        
        # Relatório de qualidade das métricas
        metrics_stats = {
            'has_apdex': 0,
            'has_response_time': 0,
            'has_error_rate': 0,
            'has_throughput': 0
        }
        
        for e in entidades_rigorosas:
            if not e.get('metricas'):
                continue
                
            for period, period_data in e['metricas'].items():
                if not period_data or not isinstance(period_data, dict):
                    continue
                    
                if 'apdex' in period_data and period_data['apdex'] is not None:
                    metrics_stats['has_apdex'] += 1
                if 'response_time_max' in period_data and period_data['response_time_max'] is not None:
                    metrics_stats['has_response_time'] += 1
                if ('error_rate' in period_data and period_data['error_rate'] is not None) or \
                   ('recent_error' in period_data and period_data['recent_error'] is not None):
                    metrics_stats['has_error_rate'] += 1
                if 'throughput' in period_data and period_data['throughput'] is not None:
                    metrics_stats['has_throughput'] += 1
        
        logger.info("\nEstatísticas de métricas nas entidades filtradas:")
        logger.info(f"- Apdex: {metrics_stats['has_apdex']} ({metrics_stats['has_apdex']/max(1,n_rigoroso)*100:.1f}%)")
        logger.info(f"- Response Time: {metrics_stats['has_response_time']} ({metrics_stats['has_response_time']/max(1,n_rigoroso)*100:.1f}%)")
        logger.info(f"- Error Rate: {metrics_stats['has_error_rate']} ({metrics_stats['has_error_rate']/max(1,n_rigoroso)*100:.1f}%)")
        logger.info(f"- Throughput: {metrics_stats['has_throughput']} ({metrics_stats['has_throughput']/max(1,n_rigoroso)*100:.1f}%)")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao medir impacto da filtragem: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Iniciando análise de economia de tokens...")
    medir_impacto_filtragem()
    logger.info("Análise concluída!")
