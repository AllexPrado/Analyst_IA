import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any

# Configurando logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importando módulos necessários
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cache import get_cache, forcar_atualizacao_cache, atualizar_cache_completo
from utils.newrelic_collector import coletar_contexto_completo, entidade_tem_dados

async def corrigir_e_consolidar_entidades():
    """
    Script para corrigir problemas de consolidação de entidades e métricas.
    Este script realiza:
    1. Coleta de dados direto do New Relic
    2. Validação de entidades e métricas
    3. Consolidação corrigida de entidades
    4. Atualização do cache com entidades corrigidas
    """
    resultado = {
        "timestamp": datetime.now().isoformat(),
        "status": "iniciado",
        "antes": {},
        "depois": {},
        "acoes_corretivas": []
    }
    
    # Passo 1: Verificar estado atual do cache
    logger.info("Verificando cache atual antes das correções...")
    cache_antes = await get_cache()
    
    # Verificar se há entidades no cache
    entidades_cache_antes = cache_antes.get("entidades", [])
    resultado["antes"]["entidades_cache"] = len(entidades_cache_antes)
    resultado["antes"]["dominios_disponiveis"] = list(filter(lambda k: isinstance(cache_antes.get(k), list), cache_antes.keys()))
    
    # Verificar entidades por domínio antes da correção
    dominios_antes = {}
    for dominio in ["apm", "browser", "infra", "db", "mobile", "iot", "serverless", "synth", "ext"]:
        if dominio in cache_antes and isinstance(cache_antes[dominio], list):
            dominios_antes[dominio] = len(cache_antes[dominio])
    
    resultado["antes"]["entidades_por_dominio"] = dominios_antes
    resultado["antes"]["total_entidades_dominios"] = sum(dominios_antes.values())
    
    # Passo 2: Forçar atualização completa do cache
    logger.info("Forçando atualização do cache com dados do New Relic...")
    sucesso = await forcar_atualizacao_cache(coletar_contexto_completo)
    
    if not sucesso:
        resultado["status"] = "erro"
        resultado["erro"] = "Falha ao atualizar cache"
        logger.error("Falha ao atualizar o cache do New Relic")
        return resultado
        
    resultado["acoes_corretivas"].append("Cache atualizado com sucesso")
    
    # Passo 3: Obter cache atualizado
    cache_atualizado = await get_cache()
    
    # Passo 4: Consolidar entidades corretamente
    logger.info("Consolidando entidades de todos os domínios...")
    entidades_consolidadas = []
    dominios_para_verificar = ['apm', 'browser', 'infra', 'db', 'mobile', 'iot', 'serverless', 'synth', 'ext']
    
    # Contagem por domínio após atualização
    dominios_depois = {}
    
    for dominio in dominios_para_verificar:
        if dominio in cache_atualizado and isinstance(cache_atualizado[dominio], list):
            entidades_dominio = cache_atualizado[dominio]
            dominios_depois[dominio] = len(entidades_dominio)
            
            # Log para cada domínio
            logger.info(f"Processando {len(entidades_dominio)} entidades do domínio {dominio}")
            
            for entidade in entidades_dominio:
                # Adicionar à lista consolidada apenas se tiver guid (evitar duplicatas)
                guid = entidade.get("guid")
                if guid and not any(e.get("guid") == guid for e in entidades_consolidadas):
                    # Verificar métricas
                    if not entidade_tem_dados(entidade.get("metricas", {})):
                        logger.warning(f"Entidade {guid} ({entidade.get('name', 'Sem nome')}) não tem métricas válidas")
                        resultado["acoes_corretivas"].append(f"Adicionando entidade {guid} mesmo sem métricas válidas")
                    
                    # Adicionar à consolidação
                    entidades_consolidadas.append(entidade)
    
    # Passo 5: Atualizar o cache com as entidades consolidadas
    logger.info(f"Atualizando cache com {len(entidades_consolidadas)} entidades consolidadas...")
    cache_atualizado["entidades"] = entidades_consolidadas
    cache_atualizado["timestamp_consolidacao"] = datetime.now().isoformat()
    
    # Salvar o cache atualizado
    await atualizar_cache_completo(cache_atualizado)
    resultado["acoes_corretivas"].append(f"Cache atualizado com {len(entidades_consolidadas)} entidades consolidadas")
    
    # Passo 6: Registrar resultado
    resultado["depois"]["entidades_cache"] = len(entidades_consolidadas)
    resultado["depois"]["entidades_por_dominio"] = dominios_depois
    resultado["depois"]["total_entidades_dominios"] = sum(dominios_depois.values())
    resultado["depois"]["total_consolidadas"] = len(entidades_consolidadas)
    
    # Finalizar status
    resultado["status"] = "concluido"
    
    # Salvar resultado no arquivo
    logger.info("Salvando resultado da correção...")
    os.makedirs("historico", exist_ok=True)
    caminho_arquivo = os.path.join("historico", f"correcao_entidades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Correção finalizada e salva em {caminho_arquivo}")
    return resultado

if __name__ == "__main__":
    resultado = asyncio.run(corrigir_e_consolidar_entidades())
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
