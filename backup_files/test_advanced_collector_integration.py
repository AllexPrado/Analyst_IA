"""
Teste de verificação da integração do coletor avançado do New Relic.
Este teste verifica:
1. Se o coletor avançado está funcionando corretamente
2. Se a integração com o sistema de cache está funcionando
3. Se todos os tipos de dados avançados estão sendo coletados

Execução: python test_advanced_collector_integration.py
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Configura logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adiciona diretório pai ao path para importar módulos
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

# Arquivos de cache para verificação
CACHE_DIR = script_dir / "historico"
CACHE_FILE = CACHE_DIR / "cache_completo.json"

# Indicadores de sucesso
RESULTADOS = {
    "coletor_avancado_disponivel": False,
    "coletor_avancado_executado": False,
    "integracao_cache_ok": False,
    "total_entidades": 0,
    "tipos_dados_avancados": set(),
    "dominios_coletados": set(),
    "timestamp": None
}

async def verificar_coletor_avancado():
    """Verifica se o coletor avançado está disponível e funcional"""
    logger.info("Verificando disponibilidade do coletor avançado...")
    
    try:
        from utils.newrelic_advanced_collector import collect_full_data
        RESULTADOS["coletor_avancado_disponivel"] = True
        logger.info("✅ Coletor avançado disponível")
        
        # Testa coleta mínima para verificar funcionalidade
        logger.info("Testando execução do coletor avançado (pode demorar alguns segundos)...")
        try:
            # Executa o coletor com timeout de 60 segundos
            # Esta função está no módulo utils.newrelic_advanced_collector
            from utils.newrelic_advanced_collector import test_collector
            resultado = await asyncio.wait_for(test_collector(), 60)
            
            if resultado:
                logger.info("✅ Teste do coletor avançado executado com sucesso")
                RESULTADOS["coletor_avancado_executado"] = True
            else:
                logger.error("❌ Teste do coletor avançado falhou")
        except asyncio.TimeoutError:
            logger.error("❌ Timeout ao testar coletor avançado")
        except Exception as e:
            logger.error(f"❌ Erro ao testar coletor avançado: {e}")
    except ImportError as e:
        logger.error(f"❌ Coletor avançado não disponível: {e}")
        return False
    
    return RESULTADOS["coletor_avancado_disponivel"] and RESULTADOS["coletor_avancado_executado"]

async def verificar_integracao_cache():
    """Verifica se a integração com o sistema de cache está funcionando"""
    logger.info("Verificando integração com o sistema de cache...")
    
    try:
        # Verifica se o arquivo de cache existe
        if not CACHE_FILE.exists():
            logger.warning(f"⚠️ Arquivo de cache não encontrado em: {CACHE_FILE}")
            return False
        
        # Carrega o cache
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
        
        # Verifica se o cache contém os dados esperados
        if not cache:
            logger.error("❌ Cache vazio")
            return False
        
        # Obtém timestamp
        timestamp = cache.get("timestamp")
        if timestamp:
            RESULTADOS["timestamp"] = timestamp
            dt = datetime.fromisoformat(timestamp)
            idade_horas = (datetime.now() - dt).total_seconds() / 3600
            logger.info(f"ℹ️ Cache atualizado há {idade_horas:.1f} horas")
        
        # Verifica entidades
        entidades = cache.get("entidades", [])
        RESULTADOS["total_entidades"] = len(entidades)
        logger.info(f"ℹ️ Total de entidades no cache: {len(entidades)}")
        
        # Verifica domínios
        dominios = {}
        for e in entidades:
            dominio = e.get("domain", "UNKNOWN")
            dominios[dominio] = dominios.get(dominio, 0) + 1
            RESULTADOS["dominios_coletados"].add(dominio)
        
        logger.info(f"ℹ️ Domínios coletados: {dominios}")
        
        # Verifica tipos de dados avançados
        if entidades:
            amostra_entidade = next((e for e in entidades if e.get("dados_avancados")), None)
            if amostra_entidade and "dados_avancados" in amostra_entidade:
                dados_avancados = amostra_entidade["dados_avancados"]
                for tipo, dados in dados_avancados.items():
                    if dados:
                        RESULTADOS["tipos_dados_avancados"].add(tipo)
                
                logger.info(f"ℹ️ Tipos de dados avançados encontrados: {RESULTADOS['tipos_dados_avancados']}")
                
                # Dados avançados esperados
                dados_esperados = {"logs", "traces", "erros", "queries", "relacionamentos"}
                dados_faltantes = dados_esperados - RESULTADOS["tipos_dados_avancados"]
                
                if dados_faltantes:
                    logger.warning(f"⚠️ Dados avançados faltantes: {dados_faltantes}")
                else:
                    logger.info("✅ Todos os tipos de dados avançados estão sendo coletados")
            else:
                logger.warning("⚠️ Nenhuma entidade com dados avançados encontrada")
        
        RESULTADOS["integracao_cache_ok"] = True
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao verificar integração do cache: {e}")
        return False

async def teste_completo():
    """Executa o teste completo de integração"""
    logger.info("=" * 50)
    logger.info("TESTE DE INTEGRAÇÃO DO COLETOR AVANÇADO")
    logger.info("=" * 50)
    
    # Etapa 1: Verificar coletor avançado
    coletor_ok = await verificar_coletor_avancado()
    
    # Etapa 2: Verificar integração com cache
    cache_ok = await verificar_integracao_cache()
    
    # Resumo dos resultados
    logger.info("\n" + "=" * 50)
    logger.info("RESUMO DOS RESULTADOS")
    logger.info("=" * 50)
    
    logger.info(f"✓ Coletor avançado disponível: {RESULTADOS['coletor_avancado_disponivel']}")
    logger.info(f"✓ Coletor avançado executado: {RESULTADOS['coletor_avancado_executado']}")
    logger.info(f"✓ Integração com cache: {RESULTADOS['integracao_cache_ok']}")
    logger.info(f"✓ Total de entidades: {RESULTADOS['total_entidades']}")
    logger.info(f"✓ Domínios coletados: {', '.join(sorted(RESULTADOS['dominios_coletados']))}")
    logger.info(f"✓ Tipos de dados avançados: {', '.join(sorted(RESULTADOS['tipos_dados_avancados']))}")
    
    # Verificação final
    todos_ok = coletor_ok and cache_ok and RESULTADOS['total_entidades'] > 0 and len(RESULTADOS['tipos_dados_avancados']) >= 3
    
    if todos_ok:
        logger.info("\n✅✅✅ TESTE COMPLETO: SUCESSO! O coletor avançado está integrado e funcionando.")
    else:
        logger.info("\n❌❌❌ TESTE COMPLETO: FALHA! Alguns componentes não estão funcionando corretamente.")
    
    return todos_ok

if __name__ == "__main__":
    resultado = asyncio.run(teste_completo())
    sys.exit(0 if resultado else 1)
