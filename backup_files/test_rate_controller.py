"""
Teste direto e simples do circuit breaker e rate limiting
"""

import sys
from pathlib import Path

# Adiciona backend ao path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

try:
    from utils.newrelic_collector import rate_controller
    print("✅ Import do rate_controller bem-sucedido")
    
    # Testa status inicial
    print("Status inicial:")
    status = rate_controller.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Simula algumas falhas
    print("\nSimulando falhas...")
    for i in range(5):
        rate_controller.record_failure(is_rate_limit=(i % 2 == 0))
        print(f"  Falha {i+1} - State: {rate_controller.circuit_state}")
    
    # Simula sucessos
    print("\nSimulando sucessos...")
    for i in range(3):
        rate_controller.record_success()
        print(f"  Sucesso {i+1} - State: {rate_controller.circuit_state}")
    
    print("\n✅ Teste do rate controller concluído com sucesso!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
