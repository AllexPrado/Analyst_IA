import unittest
import importlib

class TestImports(unittest.TestCase):
    def test_import_utils(self):
        try:
            importlib.import_module('utils.newrelic_collector')
            importlib.import_module('utils.openai_connector')
            importlib.import_module('utils.persona_detector')
        except Exception as e:
            self.fail(f'Erro ao importar módulos utils: {e}')

if __name__ == "__main__":
    unittest.main()
