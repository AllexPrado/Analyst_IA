import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

NEWRELIC_API_KEY = os.getenv("NEWRELIC_API_KEY")
NEWRELIC_ACCOUNT_ID = os.getenv("NEWRELIC_ACCOUNT_ID")
GRAPHQL_URL = "https://api.newrelic.com/graphql"
HEADERS = {
    "Api-Key": NEWRELIC_API_KEY,
    "Content-Type": "application/json"
}

# Períodos para coleta
PERIODOS = {
    "30min": "SINCE 30 minutes ago",
    "60min": "SINCE 60 minutes ago",
    "24h": "SINCE 1 day ago",
    "7d": "SINCE 7 days ago",
    "30d": "SINCE 30 days ago"
}

# NRQL_QUERIES igual ao seu script original...
NRQL_QUERIES = { ... }  # Copie o bloco do seu script aqui

def get_all_entity_guids():
    query = f'''
    {{
      actor {{
        entitySearch(queryBuilder: {{name: ""}}) {{
          results {{
            entities {{
              guid
              name
              domain
              entityType
            }}
            nextCursor
          }}
        }}
      }}
    }}
    '''
    guids = []
    cursor = None
    while True:
        payload = {"query": query}
        if cursor:
            payload = {"query": query.replace('results {', f'results(cursor: \"{cursor}\") {{')}
        resp = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload)
        data = resp.json()
        entities = data["data"]["actor"]["entitySearch"]["results"]["entities"]
        guids.extend(entities)
        cursor = data["data"]["actor"]["entitySearch"]["results"].get("nextCursor")
        if not cursor:
            break
    return guids

def coletar_todas_metricas_nrql(guid, tipo="infra", periodos=PERIODOS, account_id=None):
    if not account_id:
        account_id = NEWRELIC_ACCOUNT_ID
    results = {}
    if tipo not in NRQL_QUERIES:
        return {"erro": f"Tipo {tipo} não suportado."}
    for periodo_nome, since in periodos.items():
        results[periodo_nome] = {}
        for metrica_nome, nrql_tpl in NRQL_QUERIES[tipo].items():
            nrql = nrql_tpl.format(guid=guid, since=since)
            query = f"""
            {{
              actor {{
                account(id: {account_id}) {{
                  nrql(query: \"{nrql}\") {{
                    results
                  }}
                }}
              }}
            }}
            """
            try:
                resp = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": query})
                data = resp.json()
                results[periodo_nome][metrica_nome] = data["data"]["actor"]["account"]["nrql"]["results"]
            except Exception as e:
                results[periodo_nome][metrica_nome] = f"Erro: {e}"
    return results

if __name__ == "__main__":
    entidades = get_all_entity_guids()
    print(f"Total de entidades encontradas: {len(entidades)}")
    for ent in entidades:
        print(f"\n==== {ent['name']} ({ent['domain']}/{ent['entityType']}) ====")
        tipo = ent['domain'].lower() if ent['domain'] else "infra"
        metricas = coletar_todas_metricas_nrql(ent['guid'], tipo=tipo)
        print(json.dumps(metricas, indent=2, ensure_ascii=False))
