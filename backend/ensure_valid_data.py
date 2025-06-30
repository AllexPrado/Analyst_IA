#!/usr/bin/env python3
"""
Script principal para garantir o funcionamento do Analyst IA
com dados 100% reais do New Relic ou dados de teste quando necessário.

Este script:
1. Verifica se as credenciais do New Relic estão configuradas
2. Tenta coletar dados reais do New Relic
3. Se falhar, utiliza dados de teste realistas
4. Garante que o cache sempre tenha dados válidos para o frontend
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
import traceback

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes
CACHE_DIR = Path("historico")
CACHE_FILE = CACHE_DIR / "cache_completo.json"
ENV_FILE = Path(".env")
DADOS_DIR = Path("dados")
CHAT_HISTORY_FILE = DADOS_DIR / "chat_history.json"

async def test_newrelic_credentials():
    """Testa as credenciais do New Relic para ver se estão configuradas"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('NEW_RELIC_API_KEY')
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
    
    logger.info("=== VERIFICANDO CREDENCIAIS NEW RELIC ===")
    logger.info(f"API Key configurada: {'✅' if api_key else '❌'}")
    logger.info(f"Account ID configurado: {'✅' if account_id else '❌'}")
    
    if not api_key or not account_id:
        logger.warning("Credenciais do New Relic incompletas ou não configuradas")
        return False
    
    return True

async def collect_real_data():
    """Tenta coletar dados reais do New Relic"""
    logger.info("=== TENTANDO COLETAR DADOS REAIS DO NEW RELIC ===")
    
    try:
        # Tenta usar o coletor avançado primeiro
        success = False
        try:
            from utils.cache import atualizar_cache_completo_avancado
            logger.info("Usando coletor avançado para dados 100% reais...")
            success = await atualizar_cache_completo_avancado()
            if success:
                logger.info("✅ Coletor avançado obteve dados reais com sucesso!")
        except Exception as e:
            logger.warning(f"⚠️ Coletor avançado falhou: {e}")
        
        # Se o avançado falhar, tenta o coletor padrão
        if not success:
            logger.info("Tentando coletor padrão...")
            try:
                from utils.newrelic_collector import coletar_contexto_completo
                from utils.entity_processor import filter_entities_with_data
                from utils.cache import salvar_cache_no_disco, _cache
                
                # Coleta dados
                resultado = await coletar_contexto_completo()
                
                # Verifica se temos dados válidos
                if not resultado or not isinstance(resultado, dict) or "entidades" not in resultado:
                    logger.warning("⚠️ Coletor padrão não retornou dados válidos")
                    return False
                
                # Filtra entidades
                entidades = resultado.get("entidades", [])
                if not entidades:
                    logger.warning("⚠️ Nenhuma entidade encontrada pelo coletor padrão")
                    return False
                
                entidades_filtradas = filter_entities_with_data(entidades)
                logger.info(f"Entidades filtradas: {len(entidades_filtradas)} de {len(entidades)}")
                
                if not entidades_filtradas:
                    logger.warning("⚠️ Nenhuma entidade válida após filtragem")
                    return False
                
                # Atualiza o cache com dados reais
                resultado["entidades"] = entidades_filtradas
                resultado["timestamp"] = datetime.now().isoformat()
                resultado["tipo_coleta"] = "dados_reais"
                resultado["total_entidades"] = len(entidades_filtradas)
                
                # Contagem por domínio
                dominios = {}
                for e in entidades_filtradas:
                    domain = e.get("domain", "UNKNOWN")
                    dominios[domain] = dominios.get(domain, 0) + 1
                
                resultado["contagem_por_dominio"] = dominios
                
                # Atualiza o cache em memória
                _cache["dados"] = resultado
                
                # Salva em disco
                await salvar_cache_no_disco()
                
                logger.info("✅ Coletor padrão obteve dados reais com sucesso!")
                success = True
                
            except Exception as e:
                logger.warning(f"⚠️ Coletor padrão falhou: {e}")
                logger.debug(traceback.format_exc())
        
        return success
    except Exception as e:
        logger.error(f"❌ Erro crítico ao coletar dados reais: {e}")
        logger.debug(traceback.format_exc())
        return False

