#!/usr/bin/env python3
"""
Script para testar a API de chat do Analyst_IA de forma robusta.
Inclui verificação de portas, tentativas múltiplas e feedback detalhado.
"""

import asyncio
import os
import sys
import json
from datetime import datetime
import aiohttp
import time
import argparse

# Possíveis portas onde o backend pode estar rodando
POSSÍVEIS_PORTAS = [5000, 8000, 3001]

# Possíveis caminhos de endpoint
POSSÍVEIS_ENDPOINTS = [
    "/api/chat",
    "/chat",
    "/api/v1/chat"
]

# Perguntas de teste para verificar o funcionamento do chat
PERGUNTAS_TESTE = [
    "Resumir os incidentes da última semana",
    "Quais são as aplicações com pior desempenho?",
    "Qual é o estado atual da infraestrutura?",
    "Mostrar métricas principais de APM"
]

async def verificar_endpoint(session, base_url, endpoint, pergunta):
    """Testa um endpoint específico da API de chat"""
    url = f"{base_url}{endpoint}"
    try:
        print(f"Testando endpoint: {url}")
        payload = {"pergunta": pergunta}
        
        async with session.post(url, json=payload, timeout=10) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Endpoint funcionando: {url}")
                return url, result
            else:
                print(f"❌ Endpoint respondeu com erro {response.status}: {url}")
                return None, None
    except Exception as e:
        print(f"❌ Erro ao testar {url}: {e.__class__.__name__}")
        return None, None

async def descobrir_endpoint_chat():
    """Descobre automaticamente qual endpoint de chat está disponível"""
    async with aiohttp.ClientSession() as session:
        for porta in POSSÍVEIS_PORTAS:
            base_url = f"http://localhost:{porta}"
            print(f"\nTestando servidor na porta {porta}...")
            
            for endpoint in POSSÍVEIS_ENDPOINTS:
                url, result = await verificar_endpoint(
                    session, base_url, endpoint, PERGUNTAS_TESTE[0]
                )
                if url:
                    return url, result
    
    return None, None

async def testar_api_chat(url=None, max_tentativas=3, intervalo=5):
    """Testa a API de chat com uma série de perguntas de teste"""
    try:
        print("\n=== TESTE DA API DE CHAT ANALYST_IA ===")
        
        # Se não foi fornecido um URL, tenta descobrir automaticamente
        if not url:
            print("Descobrindo endpoint de chat disponível...")
            url, _ = await descobrir_endpoint_chat()
            
            if not url:
                print("❌ Não foi possível encontrar um endpoint de chat funcionando!")
                print("Verifique se o backend está rodando e tente novamente.")
                return False
        
        async with aiohttp.ClientSession() as session:
            for tentativa in range(max_tentativas):
                try:
                    print(f"\nTentativa {tentativa + 1}/{max_tentativas} em {url}")
                    
                    # Escolhe uma pergunta de teste
                    pergunta = PERGUNTAS_TESTE[tentativa % len(PERGUNTAS_TESTE)]
                    
                    print(f"Pergunta: \"{pergunta}\"")
                    payload = {"pergunta": pergunta}
                    
                    async with session.post(url, json=payload, timeout=30) as response:
                        status = response.status
                        print(f"Status: {status}")
                        
                        if status == 200:
                            result = await response.json()
                            
                            print("\n==== RESPOSTA DO CHAT ====")
                            
                            # Exibir a resposta
                            if "resposta" in result:
                                resposta = result["resposta"]
                                print("\nResposta:")
                                print(resposta[:500] + "..." if len(resposta) > 500 else resposta)
                                
                                # Verificar se a resposta parece real ou simulada
                                palavras_chave_simuladas = [
                                    "dados simulados", "resposta simulada", 
                                    "template", "dados fictícios"
                                ]
                                
                                if any(palavra in resposta.lower() for palavra in palavras_chave_simuladas):
                                    print("\n⚠️ ATENÇÃO: A resposta parece conter dados simulados!")
                                else:
                                    print("\n✅ A resposta parece usar dados reais.")
                            
                            # Exibir informações do contexto
                            if "contexto" in result and result["contexto"]:
                                print("\nContexto:")
                                contexto = result["contexto"]
                                for key, value in contexto.items():
                                    if isinstance(value, str) and len(value) > 100:
                                        value = value[:100] + "..."
                                    print(f"- {key}: {value}")
                                
                                # Verificar se o contexto tem dados reais
                                if "fonte_dados" in contexto:
                                    print(f"\nFonte de dados: {contexto['fonte_dados']}")
                                    if "simulado" in str(contexto['fonte_dados']).lower():
                                        print("⚠️ USANDO DADOS SIMULADOS!")
                                    else:
                                        print("✅ USANDO DADOS REAIS!")
                            
                            # Salvar resposta completa para análise
                            os.makedirs("historico", exist_ok=True)
                            output_path = f"historico/teste_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            with open(output_path, "w", encoding="utf-8") as f:
                                json.dump(result, f, indent=2, ensure_ascii=False)
                            print(f"\nResposta completa salva em: {output_path}")
                            
                            return True
                        else:
                            print(f"Erro: {status}")
                            error_text = await response.text()
                            print(error_text[:500])
                            
                            if tentativa < max_tentativas - 1:
                                print(f"Tentando novamente em {intervalo} segundos...")
                                await asyncio.sleep(intervalo)
                            else:
                                print("❌ Todas as tentativas falharam!")
                                return False
                except Exception as e:
                    print(f"Erro durante a tentativa {tentativa + 1}: {e}")
                    if tentativa < max_tentativas - 1:
                        print(f"Tentando novamente em {intervalo} segundos...")
                        await asyncio.sleep(intervalo)
                    else:
                        print("❌ Todas as tentativas falharam!")
                        return False
            
    except Exception as e:
        print(f"Erro ao testar API: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Testa a API de chat do Analyst_IA')
    parser.add_argument('--url', help='URL do endpoint de chat para testar')
    parser.add_argument('--tentativas', type=int, default=3, help='Número máximo de tentativas')
    parser.add_argument('--intervalo', type=int, default=5, help='Intervalo entre tentativas (segundos)')
    args = parser.parse_args()
    
    # Executar o teste
    if asyncio.run(testar_api_chat(args.url, args.tentativas, args.intervalo)):
        print("\n✅ Teste da API de chat concluído com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Teste da API de chat falhou!")
        sys.exit(1)

if __name__ == "__main__":
    main()
