#!/usr/bin/env python3
"""
Teste do endpoint de chat
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_chat_api():
    """Testa o endpoint de chat com perguntas simuladas"""
    
    # URL do endpoint
    url = "http://localhost:8000/chat"
    
    # Perguntas para teste
    perguntas = [
        "Quantas entidades estão sendo monitoradas?",
        "Como está a performance do sistema?",
        "Quais são as métricas principais do sistema?",
        "Temos algum erro recente?"
    ]
    
    print("=== TESTE DO ENDPOINT DE CHAT ===")
    print(f"URL: {url}")
    
    async with aiohttp.ClientSession() as session:
        for i, pergunta in enumerate(perguntas):
            print(f"\nPergunta {i+1}: {pergunta}")
            try:
                async with session.post(url, json={"pergunta": pergunta}) as response:
                    status = response.status
                    print(f"Status: {status}")
                    
                    if status == 200:
                        data = await response.json()
                        print(f"Resposta: {data['resposta']}")
                    else:
                        texto = await response.text()
                        print(f"Erro: {texto}")
            except Exception as e:
                print(f"Erro na requisição: {e}")
    
    print("\nTeste concluído!")

if __name__ == "__main__":
    asyncio.run(test_chat_api())
