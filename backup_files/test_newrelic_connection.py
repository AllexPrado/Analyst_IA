import os
import asyncio
import aiohttp
import json
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Obter credenciais
NEW_RELIC_API_KEY = os.getenv("NEW_RELIC_API_KEY")
NEW_RELIC_ACCOUNT_ID = os.getenv("NEW_RELIC_ACCOUNT_ID")

# Verificar se as credenciais estão disponíveis
if not NEW_RELIC_API_KEY or not NEW_RELIC_ACCOUNT_ID:
    logger.error("Credenciais do New Relic não configuradas!")
    exit(1)

async def testar_conexao():
    url = "https://api.newrelic.com/graphql"
    headers = {
        "API-Key": NEW_RELIC_API_KEY,
        "Content-Type": "application/json"
    }
      # Consulta GraphQL para buscar entidades
    query = f'''
    {{
      actor {{
        entitySearch(query: "accountId = {NEW_RELIC_ACCOUNT_ID}") {{
          results {{
            entities {{
              guid
              name
              domain
              entityType
            }}
            nextCursor
          }}
          count
        }}
      }}
    }}
    '''
    
    logger.info(f"Testando conexão com New Relic usando Account ID: {NEW_RELIC_ACCOUNT_ID}")
    logger.info(f"API Key (primeiros 5 caracteres): {NEW_RELIC_API_KEY[:5]}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={"query": query}, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Verificar se há erros
                    if data.get("errors"):
                        logger.error(f"Erros na resposta GraphQL: {data['errors']}")
                        return False
                      # Verificar dados retornados
                    try:
                        results = data["data"]["actor"]["entitySearch"]["results"]
                        entities = results["entities"]
                        count = data["data"]["actor"]["entitySearch"]["count"]
                        
                        logger.info(f"Conexão bem-sucedida! Encontradas {count} entidades.")
                        
                        # Mostrar algumas entidades
                        for i, ent in enumerate(entities[:5]):
                            logger.info(f"Entidade {i+1}: {ent['name']} ({ent['domain']}, {ent['entityType']})")
                        
                        # Salvar em um arquivo JSON
                        with open("test_entities.json", "w") as f:
                            json.dump(entities, f, indent=2)
                            logger.info(f"Entidades salvas em test_entities.json")
                        
                        return True
                    except Exception as e:
                        logger.error(f"Erro ao processar dados: {e}")
                        logger.error(f"Resposta: {data}")
                        return False
                else:
                    logger.error(f"Erro na resposta HTTP: {resp.status}")
                    error_text = await resp.text()
                    logger.error(f"Detalhes: {error_text}")
                    return False
    except Exception as e:
        logger.error(f"Erro ao conectar com New Relic: {e}")
        return False

# Executar o teste de conexão
if __name__ == "__main__":
    asyncio.run(testar_conexao())
