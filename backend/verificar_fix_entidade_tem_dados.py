"""
Este script verifica a distribuição de entidades por domínio após a correção
da função entidade_tem_dados, mostrando quantas entidades passaram na validação.
"""
import os
import sys
import asyncio
import logging
import json
from collections import Counter
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)

# Import required modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.newrelic_collector import buscar_todas_entidades, coletar_metricas_entidade, entidade_tem_dados
import aiohttp

async def main():
    """Test the distribution of entities by domain and checking if they have valid data"""
    logger.info("Iniciando verificação da distribuição de entidades por domínio")
    
    # Get all entities
    async with aiohttp.ClientSession() as session:
        entidades = await buscar_todas_entidades(session)
        
        if not entidades:
            logger.error("Não foi possível obter as entidades")
            return
            
        logger.info(f"Total de entidades encontradas: {len(entidades)}")
        
        # Count by domain
        dominios = Counter([e.get('domain', 'DESCONHECIDO') for e in entidades])
        logger.info(f"Entidades por domínio: {dict(dominios)}")
        
        # Test sample entities from different domains
        resultados = {}
        for dominio in dominios.keys():
            # Get a few entities of this domain
            tipo_entidades = [e for e in entidades if e.get('domain') == dominio][:5]
            
            # Skip if no entities of this domain
            if not tipo_entidades:
                continue
                
            # Test each entity
            resultados[dominio] = {'total': len(tipo_entidades), 'com_dados': 0, 'entidades': []}
            
            for entidade in tipo_entidades:
                logger.info(f"Testando entidade {entidade['name']} do domínio {dominio}")
                  # Fetch metrics for this entity
                metricas = await coletar_metricas_entidade(entidade)
                
                # Check if it has data
                tem_dados = entidade_tem_dados(metricas)
                
                # Record result
                resultado_entidade = {
                    'nome': entidade['name'],
                    'guid': entidade['guid'],
                    'tem_dados': tem_dados
                }
                resultados[dominio]['entidades'].append(resultado_entidade)
                
                if tem_dados:
                    resultados[dominio]['com_dados'] += 1
        
        # Save results
        output = {
            'timestamp': datetime.now().isoformat(),
            'resultados': resultados
        }
        
        with open('verificacao_entidades_pos_fix.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Resumo dos resultados:")
        for dominio, dados in resultados.items():
            logger.info(f"{dominio}: {dados['com_dados']}/{dados['total']} entidades com dados")
        
if __name__ == "__main__":
    asyncio.run(main())
