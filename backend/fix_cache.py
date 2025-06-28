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

async def buscar_entidades():
    if not NEW_RELIC_API_KEY or not NEW_RELIC_ACCOUNT_ID:
        logger.error("Credenciais do New Relic não configuradas!")
        return None
        
    logger.info(f"New Relic Account ID: {NEW_RELIC_ACCOUNT_ID}")
    logger.info(f"New Relic API Key (primeiros 5 caracteres): {NEW_RELIC_API_KEY[:5]}...")

    url = "https://api.newrelic.com/graphql"
    headers = {
        "API-Key": NEW_RELIC_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Consulta GraphQL para buscar TODAS as entidades incluindo INFRA
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
              reporting
            }}
          }}
          count
        }}
      }}
    }}
    '''
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={"query": query}, timeout=60) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if data.get("errors"):
                        logger.error(f"Erros na resposta GraphQL: {data['errors']}")
                        return None
                    
                    results = data["data"]["actor"]["entitySearch"]["results"]["entities"]
                    count = data["data"]["actor"]["entitySearch"]["count"]
                    
                    logger.info(f"Entidades encontradas: {count}")
                    
                    # Processar entidades
                    entidades = []
                    dominios = set()
                    
                    for ent in results:
                        domain = ent.get("domain", "UNKNOWN")
                        dominios.add(domain)
                        
                        entidade = {
                            "guid": ent.get("guid"),
                            "name": ent.get("name", "Sem nome"),
                            "domain": domain,
                            "type": ent.get("entityType", "Desconhecido"),
                            "reporting": ent.get("reporting", False),
                            "metricas": {}  # Inicialização padrão
                        }
                        
                        entidades.append(entidade)
                    
                    # Log para depuração
                    logger.info(f"Domínios encontrados: {sorted(list(dominios))}")
                    
                    # Contar por domínio
                    contagem_dominios = {}
                    for entidade in entidades:
                        domain = entidade["domain"]
                        if domain not in contagem_dominios:
                            contagem_dominios[domain] = 0
                        contagem_dominios[domain] += 1
                    
                    for domain, qtd in sorted(contagem_dominios.items()):
                        logger.info(f"Domínio {domain}: {qtd} entidades")
                    
                    # Salvar no cache
                    with open("entidades_atualizado.json", "w", encoding="utf-8") as f:
                        json.dump({
                            "timestamp": "2025-06-23T17:30:00",
                            "entidades": entidades
                        }, f, ensure_ascii=False, indent=2)
                        
                    logger.info(f"Entidades salvas em 'entidades_atualizado.json'")
                    return entidades
                else:
                    logger.error(f"Erro HTTP: {resp.status}")
                    error_text = await resp.text()
                    logger.error(f"Detalhe: {error_text}")
                    return None
    except Exception as e:
        logger.error(f"Erro ao buscar entidades: {e}")
        return None

# Executar função principal
if __name__ == "__main__":
    entidades = asyncio.run(buscar_entidades())
    if entidades:
        print(f"Total de {len(entidades)} entidades encontradas.")
    else:
        print("Não foi possível obter entidades.")
