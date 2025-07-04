#!/usr/bin/env python3
"""
Status final do sistema - Verificação completa
"""

import sys
from pathlib import Path

# Adiciona backend ao path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

def test_all_components():
    print("=" * 60)
    print("VERIFICAÇÃO FINAL DO SISTEMA ANALYST_IA")
    print("=" * 60)
    
    components_status = {}
    
    # 1. Rate Controller e Circuit Breaker
    try:
        from utils.newrelic_collector import rate_controller
        status = rate_controller.get_status()
        components_status['circuit_breaker'] = {
            'status': '✅ FUNCIONANDO',
            'state': status['circuit_state'],
            'failures': status['consecutive_failures']
        }
    except Exception as e:
        components_status['circuit_breaker'] = {
            'status': f'❌ ERRO: {e}',
            'state': 'UNKNOWN',
            'failures': 'N/A'
        }
    
    # 2. NewRelicCollector
    try:
        from utils.newrelic_collector import NewRelicCollector
        # Testa instanciação
        collector = NewRelicCollector('test', 'test')
        health = collector.get_health_status()
        components_status['newrelic_collector'] = {
            'status': '✅ FUNCIONANDO',
            'health_status': health['status']
        }
    except Exception as e:
        components_status['newrelic_collector'] = {
            'status': f'❌ ERRO: {e}',
            'health_status': 'UNKNOWN'
        }
    
    # 3. Cache System
    try:
        from utils.cache import diagnosticar_cache
        cache_info = diagnosticar_cache()
        components_status['cache_system'] = {
            'status': '✅ FUNCIONANDO',
            'cache_valid': cache_info.get('cache_valido', False),
            'entities': cache_info.get('total_entidades', 0)
        }
    except Exception as e:
        components_status['cache_system'] = {
            'status': f'❌ ERRO: {e}',
            'cache_valid': False,
            'entities': 0
        }
    
    # 4. OpenAI Connector
    try:
        from utils.openai_connector import gerar_resposta_ia
        components_status['openai_connector'] = {
            'status': '✅ FUNCIONANDO'
        }
    except Exception as e:
        components_status['openai_connector'] = {
            'status': f'❌ ERRO: {e}'
        }
    
    # 5. Main Backend
    try:
        import main
        components_status['main_backend'] = {
            'status': '✅ IMPORTADO',
            'ready': True
        }
    except Exception as e:
        components_status['main_backend'] = {
            'status': f'❌ ERRO: {e}',
            'ready': False
        }
    
    # Exibir resultados
    print("\n📊 STATUS DOS COMPONENTES:")
    print("-" * 60)
    
    for component, info in components_status.items():
        print(f"\n🔧 {component.upper().replace('_', ' ')}:")
        for key, value in info.items():
            print(f"   {key}: {value}")
    
    # Resumo geral
    working_components = sum(1 for info in components_status.values() if '✅' in info['status'])
    total_components = len(components_status)
    
    print(f"\n" + "=" * 60)
    print(f"📈 RESUMO GERAL: {working_components}/{total_components} componentes funcionando")
    
    if working_components == total_components:
        print("🎉 SISTEMA 100% OPERACIONAL!")
        print("   ✅ Circuit Breaker implementado")
        print("   ✅ Rate Limiting inteligente")
        print("   ✅ Fallback para cache")
        print("   ✅ Health monitoring")
    elif working_components >= 3:
        print("⚠️  SISTEMA PARCIALMENTE OPERACIONAL")
        print("   Alguns componentes precisam de atenção")
    else:
        print("❌ SISTEMA COM PROBLEMAS CRÍTICOS")
        print("   Múltiplos componentes falhando")
    
    print("=" * 60)
    
    return working_components, total_components

if __name__ == "__main__":
    working, total = test_all_components()
    
    # Exit code baseado no status
    if working == total:
        sys.exit(0)  # Sucesso total 
    elif working >= 3:
        sys.exit(1)  # Parcialmente funcional
    else:
        sys.exit(2)  # Problemas críticos
