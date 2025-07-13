"""
Exemplo de uso da interface do Agno e Agent-S.

Este script demonstra como se comunicar com o Agno e o Agent-S usando a
interface de comunicação simplificada.
"""

import asyncio
import logging
import json
import sys
import os
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("exemplo_agno")

# Adicionar o diretório atual ao PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar a interface do Agno
try:
    from core_inteligente.agno_interface import AgnoInterface, falar_com_agno
except ImportError as e:
    logger.error(f"Erro ao importar módulo de comunicação com Agno: {e}")
    sys.exit(1)

async def exemplo_comunicacao_simples():
    """Exemplo de comunicação simples com o Agno"""
    logger.info("=== Exemplo de Comunicação Simples com o Agno ===")
    
    try:
        # Enviar uma mensagem diretamente para o Agno
        resposta = await falar_com_agno(
            "Verifique o status do sistema e me informe se há algum problema"
        )
        
        print("\n=== Resposta do Agno ===")
        print(json.dumps(resposta, indent=2))
        print("========================\n")
        
    except Exception as e:
        logger.error(f"Erro durante comunicação simples: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def exemplo_conversacao():
    """Exemplo de conversação contínua com o Agno"""
    logger.info("=== Exemplo de Conversação com o Agno ===")
    
    try:
        # Iniciar interface do Agno com sessão persistente
        agno = AgnoInterface()
        session_id = agno.iniciar_sessao()
        logger.info(f"Sessão iniciada: {session_id}")
        
        # Primeira pergunta
        print("\n> Enviando primeira pergunta ao Agno...")
        resposta1 = await agno.enviar_mensagem(
            "Quais são as principais métricas de performance do sistema?"
        )
        
        print("=== Resposta 1 ===")
        print(json.dumps(resposta1, indent=2))
        print("=================\n")
        
        # Segunda pergunta (com contexto da primeira)
        print("> Enviando segunda pergunta com contexto da primeira...")
        resposta2 = await agno.enviar_mensagem(
            "Existe alguma métrica fora do padrão normal?"
        )
        
        print("=== Resposta 2 ===")
        print(json.dumps(resposta2, indent=2))
        print("=================\n")
        
        # Terceira pergunta (com contexto completo)
        print("> Enviando terceira pergunta com todo o contexto anterior...")
        resposta3 = await agno.enviar_mensagem(
            "O que podemos fazer para melhorar o desempenho?"
        )
        
        print("=== Resposta 3 ===")
        print(json.dumps(resposta3, indent=2))
        print("=================\n")
        
        # Verificar histórico
        historico = agno.obter_historico()
        print(f"\n> Histórico da conversa ({len(historico)} mensagens):")
        for i, item in enumerate(historico):
            tipo = item.get("tipo", "desconhecido")
            timestamp = item.get("timestamp", "")
            
            if tipo == "usuario":
                print(f"{i+1}. Você ({timestamp}): {item.get('mensagem')}")
            elif tipo == "agno":
                if "erro" in item.get("resposta", {}):
                    print(f"{i+1}. Agno ({timestamp}): Erro - {item['resposta']['erro']}")
                else:
                    print(f"{i+1}. Agno ({timestamp}): {item['resposta'].get('mensagem', 'Sem mensagem')}")
        
    except Exception as e:
        logger.error(f"Erro durante conversação: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def exemplo_comando_direto():
    """Exemplo de execução direta de comandos através do Agno para o Agent-S"""
    logger.info("=== Exemplo de Comando Direto via Agno para Agent-S ===")
    
    try:
        # Iniciar interface
        agno = AgnoInterface()
        agno.iniciar_sessao()
        
        # Executar um comando específico no Agent-S
        print("\n> Executando comando de diagnóstico via Agno...")
        resposta = await agno.executar_comando(
            "diagnosticar_sistema",
            parametros={
                "escopo": "completo",
                "incluir_metricas": True,
                "formato_saida": "detalhado"
            }
        )
        
        print("=== Resultado do Comando ===")
        print(json.dumps(resposta, indent=2))
        print("===========================\n")
        
    except Exception as e:
        logger.error(f"Erro durante execução de comando: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def exemplo_verificar_status():
    """Exemplo de verificação de status dos agentes"""
    logger.info("=== Exemplo de Verificação de Status ===")
    
    try:
        # Iniciar interface
        agno = AgnoInterface()
        
        # Verificar status dos agentes
        print("\n> Verificando status do Agno e Agent-S...")
        status = await agno.verificar_status()
        
        print("=== Status dos Agentes ===")
        print(json.dumps(status, indent=2))
        print("=========================\n")
        
    except Exception as e:
        logger.error(f"Erro durante verificação de status: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def main():
    """Função principal que executa todos os exemplos"""
    print("*** Demonstração de Comunicação com Agno e Agent-S ***\n")
    
    try:
        # Executar exemplos
        await exemplo_verificar_status()
        await exemplo_comunicacao_simples()
        await exemplo_conversacao()
        await exemplo_comando_direto()
        
        print("\n*** Demonstração Concluída ***")
        
    except Exception as e:
        logger.error(f"Erro durante a execução dos exemplos: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
