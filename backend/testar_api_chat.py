import asyncio
import os
import sys
import json
from datetime import datetime
import aiohttp

async def testar_api_chat():
    """Testa a API de chat com uma pergunta sobre incidentes da última semana"""
    try:
        print("Testando API de chat com pergunta sobre incidentes...")
        
        async with aiohttp.ClientSession() as session:
            # URL da API de chat (porta padrão do backend é 5000, não 8000)
            url = "http://localhost:5000/api/chat"
            
            # Pergunta sobre incidentes da última semana
            payload = {
                "pergunta": "Resumir os incidentes da última semana"
            }
            
            # Fazer a requisição
            print(f"Enviando requisição para {url}...")
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    # Obter resposta
                    result = await response.json()
                    
                    print("\n==== RESPOSTA DO CHAT ====")
                    print(f"Status: {response.status}")
                    
                    # Exibir a resposta
                    if "resposta" in result:
                        print("\nResposta:")
                        print(result["resposta"][:500] + "..." if len(result["resposta"]) > 500 else result["resposta"])
                    
                    # Exibir informações do contexto
                    if "contexto" in result and result["contexto"]:
                        print("\nContexto:")
                        for key, value in result["contexto"].items():
                            if isinstance(value, str) and len(value) > 100:
                                value = value[:100] + "..."
                            print(f"- {key}: {value}")
                    
                    # Salvar resposta completa para análise
                    output_path = "historico/teste_chat_resposta.json"
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    print(f"\nResposta completa salva em: {output_path}")
                    
                else:
                    print(f"Erro: {response.status}")
                    print(await response.text())
            
    except Exception as e:
        print(f"Erro ao testar API: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(testar_api_chat())
