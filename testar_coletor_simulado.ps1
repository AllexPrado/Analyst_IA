# Executando testes do coletor avançado com dados simulados
Write-Host "Executando testes do coletor avançado com dados simulados..." -ForegroundColor Green

# Definir variável de ambiente temporária para usar dados simulados
$env:USE_MOCK_DATA = "true"

# Executar o script de teste
python test_advanced_collector.py

# Pausar para que o usuário possa ver os resultados
Write-Host "`nPressione qualquer tecla para continuar..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
