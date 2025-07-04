"""
Script para testar a filtragem rigorosa de entidades com o novo processador.
Verifica se estamos economizando tokens ao rejeitar dados nulos/vazios.
"""

import json
import logging
import sys
import traceback
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona diretório pai ao path para importações
sys.path.append('.')
from utils.entity_processor import filter_entities_with_data, is_entity_valid, process_entity_details

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

def main():
    """Função principal de teste."""
    try:
        logger.info("Iniciando teste de filtragem rigorosa de entidades")
        
        # Cria um conjunto de entidades de teste
        entidades_teste = [
            criar_entidade_teste("App1 - Com dados", "guid-1", "APM", True, True),
            criar_entidade_teste("App2 - Sem dados reais", "guid-2", "APM", True, False),
            criar_entidade_teste("App3 - Sem métricas", "guid-3", "APM", False, False),
            criar_entidade_teste("App4 - Com dados", "guid-4", "BROWSER", True, True),
            criar_entidade_teste("App5 - Sem nome", "", "APM", True, True),
            criar_entidade_teste("App6 - Com problema", "guid-6", "APM", True, True),
        ]
        
        # Adiciona problema explícito à entidade 6
        entidades_teste[5]["problema"] = "NO_DATA"
        
        logger.info(f"Criadas {len(entidades_teste)} entidades de teste")
        
        # Valida cada entidade individualmente
        logger.info("\nValidação individual de entidades:")
        for entidade in entidades_teste:
            try:
                processada = process_entity_details(entidade)
                valida = is_entity_valid(processada) if processada else False
                logger.info(f"Entidade: {entidade.get('name')} - Valid: {valida}")
            except Exception as e:
                logger.error(f"Erro ao processar entidade {entidade.get('name', 'unknown')}: {str(e)}")
        
        # Testa o filtro completo
        logger.info("\nTestando filtro completo:")
        try:
            entidades_filtradas = filter_entities_with_data(entidades_teste)
            if entidades_filtradas is None:
                entidades_filtradas = []
            logger.info(f"Entidades após filtro: {len(entidades_filtradas)} de {len(entidades_teste)}")
        except Exception as e:
            logger.error(f"Erro ao filtrar entidades: {str(e)}")
            logger.error(traceback.format_exc())
            entidades_filtradas = []
    except Exception as e:
        logger.error(f"Erro geral no teste: {str(e)}")
        logger.error(traceback.format_exc())
    
    # Mostra quais entidades passaram no filtro
    if entidades_filtradas:
        logger.info("Entidades que passaram no filtro:")
        for entidade in entidades_filtradas:
            logger.info(f" - {entidade.get('name')}")
            
            # Exibe as métricas da entidade
            if '30min' in entidade.get('metricas', {}):
                logger.info(f"   Métricas 30min: {entidade['metricas']['30min']}")
    else:
        logger.warning("Nenhuma entidade passou no filtro!")
    
    # Tenta carregar o cache real do sistema
    try:
        logger.info("\nTestando com cache real do sistema:")
        cache_file = Path("historico/cache_completo.json")
        
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
                
            entidades_reais = cache.get("entidades", [])
            if entidades_reais is None:
                entidades_reais = []
                
            logger.info(f"Entidades no cache real: {len(entidades_reais)}")
            
            if entidades_reais:
                # Testa o filtro com entidades reais
                entidades_filtradas_reais = filter_entities_with_data(entidades_reais)
                if entidades_filtradas_reais is None:
                    entidades_filtradas_reais = []
                    
                logger.info(f"Entidades reais após filtro: {len(entidades_filtradas_reais)} de {len(entidades_reais)}")
                
                # Taxa de aprovação
                aprovacao = len(entidades_filtradas_reais) / len(entidades_reais) if entidades_reais else 0
                logger.info(f"Taxa de aprovação: {aprovacao:.1%}")
                
                # Verificar por domínio
                dominios = {}
                for e in entidades_filtradas_reais:
                    dominio = e.get('domain', 'UNKNOWN')
                    dominios[dominio] = dominios.get(dominio, 0) + 1
                
                logger.info(f"Distribuição por domínio após filtro: {dominios}")
        else:
            logger.warning(f"Arquivo de cache não encontrado: {cache_file}")
    except Exception as e:
        logger.error(f"Erro ao testar com cache real: {e}", exc_info=True)
    
    logger.info("\nTeste de filtragem concluído!")

if __name__ == "__main__":
    main()
