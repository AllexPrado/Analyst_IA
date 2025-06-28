import asyncio
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importa diretamente as funções de cache e coletor de contexto
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.cache import (
    get_cache, 
    buscar_no_cache_por_pergunta,
    forcar_atualizacao_cache,
    atualizar_cache_completo,
    diagnosticar_cache
)

from utils.newrelic_collector import coletar_contexto_completo
from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia

async def check_cache_data():
    """Verifica se os dados no cache estão completos"""
    logger.info("Verificando dados no cache...")
    
    cache = await get_cache()
    diag = diagnosticar_cache()
    
    logger.info(f"Diagnóstico do cache: {json.dumps(diag, indent=2)}")
    
    if not cache or not cache.get("entidades"):
        logger.warning("Cache vazio ou sem entidades. Forçando atualização...")
        await forcar_atualizacao_cache(coletar_contexto_completo)
        cache = await get_cache()
    
    entidades = cache.get("entidades", [])
    logger.info(f"Total de entidades no cache: {len(entidades)}")
    
    # Verifica domínios das entidades
    dominios = {}
    for entidade in entidades:
        domain = entidade.get("domain", "UNKNOWN")
        dominios[domain] = dominios.get(domain, 0) + 1
    
    logger.info(f"Entidades por domínio: {dominios}")
    
    # Verifica métricas nas entidades
    entidades_com_metricas = [e for e in entidades if e.get("metricas")]
    logger.info(f"Entidades com métricas: {len(entidades_com_metricas)}/{len(entidades)}")
    
    # Se menos de 50% das entidades têm métricas, há um problema
    if len(entidades_com_metricas) < len(entidades) * 0.5:
        logger.warning("ALERTA: Menos de 50% das entidades têm métricas!")
    
    # Retorna status geral do cache
    return {
        "cache_status": "OK" if len(entidades) > 0 else "VAZIO",
        "total_entidades": len(entidades),
        "entidades_com_metricas": len(entidades_com_metricas),
        "dominios": dominios,
        "diagnostico": diag
    }

async def test_chat_with_direct_api(pergunta: str) -> Dict[str, Any]:
    """
    Testa o fluxo do chat diretamente usando as funções da API
    """
    logger.info(f"Testando pergunta: '{pergunta}'")
    
    # Passo 1: Busca contexto inteligente baseado na pergunta
    contexto = await buscar_no_cache_por_pergunta(
        pergunta, 
        atualizar_se_necessario=True, 
        coletar_contexto_fn=coletar_contexto_completo
    )
    
    if not contexto:
        logger.error("Nenhum contexto retornado!")
        return {"success": False, "error": "Contexto vazio"}
    
    # Passo 2: Detecta persona e monta prompt
    persona = detectar_persona(pergunta)
    logger.info(f"Persona detectada: {persona}")
    
    contexto_str = json.dumps(contexto, indent=2, ensure_ascii=False)
    prompt = montar_prompt_por_persona(persona, contexto_str)
    
    # Passo 3: Gera resposta com a OpenAI
    try:
        prompt_final = f"{prompt}\n\nPergunta ou situação: {pergunta}"
        resposta = await gerar_resposta_ia(prompt_final)
        
        # Verifica se a resposta parece genérica
        generic_indicators = [
            "Não tenho dados suficientes",
            "Não possuo informações",
            "Não tenho acesso a",
            "Preciso de mais detalhes",
            "Não tenho contexto",
            "Não posso fornecer dados específicos"
        ]
        
        is_generic = any(indicator.lower() in resposta.lower() for indicator in generic_indicators)
        
        # Extrai seção do contexto para análise
        context_sample = str(contexto)[:500] + "..." if len(str(contexto)) > 500 else str(contexto)
        
        return {
            "success": True,
            "resposta": resposta,
            "is_generic": is_generic,
            "persona": persona,
            "prompt_size": len(prompt_final),
            "context_sample": context_sample,
            "context_keys": list(contexto.keys()) if isinstance(contexto, dict) else None
        }
    except Exception as e:
        logger.error(f"Erro ao gerar resposta: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """
    Função principal que testa o sistema de cache e chat
    """
    logger.info("Iniciando testes do sistema de cache e chat")
    
    # 1. Verifica estado do cache
    cache_status = await check_cache_data()
    logger.info(f"Status do cache: {json.dumps(cache_status, indent=2)}")
    
    # 2. Testa perguntas no chat
    perguntas = [
        "Como está o status geral do sistema agora?",
        "Quais são as métricas atuais de performance das aplicações?",
        "Houve algum erro nas últimas 24 horas?",
        "Como está o uso de CPU dos servidores no momento?",
        "Qual a disponibilidade atual do sistema?"
    ]
    
    results = []
    for pergunta in perguntas:
        result = await test_chat_with_direct_api(pergunta)
        results.append({
            "pergunta": pergunta,
            "resultado": result
        })
    
    # Gera relatório de resultados
    output = {
        "timestamp": datetime.now().isoformat(),
        "cache_status": cache_status,
        "chat_tests": results
    }
    
    with open("resultado_teste_chat.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Exibe um resumo
    print("\n===== RESUMO DOS TESTES DE CHAT =====")
    generic_count = sum(1 for item in results if item["resultado"].get("is_generic", True))
    print(f"Respostas genéricas: {generic_count}/{len(results)}")
    
    if generic_count > 0:
        print("\nRespostas genéricas encontradas nas perguntas:")
        for item in results:
            if item["resultado"].get("is_generic", True):
                print(f"- '{item['pergunta']}'")
                if item["resultado"].get("success"):
                    print(f"  Resposta: '{item['resultado']['resposta'][:100]}...'")
    
    print("\nRespostas detalhadas salvas em resultado_teste_chat.json")

if __name__ == "__main__":
    asyncio.run(main())
