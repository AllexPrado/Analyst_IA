#!/usr/bin/env python
"""
Script para testar o Chat IA do Analyst IA com prompts avançados.
Testa diversos cenários e verifica a qualidade das respostas.

Uso:
    python teste_chat_avancado.py

Requer:
    - Backend Analyst IA em execução
    - Serviço New Relic configurado
"""

import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import sys

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações
API_URL = "http://localhost:5173/chat"
RESULTADOS_DIR = Path("./testes_chat")
RESULTADOS_DIR.mkdir(exist_ok=True, parents=True)

# Cenários de teste
CENARIOS_TESTE = [
    {
        "id": "status_geral",
        "pergunta": "Como está o sistema hoje?",
        "descricao": "Verifica se o sistema fornece uma visão geral proativa",
        "criterios": ["status", "entidades", "problema", "alerta"]
    },
    {
        "id": "apis_lentas",
        "pergunta": "Quais APIs estão lentas nas últimas 24 horas?",
        "descricao": "Testa análise de performance de APIs",
        "criterios": ["latência", "resposta", "apdex", "threshold"]
    },
    {
        "id": "causa_raiz",
        "pergunta": "Por que estamos tendo erros no serviço de autenticação?",
        "descricao": "Verifica capacidade de análise de causa raiz",
        "criterios": ["causa", "erro", "correlação", "stack"]
    },
    {
        "id": "sql_performance",
        "pergunta": "Mostre queries SQL com problemas de performance",
        "descricao": "Testa análise de problemas de banco de dados",
        "criterios": ["query", "sql", "tempo", "execução"]
    },
    {
        "id": "perfil_gestor",
        "pergunta": "Resuma o status do sistema para uma apresentação executiva",
        "descricao": "Testa adaptação para perfil de gestor",
        "criterios": ["resumo", "impacto", "negócio", "visão geral"]
    }
]

async def teste_chat(cenario: Dict[str, Any]) -> Dict[str, Any]:
    """Executa teste de chat para um cenário específico."""
    try:
        logger.info(f"Executando cenário: {cenario['id']} - {cenario['descricao']}")
        
        # Chama API de chat
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json={"pergunta": cenario["pergunta"]}) as response:
                if response.status != 200:
                    logger.error(f"Erro na API: {response.status} - {await response.text()}")
                    return {
                        "cenario": cenario["id"],
                        "sucesso": False,
                        "erro": f"Status code: {response.status}",
                        "timestamp": datetime.now().isoformat()
                    }
                
                resultado = await response.json()
                
        # Analisa a resposta
        resposta = resultado.get("resposta", "")
        contexto = resultado.get("contexto", {})
        
        # Verifica se a resposta contém os critérios esperados
        criterios_encontrados = []
        termos_faltantes = []
        
        for criterio in cenario["criterios"]:
            if criterio.lower() in resposta.lower():
                criterios_encontrados.append(criterio)
            else:
                termos_faltantes.append(criterio)
        
        # Calcula pontuação de qualidade (0-100)
        porcentagem_criterios = len(criterios_encontrados) / len(cenario["criterios"]) * 100
        
        # Analisa extensão e estrutura da resposta
        estrutura_pontos = 0
        if "##" in resposta or "###" in resposta:  # Tem formatação markdown com títulos
            estrutura_pontos += 10
        if len(resposta.split("\n")) > 5:  # Tem estrutura com parágrafos
            estrutura_pontos += 10
        if any(x in resposta.lower() for x in ["recomend", "suger", "ação"]):  # Tem recomendações
            estrutura_pontos += 10
        
        # Pontua comprimento adequado (muito curto ou muito longo é ruim)
        tamanho = len(resposta)
        if 500 <= tamanho <= 4000:
            tamanho_pontos = 20
        elif 300 <= tamanho < 500 or 4000 < tamanho <= 6000:
            tamanho_pontos = 10
        else:
            tamanho_pontos = 0
            
        # Pontuação final
        pontuacao_qualidade = min(100, porcentagem_criterios + estrutura_pontos + tamanho_pontos)
        
        # Resultados
        return {
            "cenario": cenario["id"],
            "pergunta": cenario["pergunta"],
            "resposta": resposta,
            "sucesso": True,
            "criterios_encontrados": criterios_encontrados,
            "termos_faltantes": termos_faltantes,
            "pontuacao_qualidade": pontuacao_qualidade,
            "timestamp": datetime.now().isoformat(),
            "aprendizado_ativo": contexto.get("aprendizado_ativo", False),
            "tamanho_resposta": len(resposta),
            "estrutura": {
                "tem_titulos": "##" in resposta,
                "tem_recomendacoes": any(x in resposta.lower() for x in ["recomend", "suger", "ação"]),
                "tem_dados_reais": any(x in resposta for x in ["%", "ms", "s", "KB", "MB", "GB"])
            }
        }
        
    except Exception as e:
        logger.error(f"Erro no teste: {cenario['id']}", exc_info=True)
        return {
            "cenario": cenario["id"],
            "sucesso": False,
            "erro": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def executar_testes():
    """Executa todos os testes e salva resultados."""
    resultados = []
    
    for cenario in CENARIOS_TESTE:
        resultado = await teste_chat(cenario)
        resultados.append(resultado)
        
        # Pequeno intervalo entre testes
        await asyncio.sleep(1)
    
    # Salva resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo_resultados = RESULTADOS_DIR / f"resultados_teste_{timestamp}.json"
    
    with open(arquivo_resultados, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "resultados": resultados
        }, f, ensure_ascii=False, indent=2)
    
    # Imprime resumo
    logger.info(f"Testes concluídos. Resultados salvos em {arquivo_resultados}")
    
    print("\n" + "=" * 50)
    print("RESUMO DOS TESTES DE CHAT COM PROMPT AVANÇADO")
    print("=" * 50)
    
    pontuacao_total = 0
    sucesso_total = 0
    
    for resultado in resultados:
        status = "✅ SUCESSO" if resultado["sucesso"] else "❌ FALHA"
        pontuacao = resultado.get("pontuacao_qualidade", 0)
        pontuacao_total += pontuacao
        if resultado["sucesso"]:
            sucesso_total += 1
        
        print(f"{resultado['cenario']}: {status} - Qualidade: {pontuacao:.1f}/100")
        
    media_qualidade = pontuacao_total / len(resultados) if resultados else 0
    taxa_sucesso = (sucesso_total / len(resultados)) * 100 if resultados else 0
    
    print("\nRESULTADO FINAL")
    print(f"Taxa de sucesso: {taxa_sucesso:.1f}%")
    print(f"Qualidade média: {media_qualidade:.1f}/100")
    
    if media_qualidade >= 80:
        print("\nVERDICTO: EXCELENTE! O sistema está fornecendo respostas de alta qualidade.")
    elif media_qualidade >= 60:
        print("\nVERDICTO: BOM! O sistema está funcionando bem mas há espaço para melhorias.")
    else:
        print("\nVERDICTO: ATENÇÃO! O sistema precisa de ajustes para melhorar qualidade.")
    
    print("=" * 50)
    print(f"Detalhes completos em: {arquivo_resultados}")

if __name__ == "__main__":
    logger.info("Iniciando testes de Chat com Prompt Avançado")
    asyncio.run(executar_testes())
