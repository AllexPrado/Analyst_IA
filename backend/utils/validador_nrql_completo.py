"""
Validador de Métricas NRQL para todas as entidades do New Relic.
Executa queries NRQL para cada entidade encontrada e salva os resultados para auditoria.
"""
import asyncio
import json
import os
from newrelic_advanced_collector import get_all_entities, execute_nrql_query

OUTPUT_FILE = "validador_nrql_resultados.json"
MAX_CONCURRENT = 5  # Limite de concorrência para evitar travamentos

async def validar_nrql_todas_entidades():
    entities = await get_all_entities()
    resultados = []
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async def consulta_entity(entity):
        guid = entity.get("guid")
        nome = entity.get("name")
        if not guid:
            return None
        nrql = f"SELECT * FROM Metric WHERE entityGuid = '{guid}' SINCE 30 MINUTES AGO LIMIT 10"
        async with sem:
            resultado = await execute_nrql_query(nrql)
        return {"guid": guid, "nome": nome, "resultado": resultado}

    tasks = [consulta_entity(entity) for entity in entities]
    for idx, coro in enumerate(asyncio.as_completed(tasks), 1):
        res = await coro
        if res:
            resultados.append(res)
        if idx % 10 == 0:
            print(f"{idx} entidades processadas...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"Validação concluída. Resultados salvos em {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(validar_nrql_todas_entidades())
