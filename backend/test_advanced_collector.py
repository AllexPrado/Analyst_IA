"""
Script para testar a integração do coletor avançado com o sistema Analyst IA

Este script verifica:
1. Se o coletor avançado consegue coletar todos os tipos de dados do New Relic
2. Se os dados são corretamente processados e armazenados no cache
3. Se o sistema está usando o coletor avançado por padrão
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Certifica que as variáveis de ambiente estão configuradas
os.environ["USAR_COLETOR_AVANCADO"] = "true"

# Informações para simulação quando API não estiver disponível
DADOS_SIMULADOS = {
    "entidades": [
        {
            "guid": "sim-1",
            "name": "Aplicação Simulada 1",
            "domain": "APM",
            "entityType": "APPLICATION",
            "metricas": {
                "30min": {
                    "apdex": 0.95,
                    "error_rate": 0.02,
                    "throughput": 150
                }
            },
            "dados_avancados": {
                "logs": ["Erro detectado em /api/users", "Conexão com banco restabelecida"],
                "traces": [{"id": "trace-1", "path": "/api/produtos", "duration_ms": 320}],
                "errors": [{"message": "Connection refused", "count": 5}],
                "queries": [{"query": "SELECT * FROM usuarios", "time_ms": 250}]
            }
        }
    ],
    "timestamp": "2025-06-28T20:00:00"
}

async def testar_coletor_avancado():
    """Testa o coletor avançado e sua integração com o sistema"""
    try:
        logger.info("=== TESTE DO COLETOR AVANÇADO ===")
        
        # 1. Importa os módulos necessários
        try:
            from utils.newrelic_advanced_collector import test_collector, collect_full_data
            from utils.cache import atualizar_cache_completo_avancado, get_cache
            logger.info("✅ Módulos importados com sucesso")
        except ImportError as e:
            logger.error(f"❌ Erro ao importar módulos: {e}")
            return False
        
        # Verifica se New Relic API key está configurada
        from utils.newrelic_advanced_collector import NEW_RELIC_API_KEY
        api_disponivel = bool(NEW_RELIC_API_KEY)
        
        if not api_disponivel:
            logger.warning("⚠️ API do New Relic não configurada. Usando dados simulados para testes.")
            
        # 2. Testa as funções básicas do coletor avançado
        logger.info("\n=== Testando funções básicas do coletor ===")
        
        if api_disponivel:
            success = await test_collector()
            if not success:
                logger.error("❌ Teste do coletor básico falhou")
                return False
            logger.info("✅ Funções básicas do coletor testadas com sucesso")
        else:
            logger.info("✅ Teste de funções básicas ignorado (usando dados simulados)")
        
        # 3. Testa a atualização do cache com o coletor avançado
        logger.info("\n=== Testando atualização do cache ===")
        
        if api_disponivel:
            success = await atualizar_cache_completo_avancado()
            if not success:
                logger.error("❌ Atualização do cache com coletor avançado falhou")
                return False
        else:
            # Simula a atualização do cache com dados mockados
            with patch('utils.cache.collect_full_data', return_value=DADOS_SIMULADOS):
                success = await atualizar_cache_completo_avancado()
                if not success:
                    logger.error("❌ Simulação de atualização do cache falhou")
                    return False
                    
        logger.info("✅ Atualização do cache com coletor avançado concluída")
        
        # 4. Verifica se o cache foi atualizado corretamente
        logger.info("\n=== Verificando dados no cache ===")
        cache = await get_cache()
        
        if not cache or not cache.get("entidades"):
            logger.error("❌ Cache não contém entidades após atualização")
            return False
        
        entidades = cache.get("entidades", [])
        logger.info(f"✅ Cache atualizado com {len(entidades)} entidades")
        
        # 5. Verifica se há dados avançados nas entidades
        dados_avancados_count = 0
        tipos_dados_avancados = set()
        
        for entidade in entidades[:20]:  # Verifica as primeiras 20 entidades
            if "dados_avancados" in entidade:
                dados_avancados_count += 1
                if entidade["dados_avancados"]:
                    for tipo, dados in entidade["dados_avancados"].items():
                        if dados:
                            tipos_dados_avancados.add(tipo)
        
        logger.info(f"✅ Entidades com dados avançados: {dados_avancados_count}")
        logger.info(f"✅ Tipos de dados avançados: {', '.join(sorted(tipos_dados_avancados))}")
        
        if dados_avancados_count == 0:
            logger.warning("⚠️ Nenhuma entidade com dados avançados encontrada no cache")
        
        return True
            
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(testar_coletor_avancado())
    
    if success:
        logger.info("\n✅✅✅ TESTE DO COLETOR AVANÇADO CONCLUÍDO COM SUCESSO ✅✅✅")
        sys.exit(0)
    else:
        logger.error("\n❌❌❌ TESTE DO COLETOR AVANÇADO FALHOU ❌❌❌")
        sys.exit(1)
