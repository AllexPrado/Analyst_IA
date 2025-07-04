#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import asyncio
import aiohttp
import logging
import argparse
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def verify_newrelic_connectivity(api_key=None, account_id=None, timeout=30.0):
    """
    Verifica a conectividade com o New Relic.
    
    Args:
        api_key: API Key do New Relic
        account_id: ID da conta do New Relic
        timeout: Tempo limite em segundos para a requisição
    
    Returns:
        bool: True se a conectividade estiver OK, False caso contrário
    """
    # Carregar credenciais de env se não fornecidas
    try:
        # Carregar variáveis de ambiente do arquivo .env
        load_dotenv()
        api_key = api_key or os.environ.get('NEW_RELIC_API_KEY')
        account_id = account_id or os.environ.get('NEW_RELIC_ACCOUNT_ID')
        
        if not api_key:
            logger.error("New Relic API Key não fornecida")
            return False
            
        if not account_id:
            logger.error("New Relic Account ID não fornecido")
            return False
            
        # Headers da requisição
        headers = {
            'Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        # URL do GraphQL
        url = 'https://api.newrelic.com/graphql'
        
        # Query simples para testar a conectividade
        query = """
        {
          actor {
            account(id: %s) {
              name
            }
          }
        }
        """ % account_id
        
        # Dados da requisição
        data = {'query': query}
        
        logger.info("Verificando conectividade com o New Relic...")
        
        # Configuração do timeout
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        
        async with aiohttp.ClientSession(timeout=timeout_obj) as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if 'data' in result and 'actor' in result['data']:
                        account_name = result['data']['actor']['account']['name']
                        logger.info(f"✅ Conectividade com o New Relic OK: Conta {account_name} (ID: {account_id})")
                        return True
                    else:
                        logger.error(f"❌ Erro na resposta do New Relic: {result}")
                        return False
                else:
                    error = await response.text()
                    logger.error(f"❌ Erro ao conectar ao New Relic: HTTP {response.status} - {error}")
                    return False
    except Exception as e:
        logger.error(f"❌ Erro ao verificar conectividade: {e}")
        return False

def print_recommendations(success):
    """
    Imprime recomendações com base no resultado do teste.
    
    Args:
        success: Resultado do teste de conectividade
    """
    print("\n" + "="*60)
    print("RECOMENDAÇÕES")
    print("="*60)
    
    if success:
        print("✅ Sua conectividade com o New Relic está funcionando corretamente.")
        print("   Você pode executar os testes com credenciais reais:")
        print("   python test_advanced_collector.py")
    else:
        print("❌ Problemas de conectividade detectados com o New Relic.")
        print("\nRecomendações:")
        print("1. Verifique se suas credenciais estão corretas no arquivo .env")
        print("2. Verifique sua conexão de rede e configurações de firewall")
        print("3. Teste usando dados simulados para desenvolvimento:")
        print("   .\testar_simulado.ps1  (PowerShell)")
        print("   testar_coletor_simulado.bat  (CMD)")
        print("4. Se o problema persistir, tente aumentar o timeout:")
        print("   python verificar_conectividade_newrelic.py --timeout 60")
    
    print("="*60)

async def main():
    parser = argparse.ArgumentParser(description="Verifica a conectividade com o New Relic")
    parser.add_argument("--api-key", help="API Key do New Relic")
    parser.add_argument("--account-id", help="ID da conta do New Relic")
    parser.add_argument("--timeout", type=float, default=30.0, help="Tempo limite em segundos para a requisição")
    
    args = parser.parse_args()
    
    success = await verify_newrelic_connectivity(
        api_key=args.api_key,
        account_id=args.account_id,
        timeout=args.timeout
    )
    
    print_recommendations(success)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
