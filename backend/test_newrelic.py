#!/usr/bin/env python3
"""Script simples para testar conexão com New Relic."""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

NEW_RELIC_API_KEY = os.getenv("NEW_RELIC_API_KEY")
NEW_RELIC_ACCOUNT_ID = os.getenv("NEW_RELIC_ACCOUNT_ID")

print(f"API Key: {NEW_RELIC_API_KEY[:20]}...")
print(f"Account ID: {NEW_RELIC_ACCOUNT_ID}")

async def test_connection():
    query = f"""
    {{
      actor {{
        entitySearch(query: "accountId = {NEW_RELIC_ACCOUNT_ID}") {{
          count
          results {{
            entities {{
              guid
              name
              domain
            }}
          }}
        }}
      }}
    }}
    """
    
    url = "https://api.newrelic.com/graphql"
    headers = {
        "API-Key": NEW_RELIC_API_KEY,
        "Content-Type": "application/json"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"query": query}, headers=headers) as response:
                print(f"Status: {response.status}")
                result = await response.json()
                print(f"Resultado: {result}")
                
                if 'data' in result:
                    count = result['data']['actor']['entitySearch']['count']
                    print(f"Total de entidades encontradas: {count}")
                    
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
