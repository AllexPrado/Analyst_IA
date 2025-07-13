"""
Ferramenta interativa para conversar com o Agno.

Este script permite uma conversa interativa com o agente Agno usando uma
interface simples de linha de comando.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("agno_chat")

# Adicionar o diretório atual ao PATH para encontrar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def clear_screen():
    """Limpa a tela do console"""
    os.system('cls' if os.name == 'nt' else 'clear')

async def main():
    """Função principal de conversação interativa"""
    # Importar a interface do Agno
    try:
        from core_inteligente.agno_interface import AgnoInterface, falar_com_agno
    except ImportError as e:
        logger.error(f"Erro ao importar módulo de interface do Agno: {e}")
        logger.info("Verifique se você está executando o script a partir do diretório raiz do projeto.")
        return 1
    
    # Cabeçalho
    clear_screen()
    print("=" * 60)
    print("         🤖 CONVERSA INTERATIVA COM O AGNO 🤖")
    print("=" * 60)
    print("\nBem-vindo à interface de conversação com o agente Agno!")
    print("Digite suas mensagens e pressione Enter para enviar.")
    print("Digite 'sair' ou 'exit' para encerrar a conversa.\n")
    
    # Criar interface e iniciar sessão
    agno = AgnoInterface()
    session_id = agno.iniciar_sessao()
    print(f"Sessão iniciada: {session_id}")
    
    # Verificar status dos agentes
    print("\nVerificando status dos agentes...")
    try:
        status = await agno.verificar_status()
        
        # Verificar se os agentes estão ativos
        agno_ativo = status.get("agno", {}).get("ativo", False)
        agents_ativo = status.get("agent-s", {}).get("ativo", False)
        
        if agno_ativo and agents_ativo:
            print("✅ Agno e Agent-S estão ativos e prontos para uso.")
        elif agno_ativo:
            print("⚠️ Agno está ativo, mas Agent-S não respondeu. Funcionalidade limitada.")
        elif agents_ativo:
            print("⚠️ Agent-S está ativo, mas Agno não respondeu. Funcionalidade limitada.")
        else:
            print("❌ Nenhum agente respondeu. O sistema pode não estar funcionando corretamente.")
            print("   Continuando em modo simulado...")
    except Exception as e:
        logger.warning(f"Não foi possível verificar o status dos agentes: {e}")
        print("⚠️ Status dos agentes indisponível. Continuando em modo simulado...")
    
    # Loop principal de conversa
    print("\n" + "-" * 60)
    print("Inicie sua conversa com o Agno. Digite 'sair' para encerrar.")
    print("-" * 60 + "\n")
    
    while True:
        try:
            # Obter mensagem do usuário
            mensagem = input("Você: ")
            
            # Verificar se é para sair
            if mensagem.lower() in ["sair", "exit", "quit"]:
                print("\nEncerrando conversa com o Agno...")
                break
            
            # Enviar mensagem para o Agno
            print("Agno está processando...")
            try:
                resposta = await falar_com_agno(mensagem, session_id=session_id)
                
                # Verificar se houve erro
                if resposta.get("erro"):
                    print(f"❌ Erro: {resposta.get('mensagem', 'Erro desconhecido')}")
                    if resposta.get("sugestao"):
                        print(f"💡 Sugestão: {resposta['sugestao']}")
                else:
                    # Exibir resposta formatada
                    print(f"\nAgno: {resposta.get('mensagem', 'Sem resposta disponível.')}")
                    
                    # Exibir sugestões ou próximos passos, se houver
                    if resposta.get("sugestoes"):
                        print("\n💡 Sugestões:")
                        for sugestao in resposta["sugestoes"]:
                            print(f"  • {sugestao}")
                    
                    if resposta.get("acoes_realizadas"):
                        print("\n✅ Ações realizadas:")
                        for acao in resposta["acoes_realizadas"]:
                            print(f"  • {acao}")
            except Exception as e:
                logger.error(f"Erro ao processar mensagem: {e}")
                print(f"❌ Erro ao processar sua mensagem: {str(e)}")
            
            print("\n" + "-" * 60)
            
        except KeyboardInterrupt:
            print("\nConversa interrompida pelo usuário.")
            break
        except EOFError:
            print("\nEntrada encerrada.")
            break
    
    print("\nConversa encerrada. Até a próxima!")
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
