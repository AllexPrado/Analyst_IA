import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Configure logging to display detailed information
logging.basicConfig(level=logging.INFO, 
                   format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)

# Import cache and collector functionality
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.cache import forcar_atualizacao_cache, diagnosticar_cache
from utils.newrelic_collector import coletar_contexto_completo, buscar_todas_entidades

# Backup the original function
import utils.newrelic_collector as collector
original_entidade_tem_dados = collector.entidade_tem_dados

def entidade_tem_dados_fixed(metricas):
    """
    Version melhorada do verificador de entidade_tem_dados que é menos restritiva e 
    aceita entidades mesmo quando os valores das métricas são nulos.
    
    Retorna True se a estrutura de métricas estiver correta, mesmo que os valores sejam nulos.
    
    Args:
        metricas: Dicionário com métricas coletadas do New Relic
    """
    if not metricas or not isinstance(metricas, dict):
        return False
        
    # Verifica cada período (30min, 24h, 7d, 30d)
    for periodo, periodo_data in metricas.items():
        if not isinstance(periodo_data, dict):
            continue
            
        # Se temos pelo menos uma métrica com estrutura correta, consideramos válida
        if periodo_data:
            return True
                
    return False

async def test_fix():
    logger.info("Iniciando teste da correção para entidade_tem_dados")
    
    # Aplica o patch na função
    logger.info("Aplicando patch na função entidade_tem_dados")
    collector.entidade_tem_dados = entidade_tem_dados_fixed
    
    # Força atualização do cache com a nova função
    logger.info("Forçando atualização do cache com a nova função")
    update_result = await forcar_atualizacao_cache(coletar_contexto_completo)
    
    # Verifica o estado do cache após a atualização
    logger.info("Verificando estado final do cache")
    final_state = diagnosticar_cache()
    logger.info(f"Estado final do cache: {json.dumps(final_state, indent=2)}")
    
    # Restaura a função original
    logger.info("Restaurando função original para manter consistência")
    collector.entidade_tem_dados = original_entidade_tem_dados
    
    # Estatísticas e relatório
    result = {
        "update_successful": update_result,
        "final_state": final_state,
        "timestamp": datetime.now().isoformat()
    }
    
    # Salva resultado
    output_path = Path("fix_entidade_tem_dados_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    logger.info(f"Resultado do teste salvo em {output_path}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_fix())
