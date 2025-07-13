"""
Script para otimizar e controlar a coleta de dados do New Relic para evitar custos excessivos.
Este script é especialmente importante para o plano gratuito que tem limitações de 100 GB/mês.
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime, timedelta
import argparse

# Adicionar o diretório pai ao PATH para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger_config import setup_logger
from utils.newrelic_plan_checker import get_plan_settings, optimize_nrql_query, is_free_plan
from utils.newrelic_collector import NewRelicCollector

# Configurar logger
logger = setup_logger('otimizar_coleta')

# Diretório para armazenar informações de uso
USAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "usage_stats")
USAGE_FILE = os.path.join(USAGE_DIR, "newrelic_usage.json")

async def verificar_uso_atual():
    """Verifica o uso atual do New Relic"""
    try:
        # Carregar variáveis de ambiente
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('NEW_RELIC_API_KEY')
        account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
        
        if not api_key or not account_id:
            logger.error("Chaves de API New Relic não encontradas no arquivo .env")
            return {}
        
        # Inicializar coletor
        collector = NewRelicCollector(api_key, account_id)
        logger.info("Verificando uso atual do New Relic...")
        
        # Consulta para verificar uso de dados (pode variar dependendo da estrutura do New Relic)
        nrql_usage = "SELECT sum(bytesIngested)/1e9 as 'GB Ingeridos' FROM NrConsumption SINCE 30 days ago"
        
        # No modo gratuito, limitar para evitar custos extras
        if is_free_plan():
            nrql_usage = "SELECT sum(bytesIngested)/1e9 as 'GB Ingeridos' FROM NrConsumption SINCE 1 day ago"
        
        try:
            # Tentar obter informações de uso
            usage_data = await collector.execute_nrql(nrql_usage)
            if usage_data and "results" in usage_data and usage_data["results"]:
                gb_used = usage_data["results"][0].get("GB Ingeridos", 0)
                logger.info(f"Uso atual de dados: {gb_used:.2f} GB")
                
                # Em plano gratuito, extrapolar uso mensal
                if is_free_plan():
                    estimated_monthly = gb_used * 30
                    logger.info(f"Estimativa de uso mensal: {estimated_monthly:.2f} GB")
                    gb_used = estimated_monthly
                
                return {
                    "gb_used": gb_used,
                    "timestamp": datetime.now().isoformat(),
                    "is_estimated": is_free_plan()
                }
        except Exception as e:
            logger.error(f"Erro ao verificar uso do New Relic: {e}")
        
        # Se falhar a verificação online, tentar usar dados do cache
        return carregar_uso_cache()
        
    except Exception as e:
        logger.error(f"Erro ao verificar uso atual: {e}")
        return {}

def carregar_uso_cache():
    """Carrega dados de uso do cache"""
    try:
        if os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, 'r') as f:
                data = json.load(f)
                
                # Verificar se os dados são recentes (menos de 24h)
                last_update = datetime.fromisoformat(data.get('timestamp'))
                if datetime.now() - last_update < timedelta(hours=24):
                    logger.info(f"Usando dados de uso em cache: {data.get('gb_used', 'N/A')} GB")
                    return data
                else:
                    logger.warning("Dados de uso em cache estão desatualizados")
    except Exception as e:
        logger.warning(f"Erro ao carregar dados de uso do cache: {e}")
    
    return {}

def salvar_uso_cache(usage_data):
    """Salva dados de uso no cache"""
    try:
        os.makedirs(USAGE_DIR, exist_ok=True)
        with open(USAGE_FILE, 'w') as f:
            json.dump(usage_data, f)
        logger.info("Dados de uso salvos no cache")
    except Exception as e:
        logger.warning(f"Erro ao salvar dados de uso no cache: {e}")

async def aplicar_otimizacoes():
    """Aplica otimizações de acordo com o plano e uso atual"""
    plano = await get_plan_settings()
    uso = await verificar_uso_atual()
    gb_usado = uso.get('gb_used', 0)
    
    # Salvar dados de uso para referência futura
    if gb_usado > 0:
        salvar_uso_cache(uso)
    
    # Verificar se o uso está se aproximando do limite
    limite_gb = plano.get('max_data_ingest_gb', 100)
    
    if gb_usado > limite_gb * 0.8:
        logger.warning(f"⚠️ ALERTA: Uso de dados em {gb_usado:.2f} GB está próximo do limite de {limite_gb} GB!")
        nivel_otimizacao = "alto"
    elif gb_usado > limite_gb * 0.6:
        logger.warning(f"⚠️ Uso de dados em {gb_usado:.2f} GB está em 60% do limite de {limite_gb} GB")
        nivel_otimizacao = "medio"
    else:
        logger.info(f"✓ Uso de dados em {gb_usado:.2f} GB está abaixo de 60% do limite de {limite_gb} GB")
        nivel_otimizacao = "baixo" if is_free_plan() else "desativado"
    
    # Aplicar otimizações com base no nível
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "newrelic_optimization.json")
    
    if not os.path.exists(os.path.dirname(config_path)):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    otimizacoes = {
        "nivel_otimizacao": nivel_otimizacao,
        "limite_gb": limite_gb,
        "uso_atual_gb": gb_usado,
        "timestamp": datetime.now().isoformat(),
        "plano_tipo": "Free" if is_free_plan() else "Pago",
        "configuracoes": {
            "cache_ttl_hours": plano.get("cache_ttl_hours", 24),
            "reduce_logging": nivel_otimizacao in ["medio", "alto"],
            "limit_entities": 10 if nivel_otimizacao == "alto" else (50 if nivel_otimizacao == "medio" else 100),
            "data_retention_days": 1 if nivel_otimizacao == "alto" else (7 if nivel_otimizacao == "medio" else 30)
        }
    }
    
    # Salvar configurações de otimização
    try:
        with open(config_path, 'w') as f:
            json.dump(otimizacoes, f, indent=2)
        logger.info(f"Configurações de otimização salvas em {config_path}")
    except Exception as e:
        logger.error(f"Erro ao salvar configurações de otimização: {e}")
    
    # Exibir recomendações
    print("\n" + "=" * 80)
    print("OTIMIZAÇÃO DE USO NEW RELIC")
    print("=" * 80)
    print(f"Plano atual: {otimizacoes['plano_tipo']}")
    print(f"Limite de ingestão: {limite_gb} GB/mês")
    print(f"Uso atual: {gb_usado:.2f} GB ({gb_usado/limite_gb*100:.1f}% do limite)")
    print(f"Nível de otimização aplicado: {nivel_otimizacao.upper()}")
    print("\nConfigurações aplicadas:")
    print(f"- TTL do cache: {otimizacoes['configuracoes']['cache_ttl_hours']} horas")
    print(f"- Redução de logs: {'Ativado' if otimizacoes['configuracoes']['reduce_logging'] else 'Desativado'}")
    print(f"- Limite de entidades monitoradas: {otimizacoes['configuracoes']['limit_entities']}")
    print(f"- Retenção de dados: {otimizacoes['configuracoes']['data_retention_days']} dias")
    
    if nivel_otimizacao in ["medio", "alto"]:
        print("\nRecomendações para reduzir custos:")
        print("1. Considere desativar monitoramento de entidades não críticas")
        print("2. Reduza a frequência de coleta de dados")
        print("3. Filtre logs antes de enviá-los ao New Relic")
        print("4. Use armazenamento local para dados históricos extensos")
        print("5. Verifique se há processos gerando volume excessivo de telemetria")
    
    print("=" * 80)
    
    return otimizacoes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Otimizador de coleta New Relic")
    parser.add_argument("--force", action="store_true", help="Forçar aplicação de otimizações, ignorando cache")
    args = parser.parse_args()
    
    # Se forçado, limpar cache de uso
    if args.force and os.path.exists(USAGE_FILE):
        try:
            os.remove(USAGE_FILE)
            logger.info("Cache de uso removido para forçar nova verificação")
        except Exception as e:
            logger.error(f"Erro ao remover cache: {e}")
    
    # Executar otimizações
    asyncio.run(aplicar_otimizacoes())
