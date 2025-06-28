import asyncio
import json
import requests
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"  # Ajuste conforme necessário

def test_endpoint(endpoint: str, method: str = "GET", payload: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Testa um endpoint específico e valida se os dados retornados são reais
    """
    url = f"{BASE_URL}{endpoint}"
    logger.info(f"Testando endpoint: {url} [Método: {method}]")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=payload, timeout=30)
        else:
            logger.error(f"Método {method} não suportado")
            return {"success": False, "error": f"Método {method} não suportado"}
            
        response.raise_for_status()
        data = response.json()
        
        # Verifica se o retorno é um objeto JSON válido e não vazio
        if not data:
            return {
                "success": False, 
                "endpoint": endpoint, 
                "error": "Resposta vazia"
            }
            
        return {
            "success": True,
            "endpoint": endpoint,
            "data": data,
            "status_code": response.status_code
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição: {e}")
        return {
            "success": False,
            "endpoint": endpoint,
            "error": str(e)
        }
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        return {
            "success": False,
            "endpoint": endpoint,
            "error": f"Resposta não é um JSON válido: {e}"
        }

def validate_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verifica se a resposta contém dados reais ou apenas placeholders
    """
    if not response["success"]:
        return response
        
    data = response["data"]
    validation = {"real_data": True, "placeholder_indicators": []}
    
    # Verifica se existem indicadores de dados placeholder
    placeholder_keywords = ["placeholder", "dummy", "example", "mock", "sample"]
    json_str = json.dumps(str(data).lower())
    
    for keyword in placeholder_keywords:
        if keyword in json_str:
            validation["placeholder_indicators"].append(keyword)
            validation["real_data"] = False
    
    # Verifica ausência de dados reais em listas
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list) and len(value) == 0:
                validation["placeholder_indicators"].append(f"Lista vazia em {key}")
    
    response["validation"] = validation
    return response

def test_chat_endpoint(pergunta: str) -> Dict[str, Any]:
    """
    Testa o endpoint de chat com uma pergunta específica
    """
    payload = {"pergunta": pergunta}
    response = test_endpoint("/chat", "POST", payload)
    
    if response["success"]:
        # Adiciona validação específica para respostas de chat
        resp_text = response["data"].get("resposta", "")
        
        # Verifica se a resposta parece genérica
        generic_indicators = [
            "Não tenho dados suficientes",
            "Não possuo informações",
            "Não tenho acesso a",
            "Preciso de mais detalhes",
            "Não tenho contexto",
            "Não posso fornecer dados específicos"
        ]
        
        is_generic = any(indicator.lower() in resp_text.lower() for indicator in generic_indicators)
        
        response["validation"] = {
            "generic_response": is_generic,
            "response_length": len(resp_text),
            "has_metrics": any(word in resp_text.lower() for word in ["métrica", "valor", "percentual", "número"])
        }
    
    return response

def main():
    """
    Função principal que testa todos os endpoints críticos
    """
    logger.info("Iniciando testes de endpoints")
    
    results = {}
    
    # 1. Teste do endpoint de status
    results["status"] = validate_response(test_endpoint("/api/status"))
    
    # 2. Teste do endpoint de entidades
    results["entidades"] = validate_response(test_endpoint("/api/entidades"))
    
    # 3. Teste do endpoint de métricas
    results["metricas"] = validate_response(test_endpoint("/metrics"))
    
    # 4. Teste do endpoint de cobertura
    results["cobertura"] = validate_response(test_endpoint("/api/cobertura"))
    
    # 5. Teste do endpoint de diagnóstico de cache
    results["cache_diagnostico"] = validate_response(test_endpoint("/api/cache/diagnostico"))
    
    # 6. Teste do endpoint de chat com diferentes tipos de perguntas
    perguntas = [
        "Qual o status geral do sistema?",
        "Quais são as métricas de performance atuais?",
        "Houve algum erro nas últimas 24 horas?",
        "Como está o uso de CPU dos servidores?",
        "Qual a disponibilidade atual do sistema?"
    ]
    
    results["chat"] = []
    for pergunta in perguntas:
        logger.info(f"Testando pergunta: {pergunta}")
        chat_result = test_chat_endpoint(pergunta)
        results["chat"].append({
            "pergunta": pergunta,
            "resultado": chat_result
        })
    
    # Gera relatório de resultados
    with open("resultado_teste_endpoints.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Exibe um resumo
    print("\n===== RESUMO DOS TESTES =====")
    for endpoint, result in results.items():
        if endpoint != "chat":
            success = result.get("success", False)
            validation = result.get("validation", {})
            real_data = validation.get("real_data", False) if success else False
            
            status = "✅ OK" if success and real_data else "❌ FALHA"
            print(f"{endpoint}: {status}")
            
            if not real_data and success:
                print(f"  - Indicadores de placeholder: {validation.get('placeholder_indicators', [])}")
    
    print("\n===== RESUMO DO CHAT =====")
    generic_count = sum(1 for item in results["chat"] if item["resultado"].get("validation", {}).get("generic_response", True))
    print(f"Respostas genéricas: {generic_count}/{len(results['chat'])}")
    
    print("\nRespostas detalhadas salvas em resultado_teste_endpoints.json")

if __name__ == "__main__":
    main()
