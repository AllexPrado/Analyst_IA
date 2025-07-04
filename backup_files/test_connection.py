import unittest
import importlib

class TestConnectionImport(unittest.TestCase):
    def test_import_newrelic_collector(self):
        try:
            collector = importlib.import_module('utils.newrelic_collector')
            self.assertTrue(hasattr(collector, 'buscar_entidades_por_guids'))
        except Exception as e:
            self.fail(f'Erro ao importar utils.newrelic_collector: {e}')

if __name__ == "__main__":
    unittest.main()
