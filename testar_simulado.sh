#!/bin/sh
# Script para executar testes com dados simulados

# Limpar a tela
clear

# Exibir mensagem
echo "====================================================="
echo "Executando testes do coletor avançado com dados simulados"
echo "====================================================="

# Configurar ambiente para usar dados simulados
export USE_MOCK_DATA=true

# Verificar se o diretório de mock data existe
mkdir -p mock_data

# Executar o script de teste
python -c "
import sys
import os

# Adicionar diretório pai ao path para permitir importações relativas
sys.path.insert(0, os.path.abspath('.'))

# Importar classes necessárias
from backend.utils.test_helpers import MockNewRelicCollector
from test_advanced_collector import TestReport

# Criar relatório e coletor
report = TestReport()
collector = MockNewRelicCollector()

# Definir funções de teste necessárias
async def run_tests():
    import asyncio
    from test_advanced_collector import (
        test_kubernetes_metrics,
        test_serverless_metrics,
        test_dashboard_analysis,
        test_all_dashboard_nrql,
        test_infrastructure_details,
        test_capacity_report,
        test_full_entity_data
    )
    
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
"

# Pausar para que o usuário possa ver os resultados
echo ""
echo "Pressione ENTER para continuar..."
read
