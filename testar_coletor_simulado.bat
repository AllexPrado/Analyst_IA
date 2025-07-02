@echo off
echo Executando testes do coletor avancado com dados simulados...
SET USE_MOCK_DATA=true
python test_advanced_collector.py
pause
