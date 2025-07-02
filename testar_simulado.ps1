# Script para executar testes com dados simulados do coletor avançado

# Limpar a tela
Clear-Host

# Exibir mensagem
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Executando testes do coletor avançado com dados simulados" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Configurar ambiente para usar dados simulados
$env:USE_MOCK_DATA = "true"

# Verificar se o diretório de mock data existe
if (-not (Test-Path -Path "mock_data")) {
    New-Item -ItemType Directory -Path "mock_data" | Out-Null
}

# Executar o script Python inline
python -c @"
import sys
import os

# Adicionar diretório pai ao path para permitir importações relativas
sys.path.insert(0, os.path.abspath('.'))

# Importar classes necessárias
try:
    from backend.utils.test_helpers import MockNewRelicCollector
    from test_advanced_collector import TestReport
except ImportError as e:
    print(f'Erro ao importar: {e}')
    sys.exit(1)

# Criar relatório e coletor
report = TestReport()
collector = MockNewRelicCollector()

# Definir função de teste
async def run_tests():
    import asyncio
    
    try:
        # Importar funções de teste
        from test_advanced_collector import (
            test_kubernetes_metrics,
            test_serverless_metrics,
            test_dashboard_analysis,
            test_all_dashboard_nrql,
            test_infrastructure_details,
            test_capacity_report,
            test_full_entity_data
        )
    except ImportError as e:
        print(f'Erro ao importar funções de teste: {e}')
        return
    
    print('='*60)
    print('INICIANDO TESTES DO COLETOR AVANÇADO COM DADOS SIMULADOS')
    print('='*60)
    
    print('✓ Coletor mock inicializado com sucesso')
    
    # Executar testes individuais
    await test_kubernetes_metrics(collector, report)
    await test_serverless_metrics(collector, report)
    await test_dashboard_analysis(collector, report)
    await test_all_dashboard_nrql(collector, report)
    await test_infrastructure_details(collector, report)
    await test_capacity_report(collector, report)
    
    # Teste de coleta completa
    await test_full_entity_data(collector, report)
    
    # Salvar e imprimir relatório
    report.save_report('mock_test_results.json')
    report.print_summary()
    
    print('='*60)
    print('TESTES FINALIZADOS')
    print('='*60)

# Executar testes de forma assíncrona
import asyncio
asyncio.run(run_tests())
"@

# Pausar para que o usuário possa ver os resultados
Write-Host "`nPressione qualquer tecla para continuar..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
