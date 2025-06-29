"""
Integração do coletor avançado com filtragem rigorosa de entidades.

Este módulo:
1. Usa o coletor avançado para obter todos os dados do New Relic
2. Aplica filtragem rigorosa para garantir apenas dados reais
3. Economiza tokens ao descartar dados nulos, vazios ou sem valor
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
import traceback

# Configuração de logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importa os módulos necessários
try:
    from utils.newrelic_advanced_collector import collect_full_data
    from utils.entity_processor import filter_entities_with_data
except ImportError as e:
    logger.error(f"Erro ao importar módulos necessários: {e}")
    sys.exit(1)

# Diretório para armazenar o cache
CACHE_DIR = Path("historico")
CACHE_FILE = CACHE_DIR / "cache_otimizado.json"

async def coletar_e_otimizar_dados():
    """
    Coleta dados avançados do New Relic e aplica filtragem rigorosa.
    Economiza tokens ao manter apenas dados reais e úteis.
    """
    try:
        logger.info("Iniciando coleta avançada com filtragem rigorosa...")
        inicio = datetime.now()
        
        # 1. Coleta completa usando o coletor avançado
        resultado = await collect_full_data()
        
        if not resultado or "erro" in resultado:
            logger.error(f"Erro na coleta de dados: {resultado.get('erro', 'Desconhecido')}")
            return False
        
        # 2. Recupera as entidades
        entidades_raw = resultado.get("entidades", [])
        logger.info(f"Coletadas {len(entidades_raw)} entidades brutas")
        
        # 3. Aplica filtragem rigorosa
        logger.info("Aplicando filtragem rigorosa para economia de tokens...")
        entidades_filtradas = filter_entities_with_data(entidades_raw)
        if entidades_filtradas is None:
            entidades_filtradas = []
            
        logger.info(f"Após filtragem: {len(entidades_filtradas)} entidades úteis ({len(entidades_filtradas)/max(1, len(entidades_raw))*100:.1f}%)")
        
        # 4. Substitui as entidades filtradas no resultado
        resultado["entidades"] = entidades_filtradas
        resultado["timestamp_atualizacao"] = datetime.now().isoformat()
        resultado["metricas_processamento"] = {
            "entidades_originais": len(entidades_raw),
            "entidades_filtradas": len(entidades_filtradas),
            "taxa_aproveitamento": f"{len(entidades_filtradas)/max(1, len(entidades_raw))*100:.1f}%",
            "tempo_processamento": f"{(datetime.now() - inicio).total_seconds():.2f} segundos"
        }
        
        # 5. Verifica se o diretório existe
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # 6. Salva em disco
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Cache otimizado salvo em: {CACHE_FILE}")
        
        # 7. Análise final das entidades filtradas
        dominios = {}
        metrics_stats = {
            'has_apdex': 0,
            'has_response_time': 0,
            'has_error_rate': 0,
            'has_throughput': 0
        }
        
        for e in entidades_filtradas:
            # Contagem por domínio
            domain = e.get('domain', 'UNKNOWN')
            dominios[domain] = dominios.get(domain, 0) + 1
            
            # Estatísticas de métricas
            if e.get('metricas'):
                for period_data in e['metricas'].values():
                    if isinstance(period_data, dict):
                        if 'apdex' in period_data and period_data['apdex'] is not None:
                            metrics_stats['has_apdex'] += 1
                        if 'response_time_max' in period_data and period_data['response_time_max'] is not None:
                            metrics_stats['has_response_time'] += 1
                        if ('error_rate' in period_data and period_data['error_rate'] is not None) or \
                           ('recent_error' in period_data and period_data['recent_error'] is not None):
                            metrics_stats['has_error_rate'] += 1
                        if 'throughput' in period_data and period_data['throughput'] is not None:
                            metrics_stats['has_throughput'] += 1
        
        logger.info(f"Distribuição por domínio: {dominios}")
        logger.info(f"Estatísticas de métricas: Apdex: {metrics_stats['has_apdex']}, " +
                   f"Response Time: {metrics_stats['has_response_time']}, " +
                   f"Error Rate: {metrics_stats['has_error_rate']}, " +
                   f"Throughput: {metrics_stats['has_throughput']}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao coletar e otimizar dados: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Iniciando coleta otimizada de dados do New Relic...")
    
    try:
        resultado = asyncio.run(coletar_e_otimizar_dados())
        
        if resultado:
            logger.info("✅ Coleta e otimização concluídas com sucesso!")
            sys.exit(0)
        else:
            logger.error("❌ Coleta e otimização falharam!")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        traceback.print_exc()
        sys.exit(1)
