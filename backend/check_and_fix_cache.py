#!/usr/bin/env python3
"""
Script para verificar o estado do cache e criar dados de teste se necessário
"""

import json
import os
from datetime import datetime
from pathlib import Path

def check_and_fix_cache():
    """Verifica e corrige o cache se necessário"""
    
    # Diretório de cache
    cache_dir = Path("historico")
    cache_file = cache_dir / "cache_completo.json"
    
    print("=== VERIFICAÇÃO DE CACHE ===")
    
    # Verifica se o diretório existe
    if not cache_dir.exists():
        print(f"Diretório de cache não encontrado: {cache_dir}")
        os.makedirs(cache_dir, exist_ok=True)
        print(f"Diretório criado: {cache_dir}")
    else:
        print(f"Diretório de cache encontrado: {cache_dir}")
    
    # Verifica se o arquivo de cache existe
    cache_exists = cache_file.exists()
    print(f"Arquivo de cache existe: {'Sim' if cache_exists else 'Não'}")
    
    data = {}
    entities_count = 0
    
    # Tenta ler o cache se existir
    if cache_exists:
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"Cache lido com sucesso: {cache_file}")
            entities = data.get("entidades", [])
            entities_count = len(entities)
            print(f"Total de entidades: {entities_count}")
            
            # Verifica se temos dados suficientes
            if entities_count > 0:
                print("✅ Cache contém entidades, não é necessário criar dados de teste")
                
                # Garantir que os arquivos de dados também existam
                try:
                    from generate_unified_data import generate_unified_data
                    print("Verificando arquivos de dados unificados...")
                    generate_unified_data()
                    print("✅ Arquivos de dados unificados verificados/gerados com sucesso")
                except Exception as e:
                    print(f"❌ Erro ao gerar arquivos de dados unificados: {e}")
                if not Path("dados/entidades.json").exists() or not Path("dados/kpis.json").exists():
                    print("⚠️ Arquivos de dados podem estar faltando. Tentando gerar dados unificados...")
                    generate_unified_data()
                
                # Mostra informações sobre as entidades
                domains = {}
                for entity in entities:
                    domain = entity.get("domain", "UNKNOWN")
                    domains[domain] = domains.get(domain, 0) + 1
                
                print(f"Distribuição por domínio: {domains}")
                return True
            else:
                print("⚠️ Cache existe, mas não contém entidades")
                # Tentar primeiro gerar dados unificados
                try:
                    from generate_unified_data import generate_unified_data
                    print("Gerando dados unificados...")
                    if generate_unified_data():
                        print("✅ Dados unificados gerados com sucesso")
                        return True
                    else:
                        print("⚠️ Falha ao gerar dados unificados, usando fallback para dados de teste simples")
                except Exception as e:
                    print(f"❌ Erro ao gerar dados unificados: {e}")
                    print("Usando fallback para dados de teste simples")
        except Exception as e:
            print(f"❌ Erro ao ler o arquivo de cache: {e}")
            print("Tentando gerar dados unificados...")
            # Tentar primeiro gerar dados unificados
            try:
                from generate_unified_data import generate_unified_data
                print("Gerando dados unificados...")
                if generate_unified_data():
                    print("✅ Dados unificados gerados com sucesso")
                    return True
                else:
                    print("⚠️ Falha ao gerar dados unificados, usando fallback para dados de teste simples")
            except Exception as e:
                print(f"❌ Erro ao gerar dados unificados: {e}")
                print("Usando fallback para dados de teste simples")
    
    # Se chegamos aqui, precisamos criar dados de teste
    print("\n=== CRIANDO DADOS DE TESTE SIMPLES ===")
    
    # Dados de teste
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
                        "response_time": 245.5,
                        "response_time_max": 245.5,
                        "error_rate": 2.1,
                        "throughput": 1250.0,
                        "recent_error": "Connection timeout"
                    },
                    "3h": {
                        "apdex": 0.88,
                        "response_time": 220.3,
                        "response_time_max": 220.3,
                        "error_rate": 1.8,
                        "throughput": 1180.0
                    },
                    "24h": {
                        "apdex": 0.90,
                        "response_time": 180.2,
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
                        "response_time": 125.8,
                        "response_time_max": 125.8,
                        "error_rate": 0.8,
                        "throughput": 2500.0
                    },
                    "3h": {
                        "apdex": 0.91,
                        "response_time": 135.2,
                        "response_time_max": 135.2,
                        "error_rate": 1.0,
                        "throughput": 2300.0
                    },
                    "24h": {
                        "apdex": 0.89,
                        "response_time": 150.1,
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
                        "response_time": 450.2,
                        "response_time_max": 450.2,
                        "error_rate": 0.5,
                        "throughput": 800.0
                    },
                    "3h": {
                        "apdex": 0.80,
                        "response_time": 420.1,
                        "response_time_max": 420.1,
                        "error_rate": 0.4,
                        "throughput": 750.0
                    },
                    "24h": {
                        "apdex": 0.82,
                        "response_time": 380.5,
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
        "timestamp_atualizacao": datetime.now().isoformat()
    }
    
    # Salva os dados de teste
    try:
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Dados de teste criados em: {cache_file}")
        print(f"Total de entidades: {test_data['total_entidades']}")
        print(f"Distribuição por domínio: {test_data['contagem_por_dominio']}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar dados de teste: {e}")
        return False

def import_module_from_path(module_name, file_path):
    """Importa um módulo a partir de um caminho de arquivo"""
    import importlib.util
    
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        print(f"❌ Falha ao importar {module_name} de {file_path}")
        return None
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def generate_unified_data():
    """Gera dados de teste unificados usando o script dedicado"""
    print("\n=== GERANDO DADOS UNIFICADOS ===")
    
    unified_data_path = Path("generate_unified_data.py")
    if unified_data_path.exists():
        try:
            # Importar e executar o módulo
            module = import_module_from_path("generate_unified_data", str(unified_data_path))
            if module and hasattr(module, "generate_unified_data"):
                print("Iniciando geração de dados unificados...")
                result = module.generate_unified_data()
                if result:
                    print("✅ Dados unificados gerados com sucesso")
                    return True
                else:
                    print("❌ Falha na geração de dados unificados")
            else:
                print("❌ Módulo generate_unified_data não contém a função necessária")
        except Exception as e:
            print(f"❌ Erro ao executar generate_unified_data: {e}")
            import traceback
            print(traceback.format_exc())
    else:
        print(f"❓ Arquivo {unified_data_path} não encontrado")
    
    return False

if __name__ == "__main__":
    if check_and_fix_cache():
        generate_unified_data()
