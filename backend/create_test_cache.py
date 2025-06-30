#!/usr/bin/env python3
"""
Script simplificado para popular o cache com dados de teste se necessário
"""

import json
import os
from datetime import datetime
from pathlib import Path

def create_test_cache():
    """Cria um cache de teste com dados simulados se não conseguir obter dados reais"""
    
    # Diretório de cache
    cache_dir = Path("historico")
    cache_file = cache_dir / "cache_completo.json"
    
    # Verifica se já existe cache
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            
        entidades = cache_data.get("entidades", [])
        print(f"Cache atual tem {len(entidades)} entidades")
        
        if len(entidades) > 0:
            print("Cache já tem dados, não é necessário criar dados de teste")
            return
    
    print("Cache vazio ou inexistente. Criando dados de teste...")
    
    # Criar dados de teste realistas
    test_data = {
        "entidades": [
            {
                "name": "API-Pagamentos",
                "domain": "APM",
                "guid": "test-guid-1",
                "entityType": "APPLICATION",
                "reporting": True,
                "metricas": {
                    "30min": {
                        "apdex": 0.85,
                        "response_time_max": 245.5,
                        "error_rate": 2.1,
                        "throughput": 1250.0,
                        "recent_error": "Connection timeout"
                    },
                    "3h": {
                        "apdex": 0.88,
                        "response_time_max": 220.3,
                        "error_rate": 1.8,
                        "throughput": 1180.0
                    },
                    "24h": {
                        "apdex": 0.90,
                        "response_time_max": 180.2,
                        "error_rate": 1.5,
                        "throughput": 1100.0
                    }
                }
            },
            {
                "name": "API-Autenticacao",
                "domain": "APM",
                "guid": "test-guid-2",
                "entityType": "APPLICATION",
                "reporting": True,
                "metricas": {
                    "30min": {
                        "apdex": 0.92,
                        "response_time_max": 125.8,
                        "error_rate": 0.8,
                        "throughput": 2500.0
                    },
                    "3h": {
                        "apdex": 0.91,
                        "response_time_max": 135.2,
                        "error_rate": 1.0,
                        "throughput": 2300.0
                    },
                    "24h": {
                        "apdex": 0.89,
                        "response_time_max": 150.1,
                        "error_rate": 1.2,
                        "throughput": 2200.0
                    }
                }
            },
            {
                "name": "Database-Principal",
                "domain": "INFRA",
                "guid": "test-guid-3",
                "entityType": "DATABASE",
                "reporting": True,
                "metricas": {
                    "30min": {
                        "apdex": 0.78,
                        "response_time_max": 450.2,
                        "error_rate": 0.5,
                        "throughput": 800.0
                    },
                    "3h": {
                        "apdex": 0.80,
                        "response_time_max": 420.1,
                        "error_rate": 0.4,
                        "throughput": 750.0
                    },
                    "24h": {
                        "apdex": 0.82,
                        "response_time_max": 380.5,
                        "error_rate": 0.3,
                        "throughput": 700.0
                    }
                }
            }
        ],
        "timestamp": datetime.now().isoformat(),
        "total_entidades": 3,
        "contagem_por_dominio": {
            "APM": 2,
            "INFRA": 1
        },
        "timestamp_atualizacao": datetime.now().isoformat(),
        "tipo_coleta": "dados_teste_desenvolvimento"
    }
    
    # Garante que o diretório existe
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Salva os dados de teste
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Dados de teste criados em: {cache_file}")
    print(f"Total de entidades: {test_data['total_entidades']}")
    print(f"Distribuição: {test_data['contagem_por_dominio']}")
    print("\n⚠️  IMPORTANTE: Estes são dados de TESTE!")
    print("Para usar dados reais, configure as credenciais do New Relic e execute a coleta real.")

if __name__ == "__main__":
    create_test_cache()
