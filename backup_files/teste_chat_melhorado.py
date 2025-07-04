"""
Script para testar as melhorias implementadas no Chat IA
Verifica a qualidade das respostas após as modificações
"""

import asyncio
import logging
import json
import sys
import re
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

async def testar_chat_melhorado():
    """
    Testa o chat com diferentes perguntas e avalia a qualidade das respostas
    após as melhorias implementadas.
    """
    try:
        print("\n" + "="*80)
        print(" 🔬 INICIANDO TESTE DO CHAT IA MELHORADO")
        print("="*80)
        
        # Importa o endpoint de chat
        from backend.main import chat_endpoint
        
        # Lista de perguntas para testar diferentes cenários
        perguntas = [
            "Quais são os serviços mais críticos neste momento?",
            "Há algum padrão de erro comum entre as entidades com problemas?",
            "Qual a tendência de performance do sistema nas últimas horas?",
            "Compare o desempenho entre os diferentes domínios monitorados",
            "Qual a correlação entre uso de CPU e erros reportados?"
        ]
        
        resultados = []
        
        for i, pergunta in enumerate(perguntas):
            print(f"\n📝 Teste {i+1}/{len(perguntas)}: \"{pergunta}\"")
            
            # Chama o endpoint do chat
            inicio = datetime.now()
            resposta = await chat_endpoint(ChatInput(pergunta))
            fim = datetime.now()
            tempo_resposta = (fim - inicio).total_seconds()
            
            if not resposta or not hasattr(resposta, "resposta"):
                print(f"   ❌ Erro: Resposta inválida")
                continue
                
            # Analisa a resposta
            resposta_texto = resposta.resposta
            
            # Estatísticas básicas
            tamanho = len(resposta_texto)
            linhas = resposta_texto.count("\n") + 1
            palavras = len(re.findall(r'\w+', resposta_texto))
            
            # Verifica se é uma resposta genérica ou de fallback
            respostas_genericas = [
                "não tenho dados",
                "não possuo informações",
                "não foi possível encontrar",
                "não há dados",
                "não sei responder",
                "não tenho informações suficientes",
                "sem dados disponíveis",
                "preciso de mais informações"
            ]
            
            generica = any(frase.lower() in resposta_texto.lower() for frase in respostas_genericas)
            
            # Verificar se contém informações técnicas
            contem_metricas = any(termo in resposta_texto.lower() for termo in 
                               ["apdex", "latência", "erro", "throughput", "cpu", "memória", "disponibilidade"])
            contem_nrql = "NRQL" in resposta_texto or ("SELECT" in resposta_texto and "FROM" in resposta_texto)
            
            # Verificar se contém estrutura de análise
            contem_diagnostico = "diagnóstico" in resposta_texto.lower() or "análise" in resposta_texto.lower()
            contem_recomendacao = "recomend" in resposta_texto.lower() or "sugest" in resposta_texto.lower()
            
            # Qualidade técnica da resposta (baseada em heurísticas)
            score_tecnico = 0
            if contem_metricas: score_tecnico += 1
            if contem_nrql: score_tecnico += 1
            if contem_diagnostico: score_tecnico += 1
            if contem_recomendacao: score_tecnico += 1
            if not generica: score_tecnico += 1
            
            nivel_tecnico = "Baixo" if score_tecnico <= 1 else ("Médio" if score_tecnico <= 3 else "Alto")
            
            # Resumo da análise
            print(f"   ⏱️ Tempo de resposta: {tempo_resposta:.2f}s")
            print(f"   📊 Tamanho: {tamanho} caracteres, {palavras} palavras, {linhas} linhas")
            print(f"   📊 Resposta genérica: {'Sim ⚠️' if generica else 'Não ✅'}")
            print(f"   📊 Contém métricas: {'Sim ✅' if contem_metricas else 'Não ⚠️'}")
            print(f"   📊 Contém NRQL: {'Sim ✅' if contem_nrql else 'Não'}")
            print(f"   📊 Contém diagnóstico: {'Sim ✅' if contem_diagnostico else 'Não ⚠️'}")
            print(f"   📊 Contém recomendações: {'Sim ✅' if contem_recomendacao else 'Não ⚠️'}")
            print(f"   🎓 Nível técnico: {nivel_tecnico}")
            
            # Fragmento da resposta
            fragmento = resposta_texto[:150].replace("\n", " ") + "..." if len(resposta_texto) > 150 else resposta_texto
            print(f"   💬 Fragmento: \"{fragmento}\"")
            
            # Armazena resultados para análise comparativa
            resultados.append({
                "pergunta": pergunta,
                "tempo_resposta": tempo_resposta,
                "tamanho": tamanho,
                "palavras": palavras,
                "generica": generica,
                "contem_metricas": contem_metricas,
                "contem_nrql": contem_nrql,
                "contem_diagnostico": contem_diagnostico,
                "contem_recomendacao": contem_recomendacao,
                "nivel_tecnico": nivel_tecnico,
                "score_tecnico": score_tecnico
            })
        
        # Análise comparativa
        if resultados:
            print("\n" + "="*80)
            print(" 📊 ANÁLISE COMPARATIVA")
            print("="*80)
            
            avg_tempo = sum(r["tempo_resposta"] for r in resultados) / len(resultados)
            avg_tamanho = sum(r["tamanho"] for r in resultados) / len(resultados)
            avg_palavras = sum(r["palavras"] for r in resultados) / len(resultados)
            avg_score = sum(r["score_tecnico"] for r in resultados) / len(resultados)
            
            print(f"Tempo médio de resposta: {avg_tempo:.2f}s")
            print(f"Tamanho médio: {avg_tamanho:.0f} caracteres, {avg_palavras:.0f} palavras")
            print(f"Score técnico médio: {avg_score:.1f}/5")
            print(f"Respostas genéricas: {sum(1 for r in resultados if r['generica'])}/{len(resultados)}")
            print(f"Respostas com diagnóstico: {sum(1 for r in resultados if r['contem_diagnostico'])}/{len(resultados)}")
            print(f"Respostas com recomendações: {sum(1 for r in resultados if r['contem_recomendacao'])}/{len(resultados)}")
            
            # Salva os resultados em um arquivo para referência
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"logs/teste_chat_{timestamp}.json", "w", encoding="utf-8") as f:
                json.dump(resultados, f, indent=2, ensure_ascii=False)
            print(f"\nResultados salvos em: logs/teste_chat_{timestamp}.json")
        
        print("\n" + "="*80)
        print(" ✅ TESTE DO CHAT CONCLUÍDO")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Erro ao testar chat: {e}", exc_info=True)
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(testar_chat_melhorado())
