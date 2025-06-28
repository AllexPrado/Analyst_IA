#!/usr/bin/env python3
"""
Script para iniciar o backend com entidades consolidadas
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Diretório para cache
CACHE_DIR = Path("historico")
ENTIDADES_FILE = CACHE_DIR / "entidades_consolidadas.json"

# Importar funções necessárias
from utils.newrelic_collector import coletar_contexto_completo
from utils.cache import atualizar_cache_completo, get_cache

async def consolidar_entidades():
    """Consolida entidades de todos os domínios em uma única lista"""
    try:
        logger.info("Iniciando consolidação de entidades...")
        
        # Verificar se já existe cache recente
        cache = await get_cache()
        
        # Forçar coleta do New Relic
        contexto = await coletar_contexto_completo()
        
        if not contexto:
            logger.error("Não foi possível obter contexto do New Relic")
            return False
        
        # Consolidar entidades de todos os domínios
        entidades = []
        dominios_para_verificar = ['apm', 'browser', 'infra', 'db', 'mobile', 'iot', 'serverless', 'synth', 'ext']
        
        for dominio in dominios_para_verificar:
            if dominio in contexto and isinstance(contexto[dominio], list):
                for entidade in contexto[dominio]:
                    # Evitar duplicatas
                    guid = entidade.get("guid")
                    if guid and not any(e.get("guid") == guid for e in entidades):
                        entidades.append(entidade)
        
        # Contagem de entidades por domínio
        dominios = {}
        entidades_com_metricas = 0
        
        for entidade in entidades:
            domain = entidade.get("domain", "UNKNOWN")
            if domain not in dominios:
                dominios[domain] = {
                    "total": 0,
                    "com_metricas": 0
                }
            
            dominios[domain]["total"] += 1
            
            # Verificar se tem métricas
            if entidade.get("metricas"):
                dominios[domain]["com_metricas"] += 1
                entidades_com_metricas += 1
        
        # Adicionar entidades consolidadas ao cache
        contexto["entidades"] = entidades
        
        # Atualizar cache completo
        await atualizar_cache_completo(contexto)
        
        # Também salvar arquivo separado para diagnóstico
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        with open(ENTIDADES_FILE, 'w', encoding='utf-8') as f:
            resultado = {
                "entidades": entidades,
                "total": len(entidades),
                "comMetricas": entidades_com_metricas,
                "dominios": list(dominios.keys()),
                "dominiosInfo": dominios
            }
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Entidades consolidadas: {len(entidades)} ({entidades_com_metricas} com métricas)")
        logger.info(f"Informações salvas em {ENTIDADES_FILE}")
        
        return {
            "entidades": len(entidades),
            "com_metricas": entidades_com_metricas,
            "dominios": dominios
        }
    
    except Exception as e:
        logger.error(f"Erro ao consolidar entidades: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    print("Consolidando entidades antes de iniciar o backend...")
    resultado = asyncio.run(consolidar_entidades())
    
    if resultado:
        print("\n=== ENTIDADES CONSOLIDADAS ===")
        print(f"Total de entidades: {resultado['entidades']}")
        print(f"Entidades com métricas: {resultado['com_metricas']}")
        print("\nDomínios encontrados:")
        for dominio, info in resultado['dominios'].items():
            print(f"  {dominio}: {info['total']} entidades ({info['com_metricas']} com métricas)")
        print("\n=== INICIANDO BACKEND ===")
        
        # Iniciar o backend usando uvicorn
        import uvicorn
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    else:
        print("ERRO: Falha ao consolidar entidades.")
        sys.exit(1)
