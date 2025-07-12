"""
Teste rápido para verificar se os endpoints /agno estão funcionando corretamente.
Este script verifica os endpoints do Agno IA e mostra os resultados.
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configuração
BASE_URL = "http://localhost:8000"
ENDPOINTS = [
    "/agno/corrigir",
    "/agno/playbook",
    "/agno/feedback",
    "/agno/coletar_newrelic",
    "/api/agno/corrigir",
    "/api/agno/playbook",
    "/api/agno/feedback",
    "/api/agno/coletar_newrelic"
]

# Payloads para teste
PAYLOADS = {
    "/agno/corrigir": {"entidade": "sistema_teste", "acao": "verificar"},
    "/agno/playbook": {"nome": "diagnostico", "contexto": {}},
    "/agno/feedback": {"feedback": {"tipo": "teste", "valor": "ok"}},
    "/agno/coletar_newrelic": {"entidade": "sistema", "periodo": "3d", "tipo": "metricas"},
    "/api/agno/corrigir": {"entidade": "sistema_teste", "acao": "verificar"},
    "/api/agno/playbook": {"nome": "diagnostico", "contexto": {}},
    "/api/agno/feedback": {"feedback": {"tipo": "teste", "valor": "ok"}},
    "/api/agno/coletar_newrelic": {"entidade": "sistema", "periodo": "3d", "tipo": "metricas"}
}

async def testar_endpoint(client: httpx.AsyncClient, endpoint: str) -> dict:
    """Testa um endpoint específico e retorna o resultado."""
    url = f"{BASE_URL}{endpoint}"
    payload = PAYLOADS.get(endpoint, {})
    
    print(f"\nTestando endpoint: {url}")
    print(f"Payload: {payload}")
    
    try:
        response = await client.post(url, json=payload, timeout=10.0)
        
        resultado = {
            "endpoint": endpoint,
            "url": url,
            "status_code": response.status_code,
            "sucesso": 200 <= response.status_code < 300
        }
        
        if resultado["sucesso"]:        print(f"[SUCESSO] Status: {response.status_code}")
        try:
            resultado["resposta"] = response.json()
            print(f"Resposta: {json.dumps(resultado['resposta'], indent=2, ensure_ascii=False)}")
        except:
            resultado["resposta"] = response.text
            print(f"Resposta (texto): {response.text[:100]}...")
    else:
        print(f"[FALHA] Status: {response.status_code}")
            resultado["erro"] = response.text
            print(f"Erro: {response.text}")
        
        return resultado
    except Exception as e:
        print(f"[ERRO] Erro na requisição: {type(e).__name__}: {str(e)}")
        return {
            "endpoint": endpoint,
            "url": url,
            "sucesso": False,
            "erro": f"{type(e).__name__}: {str(e)}"
        }

async def main():
    """Função principal para executar os testes de endpoints."""
    print("=" * 60)
    print("TESTE DE ENDPOINTS AGNO IA")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    resultados = []
    
    async with httpx.AsyncClient() as client:
        for endpoint in ENDPOINTS:
            resultado = await testar_endpoint(client, endpoint)
            resultados.append(resultado)
    
    # Resumo dos resultados
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    endpoints_ok = [r for r in resultados if r["sucesso"]]
    endpoints_falha = [r for r in resultados if not r["sucesso"]]
    
    print(f"[OK] Endpoints funcionando: {len(endpoints_ok)} de {len(ENDPOINTS)}")
    print(f"[FALHA] Endpoints com falha: {len(endpoints_falha)}")
    
    if endpoints_falha:
        print("\nEndpoints com falha:")
        for r in endpoints_falha:
            print(f"- {r['endpoint']} ({r.get('status_code', 'N/A')})")
    
    # Verificando se temos pelo menos um endpoint funcionando de cada tipo
    tipos_endpoints = set([ep.split("/")[-1] for ep in [r["endpoint"] for r in endpoints_ok]])
    print(f"\nTipos de endpoints funcionando: {', '.join(tipos_endpoints)}")
    
    if len(tipos_endpoints) >= 4:
        print("\nRESULTADO: Todos os tipos de endpoints estão funcionando!")
    else:
        print("\nRESULTADO: Nem todos os tipos de endpoints estão funcionando!")
    
    # Salvar resultados em arquivo para análise posterior
    with open("resultado_teste_agno_endpoints.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print("\nDetalhes salvos em 'resultado_teste_agno_endpoints.json'")

if __name__ == "__main__":
    asyncio.run(main())
