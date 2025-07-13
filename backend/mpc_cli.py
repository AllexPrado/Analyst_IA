"""
CLI para Comunicação com Agentes MPC

Esta ferramenta de linha de comando permite interagir facilmente com os agentes MPC
diretamente do terminal, sem precisar escrever código Python.

Exemplos de uso:
    python mpc_cli.py status                          - Verificar status de todos os agentes
    python mpc_cli.py status diagnostico              - Verificar status de um agente específico
    python mpc_cli.py send diagnostico run_diagnostic - Enviar comando para um agente
    python mpc_cli.py broadcast get_health            - Enviar comando para todos os agentes
    python mpc_cli.py history                         - Ver histórico de comunicações
    python mpc_cli.py history diagnostico             - Ver histórico de um agente específico
"""

import asyncio
import logging
import json
import sys
import os
import argparse
from datetime import datetime

# Adicionar o diretório principal ao PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mpc_cli")

def setup_parser():
    """Configura o parser de argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description='Ferramenta CLI para comunicação com agentes MPC',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comando a ser executado')
    
    # Comando 'status'
    status_parser = subparsers.add_parser('status', help='Verificar status dos agentes')
    status_parser.add_argument('agent_id', nargs='?', help='ID do agente específico (opcional)')
    
    # Comando 'send'
    send_parser = subparsers.add_parser('send', help='Enviar comando para um agente')
    send_parser.add_argument('agent_id', help='ID do agente')
    send_parser.add_argument('action', help='Ação a ser executada')
    send_parser.add_argument('--params', '-p', help='Parâmetros em formato JSON')
    send_parser.add_argument('--context', '-c', help='Contexto em formato JSON')
    send_parser.add_argument('--timeout', '-t', type=int, default=60, help='Tempo limite em segundos')
    
    # Comando 'broadcast'
    broadcast_parser = subparsers.add_parser('broadcast', help='Enviar comando para todos os agentes')
    broadcast_parser.add_argument('action', help='Ação a ser executada')
    broadcast_parser.add_argument('--params', '-p', help='Parâmetros em formato JSON')
    broadcast_parser.add_argument('--context', '-c', help='Contexto em formato JSON')
    
    # Comando 'history'
    history_parser = subparsers.add_parser('history', help='Ver histórico de comunicações')
    history_parser.add_argument('agent_id', nargs='?', help='ID do agente específico (opcional)')
    history_parser.add_argument('--limit', '-l', type=int, default=10, help='Número máximo de registros')
    
    # Comando 'config'
    config_parser = subparsers.add_parser('config', help='Gerenciar configuração dos agentes')
    config_subparsers = config_parser.add_subparsers(dest='config_command', help='Comando de configuração')
    
    # Subcomando 'show'
    config_show_parser = config_subparsers.add_parser('show', help='Exibir configuração atual')
    
    # Subcomando 'enable'
    config_enable_parser = config_subparsers.add_parser('enable', help='Ativar um agente')
    config_enable_parser.add_argument('agent_id', help='ID do agente a ser ativado')
    
    # Subcomando 'disable'
    config_disable_parser = config_subparsers.add_parser('disable', help='Desativar um agente')
    config_disable_parser.add_argument('agent_id', help='ID do agente a ser desativado')
    
    return parser

async def run_command(args):
    """Executa o comando especificado pelos argumentos"""
    # Importar os módulos MPC apenas quando necessário
    try:
        from core_inteligente.mpc_agent_communication import (
            send_agent_command,
            broadcast_to_agents,
            get_agent_status,
            get_agent_history,
            mpc_communication
        )
    except ImportError as e:
        logger.error(f"Erro ao importar módulo de comunicação MPC: {e}")
        return 1
    
    if args.command == 'status':
        # Verificar status dos agentes
        status = await get_agent_status(args.agent_id)
        print(json.dumps(status, indent=2))
    
    elif args.command == 'send':
        # Enviar comando para um agente específico
        try:
            parameters = json.loads(args.params) if args.params else {}
        except json.JSONDecodeError:
            logger.error(f"Erro: parâmetros não estão em formato JSON válido: {args.params}")
            return 1
        
        try:
            context = json.loads(args.context) if args.context else {}
        except json.JSONDecodeError:
            logger.error(f"Erro: contexto não está em formato JSON válido: {args.context}")
            return 1
        
        response = await send_agent_command(
            agent_id=args.agent_id,
            action=args.action,
            parameters=parameters,
            context=context
        )
        
        if response.status == "success":
            print("Comando executado com sucesso!")
            print(json.dumps(response.data, indent=2) if response.data else "Nenhum dado retornado")
        else:
            print(f"Erro: {response.error_message}")
            return 1
    
    elif args.command == 'broadcast':
        # Enviar comando para todos os agentes
        try:
            parameters = json.loads(args.params) if args.params else {}
        except json.JSONDecodeError:
            logger.error(f"Erro: parâmetros não estão em formato JSON válido: {args.params}")
            return 1
        
        try:
            context = json.loads(args.context) if args.context else {}
        except json.JSONDecodeError:
            logger.error(f"Erro: contexto não está em formato JSON válido: {args.context}")
            return 1
        
        responses = await broadcast_to_agents(
            action=args.action,
            parameters=parameters,
            context=context
        )
        
        print(f"Respostas recebidas de {len(responses)} agentes:")
        for agent_id, response in responses.items():
            status = "Sucesso" if response.status == "success" else f"Erro: {response.error_message}"
            print(f"{agent_id}: {status}")
            if response.data:
                print(f"  Dados: {json.dumps(response.data, indent=2)}")
    
    elif args.command == 'history':
        # Ver histórico de comunicações
        history = get_agent_history(agent_id=args.agent_id, limit=args.limit)
        
        if not history:
            print("Nenhum registro encontrado no histórico.")
            return 0
        
        for i, entry in enumerate(history):
            timestamp = entry.get("timestamp", "Unknown")
            agent_id = entry.get("request", {}).get("agent_id", "Unknown")
            action = entry.get("request", {}).get("action", "Unknown")
            status = entry.get("response", {}).get("status", "Unknown")
            duration = entry.get("duration", 0)
            
            print(f"{i+1}. [{timestamp}] {agent_id} - {action}")
            print(f"   Status: {status}")
            print(f"   Duração: {duration:.2f}s")
            
            if status == "error":
                error_msg = entry.get("response", {}).get("error_message", "Unknown error")
                print(f"   Erro: {error_msg}")
            
            print()
    
    elif args.command == 'config':
        if args.config_command == 'show':
            # Exibir configuração atual
            print(json.dumps(mpc_communication.config, indent=2))
        
        elif args.config_command == 'enable':
            # Ativar um agente
            agent = mpc_communication.get_agent_by_id(args.agent_id)
            if not agent:
                logger.error(f"Agente '{args.agent_id}' não encontrado")
                return 1
            
            # Atualizar a configuração
            for i, agent_config in enumerate(mpc_communication.config.get("agents", [])):
                if agent_config.get("id") == args.agent_id:
                    mpc_communication.config["agents"][i]["enabled"] = True
                    break
            
            # Salvar a configuração atualizada
            try:
                with open(mpc_communication._agent_config_file, "w") as f:
                    json.dump(mpc_communication.config, f, indent=4)
                print(f"Agente '{args.agent_id}' ativado com sucesso!")
            except Exception as e:
                logger.error(f"Erro ao salvar configuração: {e}")
                return 1
        
        elif args.config_command == 'disable':
            # Desativar um agente
            agent = mpc_communication.get_agent_by_id(args.agent_id)
            if not agent:
                logger.error(f"Agente '{args.agent_id}' não encontrado")
                return 1
            
            # Atualizar a configuração
            for i, agent_config in enumerate(mpc_communication.config.get("agents", [])):
                if agent_config.get("id") == args.agent_id:
                    mpc_communication.config["agents"][i]["enabled"] = False
                    break
            
            # Salvar a configuração atualizada
            try:
                with open(mpc_communication._agent_config_file, "w") as f:
                    json.dump(mpc_communication.config, f, indent=4)
                print(f"Agente '{args.agent_id}' desativado com sucesso!")
            except Exception as e:
                logger.error(f"Erro ao salvar configuração: {e}")
                return 1
    
    return 0

def main():
    parser = setup_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        return asyncio.run(run_command(args))
    except KeyboardInterrupt:
        logger.info("Operação cancelada pelo usuário")
        return 1
    except Exception as e:
        logger.error(f"Erro durante a execução: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
