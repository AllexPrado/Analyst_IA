#!/usr/bin/env python3
"""
Teste rápido para verificar se o fix do OpenAI connector está funcionando
"""
import asyncio
import sys
import os

# Adiciona o backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.utils.openai_connector import gerar_resposta_ia

async def test_small_prompt():
    """Testa com prompt pequeno"""
    try:
        resposta = await gerar_resposta_ia(
            'Teste simples de 5 palavras', 
            'Você é um assistente.', 
            modelo='gpt-4'
        )
        print('✅ Teste prompt pequeno OK')
        print(f'Resposta: {resposta[:100]}...')
        return True
    except Exception as e:
        print(f'❌ Erro prompt pequeno: {e}')
        return False

async def test_large_prompt():
    """Testa com prompt grande para verificar corte"""
    try:
        # Cria um prompt grande
        prompt_grande = "Esta é uma pergunta muito longa. " * 1000  # ~5000 palavras
        resposta = await gerar_resposta_ia(
            prompt_grande, 
            'Você é um assistente.', 
            modelo='gpt-4'
        )
        print('✅ Teste prompt grande OK - corte funcionando')
        print(f'Resposta: {resposta[:100]}...')
        return True
    except Exception as e:
        print(f'❌ Erro prompt grande: {e}')
        return False

async def main():
    print("=== Testando OpenAI Connector Fix ===")
    
    # Verifica se tem as variáveis de ambiente
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY não encontrada")
        return
    
    # Teste 1: Prompt pequeno
    print("\n1. Testando prompt pequeno...")
    await test_small_prompt()
    
    # Teste 2: Prompt grande
    print("\n2. Testando prompt grande (verificar corte)...")
    await test_large_prompt()
    
    print("\n=== Testes concluídos ===")

if __name__ == "__main__":
    asyncio.run(main())
