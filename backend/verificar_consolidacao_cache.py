import os
import sys
import json
import logging
import asyncio
from datetime import datetime

# Configurando logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importando módulos necessários
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cache import get_cache
from utils.newrelic_collector import entidade_tem_dados

async def verificar_consolidacao_cache():
    """
    Script para verificar se as entidades estão corretamente consolidadas no cache.
    """
    resultado = {
        "timestamp": datetime.now().isoformat(),
        "status": "sucesso",
        "detalhes": {},
        "problemas": []
    }
    
    try:
        # Verificar cache atual
        logger.info("Verificando cache...")
        cache = await get_cache()
        
        # Verificar entidades consolidadas
        entidades_consolidadas = cache.get("entidades", [])
        resultado["detalhes"]["total_entidades_consolidadas"] = len(entidades_consolidadas)
        
        if not entidades_consolidadas:
            resultado["problemas"].append("Cache não possui entidades consolidadas")
            resultado["status"] = "erro"
            logger.warning("Cache não possui entidades consolidadas")
            return resultado
            
        logger.info(f"Cache contém {len(entidades_consolidadas)} entidades consolidadas")
        
        # Verificar domínios individuais
        dominios = ["apm", "browser", "infra", "db", "mobile", "iot", "serverless", "synth", "ext"]
        entidades_por_dominio = {}
        total_por_dominio = 0
        
        for dominio in dominios:
            entidades = cache.get(dominio, [])
            entidades_por_dominio[dominio] = len(entidades)
            total_por_dominio += len(entidades)
            
        resultado["detalhes"]["entidades_por_dominio"] = entidades_por_dominio
        resultado["detalhes"]["total_entidades_por_dominio"] = total_por_dominio
        
        # Verificar se há duplicatas entre domínios (que poderiam não ser consolidadas corretamente)
        guids = {}
        duplicatas = []
        
        for entidade in entidades_consolidadas:
            guid = entidade.get("guid")
            if not guid:
                resultado["problemas"].append("Entidade sem GUID na lista consolidada")
                continue
                
            if guid in guids:
                duplicatas.append({
                    "guid": guid,
                    "name": entidade.get("name", "Sem nome"),
                })
            else:
                guids[guid] = True
        
        resultado["detalhes"]["entidades_unicas"] = len(guids)
        resultado["detalhes"]["duplicatas"] = len(duplicatas)
        
        if duplicatas:
            resultado["problemas"].append(f"Encontradas {len(duplicatas)} entidades duplicadas na lista consolidada")
            resultado["status"] = "alerta"
            logger.warning(f"Encontradas {len(duplicatas)} duplicatas no cache consolidado")
            
        # Verificar métricas
        entidades_sem_metricas = []
        entidades_com_metricas = 0
        
        for entidade in entidades_consolidadas:
            metricas = entidade.get("metricas", {})
            if entidade_tem_dados(metricas):
                entidades_com_metricas += 1
            else:
                entidades_sem_metricas.append({
                    "guid": entidade.get("guid", "Sem GUID"),
                    "name": entidade.get("name", "Sem nome")
                })
        
        resultado["detalhes"]["entidades_com_metricas"] = entidades_com_metricas
        resultado["detalhes"]["entidades_sem_metricas"] = len(entidades_sem_metricas)
        
        if entidades_sem_metricas:
            resultado["problemas"].append(f"{len(entidades_sem_metricas)} entidades sem métricas")
            logger.warning(f"{len(entidades_sem_metricas)} entidades sem métricas no cache consolidado")
        
        # Verificar consistência
        if len(guids) != len(entidades_consolidadas):
            resultado["problemas"].append(f"Inconsistência: {len(entidades_consolidadas)} entidades vs {len(guids)} GUIDs únicos")
            resultado["status"] = "alerta"
        
    except Exception as e:
        logger.error(f"Erro na verificação do cache: {e}", exc_info=True)
        resultado["problemas"].append(f"Erro: {str(e)}")
        resultado["status"] = "erro"
    
    # Status final
    if resultado["problemas"]:
        if resultado["status"] != "erro":
            resultado["status"] = "alerta"
    
    # Salvar relatório
    os.makedirs("historico", exist_ok=True)
    caminho_arquivo = f"historico/verificacao_cache_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Relatório salvo em {caminho_arquivo}")
    return resultado

if __name__ == "__main__":
    print("Verificando consolidação de entidades no cache...")
    resultado = asyncio.run(verificar_consolidacao_cache())
    
    print("\n===== RESULTADOS DA VERIFICAÇÃO =====")
    print(f"Status: {resultado['status']}")
    
    if resultado['status'] == 'sucesso':
        print("✅ Cache está corretamente consolidado!")
    else:
        print("⚠️ Problemas encontrados:")
        for problema in resultado["problemas"]:
            print(f"  - {problema}")
    
    print("\nDetalhes:")
    print(f"  - Entidades consolidadas: {resultado['detalhes'].get('total_entidades_consolidadas', 0)}")
    print(f"  - Entidades com métricas: {resultado['detalhes'].get('entidades_com_metricas', 0)}")
    print(f"  - Entidades sem métricas: {resultado['detalhes'].get('entidades_sem_metricas', 0)}")
    
    print("\nVerificação concluída!")
