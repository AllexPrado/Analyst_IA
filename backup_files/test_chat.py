"""
Script para verificar o funcionamento do chat com os dados limpos
"""

import asyncio
import logging
import json
import sys
from pathlib import Path
from datetime import datetime

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona pasta atual ao path para importar módulos locais
sys.path.append(str(Path(__file__).parent))

class ChatInput:
    def __init__(self, pergunta):
        self.pergunta = pergunta

async def testar_chat():
    """
    Testa o chat com diferentes perguntas para verificar a qualidade das respostas
    """
    try:
        print("\n" + "="*80)
        print(" 🧪 INICIANDO TESTE DO CHAT")
        print("="*80)
        
        # Importa o endpoint de chat
        from backend.main import chat_endpoint
        
        # Lista de perguntas para testar
        perguntas = [
            "Como está a performance geral?",
            "Quais são os serviços com mais erros?",
            "Qual a média de latência dos aplicativos?",
            "O que mostram os dados de disponibilidade?",
            "Há algum alerta ativo agora?"
        ]
        
        for i, pergunta in enumerate(perguntas):
            print(f"\n📝 Teste {i+1}/{len(perguntas)}: \"{pergunta}\"")
            
            # Chama o endpoint do chat
            resposta = await chat_endpoint(ChatInput(pergunta))
            
            if not resposta or not hasattr(resposta, "resposta"):
                print(f"   ❌ Erro: Resposta inválida")
                continue
                
            # Analisa a resposta
            resposta_texto = resposta.resposta
            
            # Estatísticas básicas
            tamanho = len(resposta_texto)
            linhas = resposta_texto.count("\n") + 1
            
            # Verifica se é uma resposta genérica ou de fallback
            respostas_genericas = [
                "não tenho dados",
                "não possuo informações",
                "não foi possível encontrar",
                "não há dados",
                "não sei responder",
                "Não há dados suficientes",
                "Verifique se a instrumentação"
            ]
            
            generica = any(frase.lower() in resposta_texto.lower() for frase in respostas_genericas)
            
            # Verificar se contém informações técnicas
            contem_metricas = any(termo in resposta_texto.lower() for termo in ["apdex", "latência", "erro", "throughput", "cpu", "memória", "disponibilidade"])
            contem_nrql = "NRQL" in resposta_texto or "SELECT" in resposta_texto and "FROM" in resposta_texto
            
            # Resumo da análise
            print(f"   📊 Tamanho: {tamanho} caracteres, {linhas} linhas")
            print(f"   📊 Resposta genérica: {'Sim ⚠️' if generica else 'Não ✅'}")
            print(f"   📊 Contém métricas: {'Sim ✅' if contem_metricas else 'Não ⚠️'}")
            print(f"   📊 Contém NRQL: {'Sim ✅' if contem_nrql else 'Não'}")
            
            # Fragmento da resposta
            fragmento = resposta_texto[:150].replace("\n", " ") + "..." if len(resposta_texto) > 150 else resposta_texto
            print(f"   💬 Fragmento: \"{fragmento}\"")
        
        print("\n" + "="*80)
        print(" ✅ TESTE DO CHAT CONCLUÍDO")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Erro ao testar chat: {e}", exc_info=True)
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(testar_chat())
