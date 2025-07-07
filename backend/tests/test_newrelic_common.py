import asyncio
import aiohttp
import pytest
from utils.newrelic_common import execute_nrql_query_common, execute_graphql_query_common

@pytest.mark.asyncio
async def test_nrql_query_closed_session():
    # Cria uma sessão e fecha imediatamente
    session = aiohttp.ClientSession()
    await session.close()
    # Deve criar uma nova sessão internamente e não lançar erro
    result = await execute_nrql_query_common(
        nrql="{ actor { account(id: 0) { nrql(query: \"SELECT 1\") { results } } } }",
        headers={"Api-Key": "fake", "Content-Type": "application/json"},
        url="https://api.newrelic.com/graphql",
        session=session,
        max_retries=1,
        retry_delay=0.1
    )
    assert isinstance(result, dict)

@pytest.mark.asyncio
async def test_graphql_query_closed_session():
    session = aiohttp.ClientSession()
    await session.close()
    result = await execute_graphql_query_common(
        query="{ actor { account(id: 0) { name } } }",
        headers={"Api-Key": "fake", "Content-Type": "application/json"},
        url="https://api.newrelic.com/graphql",
        session=session,
        max_retries=1,
        retry_delay=0.1
    )
    assert isinstance(result, dict)

@pytest.mark.asyncio
async def test_nrql_query_concurrent():
    async def run_query():
        return await execute_nrql_query_common(
            nrql="{ actor { account(id: 0) { nrql(query: \"SELECT 1\") { results } } } }",
            headers={"Api-Key": "fake", "Content-Type": "application/json"},
            url="https://api.newrelic.com/graphql",
            max_retries=1,
            retry_delay=0.1
        )
    results = await asyncio.gather(*[run_query() for _ in range(5)])
    assert all(isinstance(r, dict) for r in results)

@pytest.mark.asyncio
async def test_graphql_query_concurrent():
    async def run_query():
        return await execute_graphql_query_common(
            query="{ actor { account(id: 0) { name } } }",
            headers={"Api-Key": "fake", "Content-Type": "application/json"},
            url="https://api.newrelic.com/graphql",
            max_retries=1,
            retry_delay=0.1
        )
    results = await asyncio.gather(*[run_query() for _ in range(5)])
    assert all(isinstance(r, dict) for r in results)
