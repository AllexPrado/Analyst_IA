import unittest
import importlib
import asyncio
from unittest.mock import patch, MagicMock

class TestCacheImport(unittest.TestCase):
    def test_import_cache(self):
        try:
            cache = importlib.import_module('utils.cache')
            self.assertTrue(hasattr(cache, 'get_cache'))
        except Exception as e:
            self.fail(f'Erro ao importar utils.cache: {e}')

    def test_cache_diagnostico(self):
        try:
            cache = importlib.import_module('utils.cache')
            diagnóstico = cache.diagnosticar_cache()
            self.assertIsInstance(diagnóstico, dict)
            self.assertIn('metadados', diagnóstico)
            self.assertIn('status', diagnóstico)
        except Exception as e:
            self.fail(f'Erro ao testar diagnóstico de cache: {e}')
    
    @patch('aiofiles.open')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_cache_io(self, mock_stat, mock_exists, mock_open):
        # Simula arquivo existente
        mock_exists.return_value = True
        
        # Simula estatísticas do arquivo
        stat_result = MagicMock()
        stat_result.st_size = 1024 * 1024  # 1 MB
        mock_stat.return_value = stat_result
        
        # Simula operação de arquivo
        mock_file = MagicMock()
        mock_file.__aenter__.return_value = mock_file
        mock_file.read.return_value = "{}"
        mock_open.return_value = mock_file
        
        cache = importlib.import_module('utils.cache')
        diagnóstico = cache.diagnosticar_cache()
        
        # Verifica se tamanho está correto
        self.assertIn('tamanho_disco_mb', diagnóstico)

if __name__ == "__main__":
    unittest.main()
