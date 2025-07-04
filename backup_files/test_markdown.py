import unittest
import importlib

class TestMarkdownImport(unittest.TestCase):
    def test_import_markdown(self):
        try:
            importlib.import_module('utils.relatorio_generator')
        except Exception as e:
            self.fail(f'Erro ao importar utils.relatorio_generator: {e}')

if __name__ == "__main__":
    unittest.main()
