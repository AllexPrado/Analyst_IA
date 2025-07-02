"""
Script para sincronizar completamente as entidades do New Relic com o cache local.
Este script detecta todas as entidades disponíveis no New Relic e atualiza o cache local.
"""

import os
import sys
import json
import logging
import asyncio
import traceback
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretórios ao path
current_dir = Path(__file__).parent
if current_dir.name != "backend":
    sys.path.append(str(current_dir))
    backend_dir = current_dir / "backend"
    if backend_dir.exists():
        sys.path.append(str(backend_dir))

try:
    # Importações do sistema de cache e New Relic
    from backend.utils.newrelic_collector import NewRelicCollector, DOMINIOS_NEWRELIC
    from backend.utils.cache import salvar_cache_no_disco
except ImportError:
    try:
        from utils.newrelic_collector import NewRelicCollector, DOMINIOS_NEWRELIC
        from utils.cache import salvar_cache_no_disco
    except ImportError as e:
        logger.error(f"Erro ao importar módulos necessários: {e}")
        sys.exit(1)

async def sincronizar_todas_entidades():
    """
    Busca todas as entidades disponíveis no New Relic e as salva no cache.
    """
    logger.info("Iniciando sincronização completa de entidades do New Relic")
    
    try:
        # Criar coletor do New Relic
        collector = NewRelicCollector(api_key=os.environ.get("NEW_RELIC_API_KEY"), account_id=os.environ.get("NEW_RELIC_ACCOUNT_ID"))
        
        # Cache atualizado
        cache_atualizado = {
            "apm": [],
            "browser": [],
            "infra": [],
            "db": [],
            "mobile": [],
            "iot": [],
            "serverless": [],
            "synth": [],
            "ext": [],
            "alertas": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Buscar entidades para cada domínio
        total_entidades = 0
        
        for dominio in DOMINIOS_NEWRELIC:
            logger.info(f"Buscando entidades do domínio: {dominio}")
            try:
                entidades = await collector.obter_entidades_por_dominio(dominio)
                dominio_lower = dominio.lower()
                
                if entidades:
                    # Adicionar entidades ao cache
                    cache_atualizado[dominio_lower] = entidades
                    logger.info(f"  ✅ {len(entidades)} entidades encontradas para {dominio}")
                    total_entidades += len(entidades)
                else:
                    logger.warning(f"  ⚠️ Nenhuma entidade encontrada para {dominio}")
                
            except Exception as e:
                logger.error(f"Erro ao buscar entidades para {dominio}: {e}")
                logger.error(traceback.format_exc())
        
        # Salvar cache atualizado
        cache_path = Path("backend") / "cache.json"
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_atualizado, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Cache atualizado com sucesso! Total de {total_entidades} entidades.")
        logger.info(f"Cache salvo em: {cache_path}")
        
        # Também salvar no diretório histórico para compatibilidade
        try:
            historico_dir = Path("backend") / "historico"
            historico_dir.mkdir(exist_ok=True)
            historico_path = historico_dir / "cache_completo.json"
            
            # Converter para o formato antigo
            dados_historico = {
                "entidades": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Consolidar todas as entidades em uma única lista
            for dominio, entidades in cache_atualizado.items():
                if dominio != "timestamp" and isinstance(entidades, list):
                    for entidade in entidades:
                        entidade_convertida = {
                            "name": entidade.get("name", "Unknown"),
                            "guid": entidade.get("guid", ""),
                            "dominio": dominio.upper(),
                            "metricas": entidade.get("metricas", {})
                        }
                        dados_historico["entidades"].append(entidade_convertida)
            
            with open(historico_path, "w", encoding="utf-8") as f:
                json.dump(dados_historico, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Cache histórico atualizado em: {historico_path}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar cache histórico: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro durante sincronização: {e}")
        logger.error(traceback.format_exc())
        return False

async def coletar_metricas_para_entidades():
    """
    Coleta métricas detalhadas para cada entidade no cache.
    """
    logger.info("Coletando métricas para entidades...")
    
    try:
        # Carregar cache atual
        cache_path = Path("backend") / "cache.json"
        
        if not cache_path.exists():
            logger.error(f"Arquivo de cache não encontrado: {cache_path}")
            return False
            
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
            
        # Criar coletor
        collector = NewRelicCollector(api_key=os.environ.get("NEW_RELIC_API_KEY"), account_id=os.environ.get("NEW_RELIC_ACCOUNT_ID"))
        
        # Processar cada domínio
        dominios_processados = 0
        entidades_processadas = 0
        
        for dominio, entidades in cache.items():
            if dominio == "timestamp" or not isinstance(entidades, list) or len(entidades) == 0:
                continue
                
            logger.info(f"Processando métricas para {len(entidades)} entidades do domínio {dominio}...")
            
            for i, entidade in enumerate(entidades):
                try:
                    # Verificar se já tem métricas detalhadas
                    if "metricas" not in entidade or not entidade["metricas"]:
                        logger.info(f"  Coletando métricas para {entidade.get('name', 'Unknown')} ({i+1}/{len(entidades)})")
                        
                        # Coletar métricas
                        metricas = await collector.coletar_metricas_entidade(entidade, dominio.upper())
                        entidade["metricas"] = metricas
                        entidades_processadas += 1
                    else:
                        logger.debug(f"  Entidade já possui métricas: {entidade.get('name', 'Unknown')}")
                        
                except Exception as e:
                    logger.error(f"Erro ao coletar métricas para entidade {entidade.get('name', 'Unknown')}: {e}")
                    
            dominios_processados += 1
            
        # Atualizar timestamp
        cache["timestamp"] = datetime.now().isoformat()
            
        # Salvar cache atualizado
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
            
        logger.info(f"✅ Métricas coletadas para {entidades_processadas} entidades em {dominios_processados} domínios")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao coletar métricas: {e}")
        logger.error(traceback.format_exc())
        return False

async def main():
    """Função principal"""
    logger.info("=== SINCRONIZADOR DE ENTIDADES NEW RELIC ===")
    
    # Sincronizar todas as entidades
    success = await sincronizar_todas_entidades()
    
    if success:
        # Coletar métricas detalhadas para cada entidade
        success = await coletar_metricas_para_entidades()
        
        if success:
            logger.info("✅ Sincronização completa realizada com sucesso!")
        else:
            logger.error("❌ Falha ao coletar métricas para entidades")
    else:
        logger.error("❌ Falha ao sincronizar entidades")

if __name__ == "__main__":
    asyncio.run(main())
