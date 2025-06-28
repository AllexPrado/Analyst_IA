import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Configurando logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importando módulos necessários
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cache import get_cache, _cache, salvar_cache_no_disco, forcar_atualizacao_cache
from utils.newrelic_collector import coletar_contexto_completo, entidade_tem_dados

async def corrigir_cache_e_consolidar_entidades():
    """
    Script para corrigir o problema de cache e consolidar entidades corretamente.
    
    Este script:
    1. Força uma atualização do cache para obter entidades atuais do New Relic
    2. Extrai entidades de todos os domínios 
    3. Consolida as entidades em uma única lista removendo duplicatas
    4. Atualiza o cache com a lista consolidada
    5. Salva o cache atualizado em disco
    """
    resultado = {
        "timestamp": datetime.now().isoformat(),
        "status": "iniciado",
        "detalhes": {},
        "acoes": []
    }
    
    try:
        logger.info("Etapa 1: Forçando atualização do cache a partir do New Relic...")
        sucesso = await forcar_atualizacao_cache(coletar_contexto_completo)
        if not sucesso:
            raise Exception("Falha ao atualizar o cache a partir do New Relic")
        
        resultado["acoes"].append("Cache atualizado com sucesso do New Relic")
        
        # Obter o cache atualizado
        logger.info("Etapa 2: Obtendo cache atualizado...")
        cache = await get_cache()
        
        # Obter todas as entidades por domínio
        dominios = ["apm", "browser", "infra", "db", "mobile", "iot", "serverless", "synth", "ext"]
        entidades_por_dominio = {}
        
        for dominio in dominios:
            if dominio in cache:
                entidades = cache.get(dominio, [])
                entidades_por_dominio[dominio] = entidades
                logger.info(f"Encontradas {len(entidades)} entidades no domínio {dominio}")
        
        # Consolidar entidades eliminando duplicatas por guid
        logger.info("Etapa 3: Consolidando entidades de todos os domínios...")
        entidades_consolidadas = []
        guids_processados = set()
        
        for dominio, entidades in entidades_por_dominio.items():
            for entidade in entidades:
                guid = entidade.get("guid")
                if not guid:
                    logger.warning(f"Entidade encontrada sem GUID no domínio {dominio}: {entidade.get('name', 'Sem nome')}")
                    continue
                    
                if guid not in guids_processados:
                    guids_processados.add(guid)
                    entidades_consolidadas.append(entidade)
        
        # Verificar se temos entidades consolidadas
        if not entidades_consolidadas:
            raise Exception("Nenhuma entidade foi consolidada. Verifique a coleta de dados do New Relic.")
            
        logger.info(f"Total de {len(entidades_consolidadas)} entidades consolidadas de {len(guids_processados)} GUIDs únicos")
        resultado["detalhes"]["total_entidades_consolidadas"] = len(entidades_consolidadas)
        resultado["acoes"].append(f"Entidades consolidadas: {len(entidades_consolidadas)}")
        
        # Atualizar o cache com as entidades consolidadas
        logger.info("Etapa 4: Atualizando o cache com as entidades consolidadas...")
        _cache["dados"]["entidades"] = entidades_consolidadas
        
        # Salvar cache atualizado em disco
        logger.info("Etapa 5: Salvando cache atualizado em disco...")
        salvo = await salvar_cache_no_disco()
        if not salvo:
            raise Exception("Falha ao salvar cache em disco")
        
        resultado["acoes"].append("Cache com entidades consolidadas salvo em disco")
        
        # Verificar o resultado
        novo_cache = await get_cache()
        entidades_no_cache = novo_cache.get("entidades", [])
        
        if len(entidades_no_cache) == len(entidades_consolidadas):
            resultado["status"] = "sucesso"
            logger.info("Cache corrigido com sucesso!")
            resultado["acoes"].append("Verificação final: cache corretamente atualizado!")
        else:
            resultado["status"] = "alerta"
            diferenca = abs(len(entidades_no_cache) - len(entidades_consolidadas))
            logger.warning(f"Possível discrepância no cache: {diferenca} entidades")
            resultado["acoes"].append(f"ALERTA: Diferença de {diferenca} entidades após salvamento")
    
    except Exception as e:
        logger.error(f"Erro ao corrigir cache: {e}", exc_info=True)
        resultado["status"] = "erro"
        resultado["detalhes"]["erro"] = str(e)
        resultado["acoes"].append(f"Erro: {str(e)}")
    
    # Salvar relatório da correção
    caminho_relatorio = Path("historico") / f"correcao_cache_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path("historico").mkdir(exist_ok=True)
    
    with open(caminho_relatorio, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Relatório da correção salvo em: {caminho_relatorio}")
    return resultado

if __name__ == "__main__":
    print("Iniciando correção do cache e consolidação de entidades...")
    resultado = asyncio.run(corrigir_cache_e_consolidar_entidades())
    print(f"Status da operação: {resultado['status']}")
    print(f"Total de entidades consolidadas: {resultado['detalhes'].get('total_entidades_consolidadas', 0)}")
    print("\nAções realizadas:")
    for acao in resultado["acoes"]:
        print(f"- {acao}")
    print("\nCorreção concluída!")
