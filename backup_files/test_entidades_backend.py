import os
import sys
import json
import logging
import asyncio
from dotenv import load_dotenv
from utils.newrelic_collector import coletar_contexto_completo
from utils.cache import get_cache, forcar_atualizacao_cache

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

async def testar_entidades_consolidadas():
    """
    Testa a funcionalidade de consolidação de entidades no backend principal.
    Verifica se as entidades estão sendo carregadas corretamente do New Relic
    e se o cache está sendo atualizado adequadamente.
    """
    logger.info("Iniciando teste de entidades consolidadas...")
    
    # Forçar atualização do cache
    logger.info("Forçando atualização do cache...")
    sucesso = await forcar_atualizacao_cache(coletar_contexto_completo)
    
    if not sucesso:
        logger.error("Falha ao atualizar o cache!")
        return False
    
    # Obter cache atualizado
    cache = await get_cache()
    
    # Verificar se o cache contém as entidades esperadas
    dominios_para_verificar = ['apm', 'browser', 'infra', 'db', 'mobile', 'iot', 'serverless', 'synth', 'ext']
    
    # Contador de entidades por domínio
    contagem_por_dominio = {}
    entidades_com_metricas = 0
    total_entidades = 0
    
    # Verificar cada domínio
    for dominio in dominios_para_verificar:
        entidades_dominio = cache.get(dominio, [])
        contagem_por_dominio[dominio] = len(entidades_dominio)
        total_entidades += len(entidades_dominio)
        
        # Verificar entidades com métricas
        for entidade in entidades_dominio:
            if entidade.get("metricas") and any(entidade["metricas"].values()):
                entidades_com_metricas += 1
    
    # Verificar se há entidades consolidadas
    entidades_consolidadas = cache.get("entidades", [])
    
    # Resultados do teste
    resultado = {
        "status": "success" if total_entidades > 0 else "error",
        "total_entidades": total_entidades,
        "entidades_com_metricas": entidades_com_metricas,
        "contagem_por_dominio": contagem_por_dominio,
        "entidades_consolidadas": len(entidades_consolidadas)
    }
    
    # Log dos resultados
    logger.info(f"Teste concluído: {json.dumps(resultado, indent=2)}")
    
    # Salvar resultado detalhado em arquivo
    with open("historico/teste_backend_entidades.json", "w") as f:
        json.dump({
            "resultado": resultado,
            "primeiras_entidades": entidades_consolidadas[:5] if entidades_consolidadas else []
        }, f, indent=2)
    
    logger.info(f"Resultado detalhado salvo em historico/teste_backend_entidades.json")
    
    return resultado

if __name__ == "__main__":
    # Executar o teste
    asyncio.run(testar_entidades_consolidadas())
