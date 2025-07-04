#!/usr/bin/env python3
"""
Script para testar a conexão com o New Relic e consolidar entidades
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Importar funções do collector
from utils.newrelic_collector import coletar_contexto_completo

# Diretório para salvar resultados
CACHE_DIR = Path("historico")
RESULTADO_FILE = CACHE_DIR / "teste_entidades.json"

async def testar_conexao():
    """Testa a conexão com o New Relic e obtém entidades"""
    try:
        logger.info("Iniciando teste de conexão com New Relic...")
        
        # Coletar contexto completo
        contexto = await coletar_contexto_completo()
        
        if not contexto:
            logger.error("Não foi possível obter contexto do New Relic")
            return False
            
        # Verificar cada domínio
        total_entidades = 0
        entidades_com_metricas = 0
        dominios_info = {}
        
        for dominio, entidades in contexto.items():
            if isinstance(entidades, list):
                qtd = len(entidades)
                total_entidades += qtd
                
                # Contar entidades com métricas
                com_metricas = sum(1 for e in entidades if e.get("metricas"))
                entidades_com_metricas += com_metricas
                
                dominios_info[dominio] = {
                    "total": qtd,
                    "com_metricas": com_metricas
                }
        
        logger.info(f"Teste concluído: {total_entidades} entidades encontradas")
        logger.info(f"Entidades com métricas: {entidades_com_metricas}")
        logger.info(f"Informações por domínio: {dominios_info}")
        
        # Salvar resultados para análise
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        resultado = {
            "total_entidades": total_entidades,
            "entidades_com_metricas": entidades_com_metricas,
            "dominios": dominios_info,
            "amostra_entidades": {}
        }
        
        # Adicionar algumas entidades de exemplo para cada domínio
        for dominio, entidades in contexto.items():
            if isinstance(entidades, list) and entidades:
                # Limitar para no máximo 3 entidades por domínio para o arquivo não ficar muito grande
                resultado["amostra_entidades"][dominio] = entidades[:3]
        
        # Salvar o resultado
        with open(RESULTADO_FILE, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Resultado salvo em {RESULTADO_FILE}")
        return resultado
        
    except Exception as e:
        logger.error(f"Erro durante o teste: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    print("Iniciando teste de conexão com New Relic...")
    resultado = asyncio.run(testar_conexao())
    
    if resultado:
        print("\n=== RESUMO DO TESTE ===")
        print(f"Total de entidades: {resultado['total_entidades']}")
        print(f"Entidades com métricas: {resultado['entidades_com_metricas']}")
        print("\nInformações por domínio:")
        for dominio, info in resultado['dominios'].items():
            print(f"  {dominio}: {info['total']} entidades ({info['com_metricas']} com métricas)")
        print(f"\nResultado completo salvo em {RESULTADO_FILE}")
    else:
        print("ERRO: Falha no teste de conexão.")
        sys.exit(1)
