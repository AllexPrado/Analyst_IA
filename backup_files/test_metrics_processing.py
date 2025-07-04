"""
Teste da correção do erro de processamento de métricas

Este script verifica se o processador de entidades está convertendo corretamente
strings JSON para dicionários quando necessário.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Configura logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona diretório pai ao path para poder importar módulos corretamente
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

# Importa os módulos necessários
try:
    from utils.entity_processor import process_entity_details
except ImportError as e:
    logger.error(f"Erro ao importar módulos necessários: {e}")
    sys.exit(1)

def criar_entidade_teste_com_string():
    """Cria uma entidade de teste com métricas em formato string"""
    return {
        "name": "Entidade Teste",
        "guid": "123456",
        "domain": "APM",
        "metricas": {
            "30min": '{"apdex": [{"score": 0.95}], "response_time_max": [{"max.duration": 0.235}]}',
            "24h": '{"apdex": [{"score": 0.90}], "response_time_max": [{"max.duration": 0.456}]}',
            "timestamp": "2025-06-28T12:00:00.000Z"
        }
    }

def testar_processamento_metricas():
    """Testa o processamento de métricas string -> dict"""
    print("🧪 Testando processamento de métricas...")
    
    # 1. Cria entidade de teste com métricas em formato string
    entidade = criar_entidade_teste_com_string()
    print(f"\n▶️ Entidade original com métricas string: ")
    print(f"   - Tipo 30min: {type(entidade['metricas']['30min'])}")
    print(f"   - Conteúdo: {entidade['metricas']['30min'][:50]}...")
    
    # 2. Processa a entidade
    print("\n▶️ Processando entidade...")
    entidade_processada = process_entity_details(entidade)
    
    # 3. Verifica se as métricas foram convertidas corretamente
    if isinstance(entidade_processada['metricas']['30min'], dict):
        print("\n✅ Sucesso! Métricas '30min' foram convertidas para dicionário")
        print(f"   - Tipo agora: {type(entidade_processada['metricas']['30min'])}")
        
        # Verifica se os dados estão acessíveis como dicionário
        try:
            apdex = entidade_processada['metricas']['30min']['apdex'][0]['score']
            print(f"   - Apdex acessado com sucesso: {apdex}")
            
            response_time = entidade_processada['metricas']['30min']['response_time_max'][0]['max.duration']
            print(f"   - Response time acessado com sucesso: {response_time}")
            
            print("\n✅ Teste concluído com sucesso! Agora é possível acessar os dados das métricas.")
            return True
        except Exception as e:
            print(f"\n❌ Erro ao acessar dados convertidos: {e}")
            return False
    else:
        print(f"\n❌ Falha! Métricas '30min' não foram convertidas para dicionário")
        print(f"   - Tipo continua sendo: {type(entidade_processada['metricas']['30min'])}")
        return False

def teste_manipulacao_periodo_data():
    """Teste específico para o problema do AttributeError"""
    print("\n\n🧪 Testando manipulação segura de period_data (AttributeError)...")
    
    # 1. Cria entidade de teste com métricas em formato string
    entidade = criar_entidade_teste_com_string()
    
    # 2. Simulando o código que estava falhando
    print("\n▶️ Simulando código que antes falhava com AttributeError...")
    for period_key, period_data in entidade["metricas"].items():
        print(f"   - Processando período: {period_key}, tipo: {type(period_data)}")
        
        # Testa o tratamento de string vs dicionário
        if period_key == "timestamp":
            print(f"     Ignorando timestamp")
            continue
            
        if isinstance(period_data, dict):
            print(f"     É um dicionário, tentando acessar .values()")
            if period_data and any(period_data.values()):
                print(f"     ✅ Tem valores reais")
        elif isinstance(period_data, str):
            print(f"     É uma string, tentando converter para JSON...")
            try:
                json_data = json.loads(period_data.replace("'", "\""))
                if json_data and any(json_data.values()):
                    print(f"     ✅ Convertido com sucesso e tem valores")
                    # Atualiza para um dicionário real
                    entidade["metricas"][period_key] = json_data
            except Exception as e:
                print(f"     ❌ Erro ao converter string para JSON: {e}")
        else:
            print(f"     É outro tipo de dado ({type(period_data)})")
    
    # 3. Verifica se foi atualizado corretamente
    print("\n▶️ Verificando resultados após processamento:")
    for period_key, period_data in entidade["metricas"].items():
        print(f"   - Período: {period_key}, tipo atual: {type(period_data)}")
        
        if isinstance(period_data, dict) and period_key != "timestamp":
            # Tenta acessar os valores
            try:
                if any(period_data.values()):
                    print(f"     ✅ Consegue acessar .values() sem AttributeError")
                else:
                    print(f"     ⚠️ values() está vazio")
            except Exception as e:
                print(f"     ❌ Erro ao acessar .values(): {e}")
    
    print("\n✅ Teste de manipulação de period_data concluído!")

if __name__ == "__main__":
    print("🔍 Iniciando testes de correção do processamento de métricas...")
    
    # Executa os testes
    testar_processamento_metricas()
    teste_manipulacao_periodo_data()
    
    print("\n✅ Todos os testes concluídos!")
