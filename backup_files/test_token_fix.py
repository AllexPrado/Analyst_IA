#!/usr/bin/env python3
"""
Teste específico para validar o corte de tokens no openai_connector.py
"""

import sys
import os
import asyncio
import logging

# Adiciona o path do backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.utils.openai_connector import gerar_resposta_ia

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_token_cutting():
    """Testa o corte de tokens com um prompt muito grande"""
    
    # Cria um prompt muito grande (similar ao que está sendo enviado)
    system_prompt = "Você é um assistente de análise de métricas APM."
    
    # Gera um prompt enorme para forçar o corte
    base_text = "Esta é uma análise detalhada do New Relic com muitas entidades e métricas. "
    large_prompt = base_text * 2000  # Vai dar mais de 20k tokens
    
    print(f"Testando com prompt de ~{len(large_prompt)} caracteres")
    
    try:
        # Tenta GPT-4 (limite 8192)
        print("\n=== Testando GPT-4 ===")
        response = await gerar_resposta_ia(
            prompt=large_prompt,
            system_prompt=system_prompt,
            use_gpt4=True
        )
        print(f"✅ GPT-4 funcionou! Resposta: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ GPT-4 falhou: {e}")
        return False
    
    try:
        # Testa GPT-3.5 (limite 4096)
        print("\n=== Testando GPT-3.5 ===")
        response = await gerar_resposta_ia(
            prompt=large_prompt,
            system_prompt=system_prompt,
            use_gpt4=False
        )
        print(f"✅ GPT-3.5 funcionou! Resposta: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ GPT-3.5 falhou: {e}")
        return False
    
    return True

async def test_realistic_prompt():
    """Testa com um prompt similar ao que está falhando no log"""
    
    system_prompt = "Você é um assistente de análise de métricas APM."
    
    # Simula um prompt similar ao do log (9647 tokens)
    realistic_prompt = """
    Análise do ambiente New Relic:
    
    ENTIDADES PRINCIPAIS:
    """ + "- Entidade de exemplo com muitos detalhes e métricas\n" * 500
    
    print(f"Testando com prompt realístico de ~{len(realistic_prompt)} caracteres")
    
    try:
        print("\n=== Testando prompt realístico ===")
        response = await gerar_resposta_ia(
            prompt=realistic_prompt,
            system_prompt=system_prompt,
            use_gpt4=True
        )
        print(f"✅ Prompt realístico funcionou! Resposta: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Prompt realístico falhou: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testando correção do corte de tokens...")
    
    async def run_tests():
        print("\n" + "="*50)
        print("TESTE 1: Prompt muito grande")
        success1 = await test_token_cutting()
        
        print("\n" + "="*50) 
        print("TESTE 2: Prompt realístico")
        success2 = await test_realistic_prompt()
        
        print("\n" + "="*50)
        if success1 and success2:
            print("✅ TODOS OS TESTES PASSARAM!")
            print("🎉 O corte de tokens está funcionando corretamente!")
        else:
            print("❌ ALGUNS TESTES FALHARAM!")
            print("🔍 Verifique os logs acima para mais detalhes.")
    
    asyncio.run(run_tests())
