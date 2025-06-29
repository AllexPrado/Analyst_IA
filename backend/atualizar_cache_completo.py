"""
Script para atualizar o cache com dados completos do New Relic

Este script utiliza o novo coletor avançado para obter todos os tipos de dados disponíveis:
- Métricas básicas (Apdex, Response Time, Error Rate, Throughput)
- Logs detalhados
- Traces e distribuições
- Backtraces de erros
- Queries SQL e performance
- Informações de execução de código (módulo, linha, tempo)
- Relacionamentos entre entidades
- Dados de infraestrutura e hosts

Isso garante que a IA tenha acesso a 100% dos dados do New Relic.
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Configura logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona diretório pai ao path para poder importar módulos corretamente
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

# Importa os módulos necessários
try:
    from utils.newrelic_advanced_collector import collect_full_data
    from utils.entity_processor import filter_entities_with_data
except ImportError as e:
    logger.error(f"Erro ao importar módulos necessários: {e}")
    sys.exit(1)

# Diretório para armazenar o cache
CACHE_DIR = script_dir / "historico"
CACHE_FILE = CACHE_DIR / "cache_completo.json"

async def atualizar_cache_completo():
    """
    Executa a coleta completa de dados do New Relic e salva em disco.
    - Usa o coletor avançado para todos os tipos de dados
    - Filtra e processa as entidades para garantir qualidade
    - Salva o cache atualizado em disco
    """
    try:
        logger.info("Iniciando atualização completa do cache com todos os tipos de dados do New Relic...")
        
        # 1. Coleta completa usando o coletor avançado
        resultado = await collect_full_data()
        
        if not resultado or "erro" in resultado:
            logger.error(f"Erro na coleta de dados: {resultado.get('erro', 'Desconhecido')}")
            return False
        
        # 2. Recupera e filtra as entidades
        entidades_raw = resultado.get("entidades", [])
        
        logger.info(f"Coletadas {len(entidades_raw)} entidades brutas. Filtrando...")
        
        # Filtra entidades com dados reais
        entidades_filtradas = filter_entities_with_data(entidades_raw)
        
        logger.info(f"Filtradas {len(entidades_filtradas)} entidades válidas de {len(entidades_raw)} totais")
        
        # 3. Substitui as entidades filtradas no resultado
        resultado["entidades"] = entidades_filtradas
        resultado["timestamp_atualizacao"] = datetime.now().isoformat()
        
        # 4. Verifica se o diretório existe
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # 5. Salva em disco
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Cache completo atualizado e salvo em: {CACHE_FILE}")
        logger.info(f"Entidades por domínio: {resultado['contagem_por_dominio']}")
        
        # 6. Análise final dos dados coletados
        if entidades_filtradas:
            entidade_exemplo = entidades_filtradas[0]
            tipo_dados = set()
            
            if "dados_avancados" in entidade_exemplo:
                dados_avancados = entidade_exemplo["dados_avancados"]
                # Contabiliza que tipos de dados avançados foram coletados
                for tipo, dados in dados_avancados.items():
                    if dados:
                        tipo_dados.add(tipo)
            
            logger.info(f"Tipos de dados avançados coletados: {', '.join(sorted(tipo_dados))}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar cache completo: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Iniciando script de atualização completa do cache...")
    
    # Executa a atualização do cache
    try:
        result = asyncio.run(atualizar_cache_completo())
        
        if result:
            logger.info("✅ Script de atualização finalizado com sucesso!")
            sys.exit(0)
        else:
            logger.error("❌ Script de atualização falhou!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro crítico ao executar script: {e}", exc_info=True)
        sys.exit(1)
