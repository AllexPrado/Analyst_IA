import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path

async def testar_api_incidentes():
    """Testa a API de incidentes para verificar se está funcionando corretamente"""
    print("=== TESTANDO API DE INCIDENTES ===")
    
    async with aiohttp.ClientSession() as session:
        # 1. Verificar endpoint /status-cache
        print("\n1. Testando endpoint /status-cache...")
        try:
            async with session.get("http://localhost:8002/status-cache") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"Status do cache: {result.get('status')}")
                    print(f"Total de entidades: {result.get('total_entidades_consolidadas')}")
                    print(f"Total de alertas: {result.get('total_alertas')}")
                    print(f"Total de incidentes: {result.get('total_incidentes')}")
                    print(f"Chaves disponíveis: {', '.join(result.get('chaves_disponiveis', []))}")
                else:
                    print(f"Erro: {response.status} - {await response.text()}")
        except Exception as e:
            print(f"Erro ao testar /status-cache: {e}")
        
        # 2. Verificar endpoint /incidentes
        print("\n2. Testando endpoint /incidentes...")
        try:
            async with session.get("http://localhost:8002/incidentes") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"Total de incidentes: {len(result.get('incidentes', []))}")
                    print(f"Total de alertas: {len(result.get('alertas', []))}")
                    
                    # Mostrar resumo
                    if "resumo" in result:
                        resumo = result["resumo"]
                        print("\nResumo:")
                        for key, value in resumo.items():
                            print(f"- {key}: {value}")
                    
                    # Salvar resultado para análise
                    output_path = "historico/teste_incidentes_resposta.json"
                    Path("historico").mkdir(exist_ok=True)
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    print(f"\nResposta completa salva em: {output_path}")
                else:
                    print(f"Erro: {response.status} - {await response.text()}")
        except Exception as e:
            print(f"Erro ao testar /incidentes: {e}")
        
        # 3. Testar adicionar dados de exemplo (opcional)
        adicionar_dados = input("\nDeseja adicionar novos dados de exemplo? (s/n): ").lower() == 's'
        if adicionar_dados:
            print("\n3. Adicionando novos dados de exemplo...")
            try:
                async with session.post("http://localhost:8002/adicionar-dados-exemplo") as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"Status: {result.get('status')}")
                        print(f"Mensagem: {result.get('message')}")
                        print(f"Alertas adicionados: {result.get('alertas_adicionados')}")
                        print(f"Incidentes adicionados: {result.get('incidentes_adicionados')}")
                    else:
                        print(f"Erro: {response.status} - {await response.text()}")
            except Exception as e:
                print(f"Erro ao adicionar dados de exemplo: {e}")
        
        print("\n=== TESTE CONCLUÍDO ===")
        print("Se todos os testes passaram, a API de incidentes está funcionando corretamente!")
        print("O frontend agora deve ser capaz de apresentar os dados de incidentes.")

if __name__ == "__main__":
    asyncio.run(testar_api_incidentes())
