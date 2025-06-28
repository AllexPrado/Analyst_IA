import unittest
import asyncio
import os
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

class TestSimpleCache(unittest.TestCase):
    """
    Testes simples para o funcionamento básico do cache.
    Não requer dependências externas.
    """
    
    def setUp(self):
        self.cache_module = None
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from utils import cache
            self.cache_module = cache
        except ImportError as e:
            self.fail(f"Erro ao importar módulo de cache: {e}")
    
    def test_cache_inicializado(self):
        """Verifica se o cache é inicializado corretamente"""
        self.assertIsNotNone(self.cache_module)
        self.assertTrue(hasattr(self.cache_module, "_cache"))
        self.assertIn("metadados", self.cache_module._cache)
        self.assertIn("dados", self.cache_module._cache)
        self.assertIn("consultas_historicas", self.cache_module._cache)

    def test_cache_intervalo_diario(self):
        """Verifica se o intervalo de cache está configurado para diário (86400 segundos)"""
        self.assertEqual(self.cache_module.CACHE_UPDATE_INTERVAL, 86400)
    
    def test_diagnostico_cache(self):
        """Verifica se o diagnóstico do cache retorna as informações corretas"""
        diagnostico = self.cache_module.diagnosticar_cache()
        self.assertIsInstance(diagnostico, dict)
        self.assertIn("metadados", diagnostico)
        self.assertIn("status", diagnostico)
        self.assertIn("total_chaves_dados", diagnostico)
    
    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    @patch('os.makedirs')
    def test_cache_disk_operations(self, mock_makedirs, mock_exists, mock_open):
        """Testa operações de disco do cache de forma isolada"""
        # Prepara mocks
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.read.return_value = '{"timestamp": "2025-06-23T12:00:00", "apm": [], "browser": []}'
        mock_file.write = MagicMock()
        mock_open.return_value = mock_file
        
        # Testa carregar_cache_do_disco
        loop = asyncio.new_event_loop()
        resultado = loop.run_until_complete(self.cache_module.carregar_cache_do_disco())
        loop.close()
        
        self.assertTrue(resultado)
        mock_makedirs.assert_called()
        mock_exists.assert_called()
        mock_file.read.assert_called_once()
    
    def test_deteccao_dados_recentes(self):
        """Testa se o sistema detecta corretamente necessidade de dados recentes"""
        perguntas_tempo_real = [
            "Como está o sistema agora?",
            "Quais são os incidentes no momento?",
            "Qual é a performance atual?",
            "Mostre os erros das últimas horas"
        ]
        
        perguntas_historicas = [
            "Como foi a performance na semana passada?",
            "Quais foram os incidentes do mês passado?",
            "Mostre um resumo dos erros do último trimestre"
        ]
        
        # Função mock para testar a detecção
        async def _testar_deteccao(pergunta):
            palavras_tempo_real = ["agora", "momento", "atual", "recente", "hoje", "últimas horas"]
            precisa_dados_recentes = any(palavra in pergunta.lower() for palavra in palavras_tempo_real)
            return precisa_dados_recentes
        
        loop = asyncio.new_event_loop()
        
        # Testa perguntas que devem requerer dados recentes
        for pergunta in perguntas_tempo_real:
            resultado = loop.run_until_complete(_testar_deteccao(pergunta))
            self.assertTrue(resultado, f"Falha ao detectar necessidade de dados recentes: '{pergunta}'")
        
        # Testa perguntas que não requerem dados recentes
        for pergunta in perguntas_historicas:
            resultado = loop.run_until_complete(_testar_deteccao(pergunta))
            self.assertFalse(resultado, f"Detectou incorretamente necessidade de dados recentes: '{pergunta}'")
        
        loop.close()

if __name__ == "__main__":
    unittest.main()
