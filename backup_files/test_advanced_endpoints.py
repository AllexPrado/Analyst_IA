import requests
import json
import os
import sys
from datetime import datetime

# Adicionar o diretório pai ao caminho para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuração
BASE_URL = "http://localhost:8000/api"  # URL base da API
ENDPOINTS = [
    "/avancado/kubernetes",
    "/avancado/infraestrutura",
    "/avancado/topologia"
]

def test_endpoint(url):
    """Testa um endpoint específico"""
    print(f"Testando {url}...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Verificar se a resposta é um JSON válido
        data = response.json()
        
        print(f"✅ {url}: OK (status {response.status_code})")
        return True, data
    except requests.exceptions.RequestException as e:
        print(f"❌ {url}: ERRO - {e}")
        return False, None
    except json.JSONDecodeError:
        print(f"❌ {url}: ERRO - Resposta não é um JSON válido")
        return False, None

def validate_kubernetes_data(data):
    """Valida os dados de Kubernetes"""
    if not data.get("clusters"):
        print("❌ Dados de Kubernetes inválidos: clusters não encontrados")
        return False
        
    if not data.get("nodes"):
        print("❌ Dados de Kubernetes inválidos: nodes não encontrados")
        return False
        
    if not data.get("summary"):
        print("❌ Dados de Kubernetes inválidos: summary não encontrado")
        return False
        
    print("✅ Dados de Kubernetes válidos")
    return True

def validate_infrastructure_data(data):
    """Valida os dados de Infraestrutura"""
    if not data.get("servers"):
        print("❌ Dados de Infraestrutura inválidos: servers não encontrados")
        return False
        
    if not data.get("summary"):
        print("❌ Dados de Infraestrutura inválidos: summary não encontrado")
        return False
        
    print("✅ Dados de Infraestrutura válidos")
    return True

def validate_topology_data(data):
    """Valida os dados de Topologia"""
    if not data.get("nodes"):
        print("❌ Dados de Topologia inválidos: nodes não encontrados")
        return False
        
    if not data.get("links"):
        print("❌ Dados de Topologia inválidos: links não encontrados")
        return False
        
    if not data.get("summary"):
        print("❌ Dados de Topologia inválidos: summary não encontrado")
        return False
        
    print("✅ Dados de Topologia válidos")
    return True

def save_test_results(results):
    """Salva os resultados do teste em um arquivo JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_advanced_endpoints_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\nResultados salvos em {filename}")

def main():
    """Função principal"""
    print("=== TESTE DOS ENDPOINTS AVANÇADOS ===")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=====================================\n")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "endpoints": {}
    }
    
    all_tests_passed = True
    
    for endpoint in ENDPOINTS:
        url = f"{BASE_URL}{endpoint}"
        success, data = test_endpoint(url)
        
        results["endpoints"][endpoint] = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "sample_data": data if success else None
        }
        
        if success:
            # Validar os dados específicos de cada endpoint
            if endpoint == "/avancado/kubernetes":
                validation_result = validate_kubernetes_data(data)
            elif endpoint == "/avancado/infraestrutura":
                validation_result = validate_infrastructure_data(data)
            elif endpoint == "/avancado/topologia":
                validation_result = validate_topology_data(data)
            else:
                validation_result = True
                
            results["endpoints"][endpoint]["validation"] = validation_result
            all_tests_passed = all_tests_passed and validation_result
        else:
            all_tests_passed = False
            
        print("")  # Linha em branco para separar os resultados
    
    # Resultado final
    print("\n=====================================")
    if all_tests_passed:
        print("✅ TODOS OS TESTES PASSARAM!")
        results["overall_result"] = "success"
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        results["overall_result"] = "failure"
    print("=====================================")
    
    # Salvar os resultados
    save_test_results(results)

if __name__ == "__main__":
    main()
