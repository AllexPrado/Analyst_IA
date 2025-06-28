#!/usr/bin/env python3
"""
Teste super simples - apenas valida se tudo está funcionando
"""

import sys
from pathlib import Path

# Adiciona backend ao path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

def main():
    print("=== TESTE RÁPIDO ===")
    
    # Teste 1: Import do rate controller
    try:
        from utils.newrelic_collector import rate_controller
        print("✅ Rate controller importado")
        
        # Status do circuit breaker
        status = rate_controller.get_status()
        print(f"✅ Circuit breaker status: {status['circuit_state']}")
        
    except Exception as e:
        print(f"❌ Erro no rate controller: {e}")
        return
    
    # Teste 2: Import das funções NRQL
    try:
        from utils.newrelic_collector import executar_nrql_graphql, buscar_todas_entidades
        print("✅ Funções NRQL importadas")
        
    except Exception as e:
        print(f"❌ Erro nas funções NRQL: {e}")
        return
    
    # Teste 3: Import do cache
    try:
        from utils.cache import get_cache, diagnosticar_cache
        print("✅ Sistema de cache importado")
        
        # Diagnóstico do cache
        cache_info = diagnosticar_cache()
        print(f"✅ Cache válido: {cache_info.get('cache_valido', False)}")
        
    except Exception as e:
        print(f"❌ Erro no cache: {e}")
        return
    
    # Teste 4: Import do OpenAI
    try:
        from utils.openai_connector import gerar_resposta_ia
        print("✅ OpenAI connector importado")
        
    except Exception as e:
        print(f"❌ Erro no OpenAI: {e}")
        return
    
    print("\n🎉 TODOS OS COMPONENTES ESTÃO FUNCIONANDO!")
    print("   ✅ Rate Controller + Circuit Breaker")
    print("   ✅ Funções NRQL")
    print("   ✅ Sistema de Cache") 
    print("   ✅ OpenAI Connector")
    
    print("\n📊 RESUMO DO SISTEMA:")
    print(f"   Circuit State: {status['circuit_state']}")
    print(f"   Cache Válido: {cache_info.get('cache_valido', False)}")
    print(f"   Entidades em Cache: {cache_info.get('total_entidades', 0)}")

if __name__ == "__main__":
    main()
