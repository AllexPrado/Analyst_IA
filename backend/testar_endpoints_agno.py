"""
Script para testar endpoints do Agno IA através dos diferentes caminhos.
Verifica se os endpoints estão acessíveis tanto via /agno/ quanto via /api/agno/
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any, List

# Configuração
BASE_URL = "http://localhost:8000"  # Ajuste se necessário
ENDPOINTS = [
    "/agno/corrigir",
    "/agno/playbook",
    "/agno/feedback",
    "/agno/coletar_newrelic",
    "/api/agno/corrigir",
    "/api/agno/playbook",
    "/api/agno/feedback",
    "/api/agno/coletar_newrelic",
]

# Dados de teste para os endpoints
TEST_DATA = {
    "/agno/corrigir": {"entidade": "test_entity", "acao": "corrigir"},
    "/agno/playbook": {"nome": "test_playbook", "contexto": {}},
    "/agno/feedback": {"feedback": {"rating": 5, "comments": "Test feedback"}},
    "/agno/coletar_newrelic": {"entidade": "test_entity", "periodo": "3d", "tipo": "metricas"},
    "/api/agno/corrigir": {"entidade": "test_entity", "acao": "corrigir"},
    "/api/agno/playbook": {"nome": "test_playbook", "contexto": {}},
    "/api/agno/feedback": {"feedback": {"rating": 5, "comments": "Test feedback"}},
    "/api/agno/coletar_newrelic": {"entidade": "test_entity", "periodo": "3d", "tipo": "metricas"},
}

async def test_endpoint(client: httpx.AsyncClient, endpoint: str) -> Dict[str, Any]:
    """Testa um endpoint específico."""
    url = f"{BASE_URL}{endpoint}"
    print(f"Testando {url}...")
    
    try:
        # Todos os endpoints de teste são POST
        response = await client.post(url, json=TEST_DATA.get(endpoint, {}))
        
        result = {
            "endpoint": endpoint,
            "status_code": response.status_code,
            "success": 200 <= response.status_code < 300,
        }
        
        # Se for bem-sucedido, adicionar dados da resposta
        if result["success"]:
            try:
                result["data"] = response.json()
            except json.JSONDecodeError:
                result["data"] = response.text
        else:
            result["error"] = response.text
            
        return result
    except Exception as e:
        return {
            "endpoint": endpoint,
            "status_code": None,
            "success": False,
            "error": str(e)
        }

async def run_tests():
    """Executa os testes em todos os endpoints."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [test_endpoint(client, endpoint) for endpoint in ENDPOINTS]
        results = await asyncio.gather(*tasks)
        
    # Formatar e exibir resultados
    print("\n===== RESULTADOS DOS TESTES =====")
    
    success_count = 0
    failed_endpoints = []
    
    for result in results:
        status = "✅ SUCESSO" if result["success"] else "❌ FALHA"
        print(f"{status} - {result['endpoint']} (Status: {result['status_code']})")
        
        if result["success"]:
            success_count += 1
        else:
            failed_endpoints.append(result["endpoint"])
            print(f"  Erro: {result.get('error', 'Desconhecido')}")
            
    print("\n===== RESUMO =====")
    print(f"Total de endpoints testados: {len(ENDPOINTS)}")
    print(f"Bem-sucedidos: {success_count}")
    print(f"Falhas: {len(ENDPOINTS) - success_count}")
    
    if failed_endpoints:
        print("\nEndpoints com falha:")
        for endpoint in failed_endpoints:
            print(f"- {endpoint}")
            
    # Salvar resultados em um arquivo JSON
    with open("resultado_teste_endpoints.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nResultados detalhados salvos em 'resultado_teste_endpoints.json'")
    
    return success_count == len(ENDPOINTS)

if __name__ == "__main__":
    print("Iniciando testes de endpoints Agno IA...\n")
    success = asyncio.run(run_tests())
    
    if not success:
        print("\n⚠️ Alguns testes falharam. Verifique o relatório para mais detalhes.")
        sys.exit(1)
    else:
        print("\n✅ Todos os testes foram bem-sucedidos!")
        sys.exit(0)
