#!/usr/bin/env python3
"""
Script para forçar atualização do cache com debug detalhado
"""

import asyncio
import logging
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Configurar logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adiciona o diretório atual ao path
sys.path.append(str(Path(__file__).parent))

async def force_cache_update():
    """Força atualização do cache com debug detalhado"""
    try:
        logger.info("=== FORÇANDO ATUALIZAÇÃO DO CACHE ===")
        
        # Importa as funções necessárias
        from utils.cache import atualizar_cache_completo_avancado, _cache, salvar_cache_no_disco
        from utils.newrelic_collector import coletar_contexto_completo
        
        logger.info("✅ Módulos importados com sucesso")
        
        # Verifica se temos as credenciais
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('NEW_RELIC_API_KEY')
        account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
        
        logger.info(f"API Key presente: {'Sim' if api_key else 'Não'}")
        logger.info(f"Account ID: {account_id}")
        
        if not api_key or not account_id:
            logger.error("❌ Credenciais do New Relic não encontradas!")
            return False
        
        # Método 1: Tentar com coletor avançado
        logger.info("🔄 Tentando atualização com coletor avançado...")
        try:
            success = await atualizar_cache_completo_avancado()
            if success:
                logger.info("✅ Atualização com coletor avançado bem-sucedida!")
                return True
            else:
                logger.warning("⚠️ Atualização com coletor avançado falhou")
        except Exception as e:
            logger.warning(f"⚠️ Erro no coletor avançado: {e}")
        
        # Método 2: Tentar com coletor padrão
        logger.info("🔄 Tentando atualização com coletor padrão...")
        try:
            resultado = await coletar_contexto_completo()
            logger.info(f"Resultado da coleta: {type(resultado)}")
            
            if resultado and isinstance(resultado, dict):
                logger.info(f"Chaves do resultado: {list(resultado.keys())}")
                
                entidades = resultado.get("entidades", [])
                logger.info(f"Total de entidades coletadas: {len(entidades)}")
                
                if entidades:
                    # Processa e filtra entidades
                    from utils.entity_processor import filter_entities_with_data
                    entidades_filtradas = filter_entities_with_data(entidades)
                    logger.info(f"Entidades após filtro: {len(entidades_filtradas)}")
                    
                    # Atualiza cache manualmente
                    _cache["dados"] = {
                        "entidades": entidades_filtradas,
                        "timestamp": datetime.now().isoformat(),
                        "total_entidades": len(entidades_filtradas),
                        "contagem_por_dominio": {}
                    }
                    
                    # Contagem por domínio
                    dominios = {}
                    for e in entidades_filtradas:
                        domain = e.get("domain", "UNKNOWN")
                        dominios[domain] = dominios.get(domain, 0) + 1
                    
                    _cache["dados"]["contagem_por_dominio"] = dominios
                    
                    # Salva em disco
                    await salvar_cache_no_disco()
                    
                    logger.info("✅ Cache atualizado manualmente!")
                    logger.info(f"Distribuição por domínio: {dominios}")
                    return True
                else:
                    logger.error("❌ Nenhuma entidade foi coletada!")
                    return False
            else:
                logger.error("❌ Resultado da coleta inválido!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no coletor padrão: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def verify_cache():
    """Verifica o estado atual do cache"""
    try:
        logger.info("=== VERIFICANDO ESTADO DO CACHE ===")
        
        from utils.cache import get_cache_sync, diagnosticar_cache
        
        # Diagnóstico detalhado
        stats = diagnosticar_cache()
        logger.info("Estatísticas do cache:")
        logger.info(f"  Status: {stats.get('status', 'N/A')}")
        logger.info(f"  Total entidades: {stats.get('total_entidades', 0)}")
        logger.info(f"  Domínios: {stats.get('contagem_por_dominio', {})}")
        logger.info(f"  Última atualização: {stats.get('ultima_atualizacao', 'N/A')}")
        
        # Cache atual
        cache_atual = get_cache_sync()
        if cache_atual:
            entidades = cache_atual.get("entidades", [])
            logger.info(f"✅ Cache carregado com {len(entidades)} entidades")
            return len(entidades) > 0
        else:
            logger.warning("⚠️ Cache vazio ou não carregado")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar cache: {e}")
        return False

async def main():
    """Executa o processo completo"""
    logger.info("🚀 INICIANDO PROCESSO DE ATUALIZAÇÃO FORÇADA DO CACHE")
    
    # Verifica estado inicial
    initial_state = await verify_cache()
    logger.info(f"Estado inicial do cache: {'✅ OK' if initial_state else '❌ Vazio'}")
    
    # Força atualização
    success = await force_cache_update()
    
    # Verifica estado final
    if success:
        final_state = await verify_cache()
        logger.info(f"Estado final do cache: {'✅ OK' if final_state else '❌ Ainda vazio'}")
        
        if final_state:
            logger.info("🎉 CACHE ATUALIZADO COM SUCESSO!")
        else:
            logger.error("💥 CACHE AINDA ESTÁ VAZIO APÓS ATUALIZAÇÃO!")
    else:
        logger.error("💥 FALHA NA ATUALIZAÇÃO DO CACHE!")

if __name__ == "__main__":
    asyncio.run(main())
