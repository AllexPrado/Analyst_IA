import unittest
import asyncio
import sys
import os
import time
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

# Garante que o diretório backend está no sys.path para importar utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.newrelic_collector import buscar_entidades_por_guids, coletar_metricas_nrql, buscar_todas_entidades, executar_nrql_graphql
from utils.openai_connector import verificar_conectividade, gerar_resposta_ia

class TestNewRelicCollector(unittest.IsolatedAsyncioTestCase):
    async def test_buscar_entidades_por_guids(self):
        guids = ["test-guid-1", "test-guid-2"]
        entidades = await buscar_entidades_por_guids(guids)
        self.assertIsInstance(entidades, list)
        self.assertGreaterEqual(len(entidades), 0)

    async def test_coletar_metricas_nrql(self):
        guid = "test-guid"
        periodo = "7d"
        domain = "APM"
        metricas = await coletar_metricas_nrql(guid, periodo, domain)
        self.assertIsInstance(metricas, dict)
        self.assertGreaterEqual(len(metricas), 0)

    @patch('utils.newrelic_collector.aiohttp.ClientSession', new_callable=MagicMock)
    async def test_buscar_todas_entidades_valida(self, mock_session):
        # Mock da resposta da API
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={
            "data": {
                "actor": {
                    "entitySearch": {
                        "results": {
                            "entities": [
                                {"guid": "abc123", "name": "App1", "domain": "APM", "entityType": "APPLICATION", "tags": [], "reporting": True},
                                {"guid": "def456", "name": "Infra1", "domain": "INFRA", "entityType": "HOST", "tags": [], "reporting": True}
                            ]
                        }
                    }
                }
            }
        })
        mock_post_ctx = MagicMock()
        mock_post_ctx.__aenter__.return_value = mock_response
        mock_post_ctx.__aexit__.return_value = AsyncMock()
        mock_session.return_value.post.return_value = mock_post_ctx
        session = mock_session.return_value
        entidades = await buscar_todas_entidades(session)
        self.assertIsInstance(entidades, list)
        self.assertGreater(len(entidades), 0)
        for ent in entidades:
            self.assertIn('guid', ent)
            self.assertIn('name', ent)
            self.assertIn('domain', ent)
            self.assertIsNotNone(ent['guid'])
            self.assertIsNotNone(ent['name'])
            self.assertIsNotNone(ent['domain'])

class TestNRQLValidation(unittest.IsolatedAsyncioTestCase):
    @patch('utils.newrelic_collector.aiohttp.ClientSession', new_callable=AsyncMock)
    async def test_nrql_query_tamanho_excedido(self, mock_session):
        query_excedida = "SELECT * " + "FROM Transaction " * 1000
        session = mock_session.return_value
        resultados = await executar_nrql_graphql(session, query_excedida)
        self.assertEqual(resultados, [])

    @patch('utils.newrelic_collector.aiohttp.ClientSession', new_callable=AsyncMock)
    async def test_nrql_query_sem_select(self, mock_session):
        query_invalida = "FROM Transaction WHERE duration > 5"
        session = mock_session.return_value
        resultados = await executar_nrql_graphql(session, query_invalida)
        self.assertEqual(resultados, [])

    @patch('utils.newrelic_collector.aiohttp.ClientSession', new_callable=MagicMock)
    async def test_nrql_query_valida(self, mock_session):
        query_valida = "SELECT max(duration) FROM Transaction"
        def make_response():
            mock_response = MagicMock()
            mock_response.json = AsyncMock(return_value={
                "data": {
                    "actor": {
                        "account": {
                            "nrql": {
                                "results": [{"max.duration": 123}]
                            }
                        }
                    }
                }
            })
            mock_response.status = 200
            mock_post_ctx = MagicMock()
            mock_post_ctx.__aenter__.return_value = mock_response
            mock_post_ctx.__aexit__.return_value = AsyncMock()
            return mock_post_ctx
        mock_session.return_value.post.side_effect = lambda *a, **kw: make_response()
        session = mock_session.return_value
        resultados = await executar_nrql_graphql(session, query_valida)
        self.assertIsInstance(resultados, list)
        self.assertGreater(len(resultados), 0)

class TestRetryMechanism(unittest.IsolatedAsyncioTestCase):
    @patch('utils.newrelic_collector.aiohttp.ClientSession', new_callable=AsyncMock)
    async def test_retry_backoff_exponencial(self, mock_session):
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value = mock_response
        mock_response.status = 429
        mock_response.json.return_value = {
            "errors": [{"message": "Rate limit exceeded"}]
        }
        mock_session.return_value.post.return_value = mock_response
        session = mock_session.return_value
        start_time = time.time()
        resultados = await executar_nrql_graphql(session, "SELECT max(duration) FROM Transaction")
        end_time = time.time()
        self.assertEqual(resultados, [])
        self.assertGreater(end_time - start_time, 1)  # Verifica se o backoff foi aplicado

    @patch('utils.newrelic_collector.aiohttp.ClientSession', new_callable=AsyncMock)
    async def test_cache_usage(self, mock_session):
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value = mock_response
        mock_response.json.return_value = {
            "data": {
                "actor": {
                    "account": {
                        "nrql": {
                            "results": [{"max.duration": 123}]
                        }
                    }
                }
            }
        }
        mock_session.return_value.post.return_value = mock_response
        session = mock_session.return_value
        resultados_1 = await executar_nrql_graphql(session, "SELECT max(duration) FROM Transaction")
        resultados_2 = await executar_nrql_graphql(session, "SELECT max(duration) FROM Transaction")
        self.assertEqual(resultados_1, resultados_2)  # Verifica se o cache foi utilizado

class TestOpenAIConnector(unittest.IsolatedAsyncioTestCase):
    async def test_verificar_conectividade_sucesso(self):
        with patch("utils.openai_connector.httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value.status_code = 200
            resultado = await verificar_conectividade("api.openai.com")
            self.assertTrue(resultado)

    async def test_verificar_conectividade_falha(self):
        with patch("utils.openai_connector.httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.RequestError("Erro de conexão")
            resultado = await verificar_conectividade("api.openai.com")
            self.assertFalse(resultado)

    async def test_gerar_resposta_ia_conectividade_falha(self):
        with patch("utils.openai_connector.verificar_conectividade", new_callable=AsyncMock) as mock_verificar:
            mock_verificar.return_value = False
            with self.assertRaises(RuntimeError) as context:
                await gerar_resposta_ia("Teste de prompt")
            self.assertIn("Erro de conectividade com a API da OpenAI", str(context.exception))

    async def test_gerar_resposta_ia_conexao_falha(self):
        with patch("utils.openai_connector.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = httpx.ConnectError("Erro de conexão")
            with self.assertRaises(RuntimeError) as context:
                await gerar_resposta_ia("Teste de prompt")
            self.assertIn("Erro de conectividade com a API da OpenAI", str(context.exception))

if __name__ == "__main__":
    unittest.main()