async def create_test_data():
    """Cria dados de teste realistas se não conseguiu obter dados reais"""
    logger.info("=== CRIANDO DADOS DE TESTE REALISTAS ===")
    
    try:
        # Verifica se o cache já existe e tem dados
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "entidades" in data and len(data["entidades"]) > 0:
                        logger.info("✅ Cache já contém dados, não é necessário criar dados de teste")
                        return True
            except Exception as e:
                logger.warning(f"⚠️ Erro ao ler cache existente: {e}")
        
        # Criar estrutura de diretórios
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Dados de teste realistas
        test_data = {
            "entidades": [
                {
                    "name": "API-Pagamentos",
                    "domain": "APM",
                    "guid": "test-guid-1",
                    "entityType": "APPLICATION",
                    "reporting": True,
                    "metricas": {
                        "30min": {
                            "apdex": 0.85,
                            "response_time": 245.5,
                            "response_time_max": 245.5,
                            "error_rate": 2.1,
                            "throughput": 1250.0,
                            "recent_error": "Connection timeout"
                        },
                        "3h": {
                            "apdex": 0.88,
                            "response_time": 220.3,
                            "response_time_max": 220.3,
                            "error_rate": 1.8,
                            "throughput": 1180.0
                        },
                        "24h": {
                            "apdex": 0.90,
                            "response_time": 180.2,
                            "response_time_max": 180.2,
                            "error_rate": 1.5,
                            "throughput": 1100.0
                        }
                    }
                },
                {
                    "name": "API-Autenticacao",
                    "domain": "APM",
                    "guid": "test-guid-2",
                    "entityType": "APPLICATION",
                    "reporting": True,
                    "metricas": {
                        "30min": {
                            "apdex": 0.92,
                            "response_time": 125.8,
                            "response_time_max": 125.8,
                            "error_rate": 0.8,
                            "throughput": 2500.0
                        },
                        "3h": {
                            "apdex": 0.91,
                            "response_time": 135.2,
                            "response_time_max": 135.2,
                            "error_rate": 1.0,
                            "throughput": 2300.0
                        },
                        "24h": {
                            "apdex": 0.89,
                            "response_time": 150.1,
                            "response_time_max": 150.1,
                            "error_rate": 1.2,
                            "throughput": 2200.0
                        }
                    }
                },
                {
                    "name": "Database-Principal",
                    "domain": "INFRA",
                    "guid": "test-guid-3",
                    "entityType": "DATABASE",
                    "reporting": True,
                    "metricas": {
                        "30min": {
                            "apdex": 0.78,
                            "response_time": 450.2,
                            "response_time_max": 450.2,
                            "error_rate": 0.5,
                            "throughput": 800.0
                        },
                        "3h": {
                            "apdex": 0.80,
                            "response_time": 420.1,
                            "response_time_max": 420.1,
                            "error_rate": 0.4,
                            "throughput": 750.0
                        },
                        "24h": {
                            "apdex": 0.82,
                            "response_time": 380.5,
                            "response_time_max": 380.5,
                            "error_rate": 0.3,
                            "throughput": 700.0
                        }
                    }
                },
                {
                    "name": "Frontend-User",
                    "domain": "BROWSER",
                    "guid": "test-guid-4",
                    "entityType": "BROWSER_APPLICATION",
                    "reporting": True,
                    "metricas": {
                        "30min": {
                            "apdex": 0.94,
                            "response_time": 1.2,
                            "response_time_max": 8.5,
                            "error_rate": 0.3,
                            "throughput": 3500.0
                        },
                        "3h": {
                            "apdex": 0.93,
                            "response_time": 1.3,
                            "response_time_max": 9.8,
                            "error_rate": 0.4,
                            "throughput": 3200.0
                        },
                        "24h": {
                            "apdex": 0.91,
                            "response_time": 1.5,
                            "response_time_max": 12.3,
                            "error_rate": 0.5,
                            "throughput": 3000.0
                        }
                    }
                },
                {
                    "name": "Redis-Cache",
                    "domain": "INFRA",
                    "guid": "test-guid-5",
                    "entityType": "CACHE",
                    "reporting": True,
                    "metricas": {
                        "30min": {
                            "apdex": 0.98,
                            "response_time": 0.8,
                            "response_time_max": 2.1,
                            "error_rate": 0.1,
                            "throughput": 9500.0,
                            "memory_usage": 65.4
                        },
                        "24h": {
                            "apdex": 0.97,
                            "response_time": 1.0,
                            "response_time_max": 4.5,
                            "error_rate": 0.2,
                            "throughput": 8900.0,
                            "memory_usage": 72.3
                        }
                    }
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "timestamp_atualizacao": datetime.now().isoformat(),
            "total_entidades": 5,
            "contagem_por_dominio": {
                "APM": 2,
                "INFRA": 2,
                "BROWSER": 1
            },
            "tipo_coleta": "dados_teste_desenvolvimento"
        }
        
        # Salvar no cache
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        # Também atualiza o cache em memória se possível
        try:
            from utils.cache import _cache
            _cache["dados"] = test_data
            logger.info("Cache em memória atualizado")
        except Exception:
            pass
        
        logger.info(f"✅ Dados de teste criados em: {CACHE_FILE}")
        logger.info(f"Total de entidades: {test_data['total_entidades']}")
        logger.info(f"Distribuição por domínio: {test_data['contagem_por_dominio']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar dados de teste: {e}")
        logger.debug(traceback.format_exc())
        return False

async def ensure_chat_history_exists():
    """Garante que o arquivo de histórico de chat exista"""
    try:
        DADOS_DIR.mkdir(parents=True, exist_ok=True)
        
        if not CHAT_HISTORY_FILE.exists():
            with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
            logger.info(f"✅ Arquivo de histórico de chat criado: {CHAT_HISTORY_FILE}")
        else:
            logger.info(f"Arquivo de histórico de chat existe: {CHAT_HISTORY_FILE}")
        
        return True
    except Exception as e:
        logger.warning(f"⚠️ Erro ao verificar histórico de chat: {e}")
        return False

async def main():
    """Função principal para garantir que o sistema tenha dados válidos"""
    logger.info("=" * 80)
    logger.info("INICIALIZANDO ANALYST IA COM VERIFICAÇÃO COMPLETA")
    logger.info("=" * 80)
    
    # 1. Garantir que diretórios básicos existam
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DADOS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. Verificar histórico de chat
    await ensure_chat_history_exists()
    
    # 3. Testar credenciais do New Relic
    has_credentials = await test_newrelic_credentials()
    
    # 4. Tentar coletar dados reais se tiver credenciais
    real_data_success = False
    if has_credentials:
        real_data_success = await collect_real_data()
        
        if real_data_success:
            logger.info("✅ Dados reais do New Relic coletados com sucesso!")
        else:
            logger.warning("⚠️ Não foi possível coletar dados reais do New Relic")
    
    # 5. Se não conseguiu dados reais, criar dados de teste
    if not real_data_success:
        test_data_success = await create_test_data()
        if test_data_success:
            logger.info("✅ Dados de teste criados com sucesso!")
        else:
            logger.error("❌ Não foi possível criar dados de teste")
            return False
    
    # 6. Verificar se o cache está preenchido corretamente
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            
        entidades = cache_data.get("entidades", [])
        logger.info(f"Cache verificado: {len(entidades)} entidades disponíveis")
        
        if len(entidades) == 0:
            logger.error("❌ Cache ainda está vazio após tentativas de preenchimento")
            return False
        
        # Contar por domínio para log
        dominios = {}
        for e in entidades:
            domain = e.get("domain", "UNKNOWN")
            dominios[domain] = dominios.get(domain, 0) + 1
        
        logger.info(f"Distribuição por domínio: {dominios}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar cache final: {e}")
        return False
    
    # 7. Final report
    logger.info("=" * 80)
    logger.info("SYSTEM READY!")
    logger.info("=" * 80)
    return True

if __name__ == "__main__":
    # Executar verificação e inicialização
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
