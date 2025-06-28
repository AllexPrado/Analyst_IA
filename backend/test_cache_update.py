import unittest
import importlib
import asyncio

class TestCacheUpdateImport(unittest.TestCase):
    def test_import_cache_update(self):
        try:
            cache = importlib.import_module('utils.cache')
            self.assertTrue(hasattr(cache, 'atualizar_cache_completo'))
            self.assertTrue(hasattr(cache, 'atualizar_cache_incremental'))
            self.assertTrue(hasattr(cache, 'forcar_atualizacao_cache'))
        except Exception as e:
            self.fail(f'Erro ao importar utils.cache: {e}')

    def test_cache_functions(self):
        try:
            cache = importlib.import_module('utils.cache')
            self.assertTrue(hasattr(cache, 'carregar_cache_do_disco'))
            self.assertTrue(hasattr(cache, 'salvar_cache_no_disco'))
            self.assertTrue(hasattr(cache, 'salvar_consulta_historica'))
            self.assertTrue(hasattr(cache, 'buscar_no_cache_por_pergunta'))
        except Exception as e:
            self.fail(f'Erro ao verificar funções do cache: {e}')

    def test_cache_configuracoes(self):
        try:
            cache = importlib.import_module('utils.cache')
            # Verificar se o período de atualização está configurado para 24h
            self.assertEqual(cache.CACHE_UPDATE_INTERVAL, 86400)
            # Verificar se o cache em memória está inicializado corretamente
            self.assertTrue("metadados" in cache._cache)
            self.assertTrue("dados" in cache._cache)
            self.assertTrue("consultas_historicas" in cache._cache)
        except Exception as e:
            self.fail(f'Erro ao verificar configuração do cache: {e}')


if __name__ == "__main__":
    unittest.main()
