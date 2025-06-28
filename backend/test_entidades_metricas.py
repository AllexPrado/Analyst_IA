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
from utils.cache import get_cache, forcar_atualizacao_cache
from utils.newrelic_collector import coletar_contexto_completo, entidade_tem_dados

async def diagnostico_entidades_metricas():
    """
    Script de diagnóstico para verificar entidades, métricas e problemas de consolidação.
    """
    resultado = {
        "timestamp": datetime.now().isoformat(),
        "status": "iniciado",
        "detalhes": {},
        "problemas": []
    }
    
    # Passo 1: Verificar cache atual
    logger.info("Verificando cache atual...")
    cache = await get_cache()
    
    # Verificar se há entidades no cache
    entidades_cache = cache.get("entidades", [])
    resultado["detalhes"]["entidades_cache"] = len(entidades_cache)
    
    if not entidades_cache:
        resultado["problemas"].append("Cache não possui entidades consolidadas")
        logger.warning("Cache não possui entidades consolidadas")
    
    # Passo 2: Coletar entidades diretamente do New Relic
    logger.info("Coletando contexto completo do New Relic...")
    contexto = await coletar_contexto_completo()
    
    # Verificar entidades por domínio
    dominios = {
        "apm": len(contexto.get("apm", [])),
        "browser": len(contexto.get("browser", [])),
        "infra": len(contexto.get("infra", [])), 
        "db": len(contexto.get("db", [])),
        "mobile": len(contexto.get("mobile", [])),
        "iot": len(contexto.get("iot", [])),
        "serverless": len(contexto.get("serverless", [])),
        "synth": len(contexto.get("synth", [])),
        "ext": len(contexto.get("ext", []))
    }
    
    resultado["detalhes"]["entidades_por_dominio_newrelic"] = dominios
    resultado["detalhes"]["total_entidades_newrelic"] = sum(dominios.values())
    
    if sum(dominios.values()) == 0:
        resultado["problemas"].append("Nenhuma entidade coletada do New Relic")
        logger.error("Nenhuma entidade coletada do New Relic")
    
    # Passo 3: Verificar métricas para cada entidade
    logger.info("Verificando métricas para cada entidade...")
    entidades_com_metricas = 0
    entidades_sem_metricas = []
    
    for dominio, entidades in contexto.items():
        if not isinstance(entidades, list):
            continue
            
        for entidade in entidades:
            guid = entidade.get("guid")
            metricas = entidade.get("metricas", {})
            
            if not guid:
                resultado["problemas"].append(f"Entidade sem GUID no domínio {dominio}")
                continue
                
            if entidade_tem_dados(metricas):
                entidades_com_metricas += 1
            else:
                entidades_sem_metricas.append({
                    "guid": guid,
                    "name": entidade.get("name", "Sem nome"),
                    "dominio": dominio
                })
    
    resultado["detalhes"]["entidades_com_metricas"] = entidades_com_metricas
    resultado["detalhes"]["entidades_sem_metricas"] = len(entidades_sem_metricas)
    resultado["detalhes"]["detalhes_sem_metricas"] = entidades_sem_metricas[:10]  # Limitar para os primeiros 10
    
    if entidades_sem_metricas:
        resultado["problemas"].append(f"{len(entidades_sem_metricas)} entidades sem métricas válidas")
        
    # Passo 4: Teste de consolidação de entidades
    logger.info("Testando consolidação de entidades...")
    
    # Criar lista consolidada
    entidades_consolidadas = []
    for dominio, entidades in contexto.items():
        if not isinstance(entidades, list):
            continue
            
        for entidade in entidades:
            guid = entidade.get("guid")
            if guid and not any(e.get("guid") == guid for e in entidades_consolidadas):
                entidades_consolidadas.append(entidade)
    
    resultado["detalhes"]["total_entidades_consolidadas"] = len(entidades_consolidadas)
    
    if len(entidades_consolidadas) == 0:
        resultado["problemas"].append("Falha ao consolidar entidades")
    elif len(entidades_consolidadas) < sum(dominios.values()):
        resultado["problemas"].append(f"Possíveis duplicatas: {sum(dominios.values()) - len(entidades_consolidadas)}")
    
    # Finalizar status
    if resultado["problemas"]:
        resultado["status"] = "problemas_encontrados"
    else:
        resultado["status"] = "sucesso"
    
    # Salvar resultado no arquivo
    logger.info("Salvando resultado do diagnóstico...")
    os.makedirs("historico", exist_ok=True)
    caminho_arquivo = os.path.join("historico", f"diagnostico_entidades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Diagnóstico finalizado e salvo em {caminho_arquivo}")
    return resultado

if __name__ == "__main__":
    resultado = asyncio.run(diagnostico_entidades_metricas())
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
