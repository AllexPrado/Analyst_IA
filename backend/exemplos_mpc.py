"""
Exemplos de Comunicação com Agentes MPC

Este script demonstra diferentes formas de se comunicar com os agentes MPC,
incluindo envio de comandos, broadcast e verificação de status.
"""

import asyncio
import logging
import json
import sys
import os
from datetime import datetime

# Adicionar o diretório principal ao PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mpc_exemplos")

# Importar o módulo de comunicação
try:
    from core_inteligente.mpc_agent_communication import (
        send_agent_command,
        broadcast_to_agents,
        get_agent_status,
        get_agent_history
    )
except ImportError as e:
    logger.error(f"Erro ao importar módulo de comunicação MPC: {e}")
    sys.exit(1)

async def exemplo_diagnostico_sistema():
    """Exemplo de diagnóstico do sistema usando o agente de diagnóstico"""
    logger.info("Executando diagnóstico do sistema...")
    
    response = await send_agent_command(
        agent_id="diagnostico",
        action="run_diagnostic",
        parameters={
            "scope": "full",
            "include_metrics": True,
            "include_logs": True
        },
        context={
            "urgency": "high",
            "triggered_by": "exemplo_script"
        }
    )
    
    if response.status == "success":
        logger.info("Diagnóstico concluído com sucesso!")
        logger.info(f"Resultado: {json.dumps(response.data, indent=2) if response.data else 'Nenhum dado retornado'}")
    else:
        logger.error(f"Erro no diagnóstico: {response.error_message}")
    
    return response

async def exemplo_correcao_automatica():
    """Exemplo de correção automática usando o agente de correção"""
    logger.info("Iniciando correção automática...")
    
    response = await send_agent_command(
        agent_id="correcao",
        action="fix_issues",
        parameters={
            "auto_apply": True,
            "max_issues": 10
        }
    )
    
    if response.status == "success":
        logger.info("Correção automática concluída!")
        issues_fixed = response.data.get("issues_fixed", []) if response.data else []
        logger.info(f"Problemas corrigidos: {len(issues_fixed)}")
        for issue in issues_fixed:
            logger.info(f"  - {issue}")
    else:
        logger.error(f"Erro na correção automática: {response.error_message}")
    
    return response

async def exemplo_verificacao_seguranca():
    """Exemplo de verificação de segurança usando o agente de segurança"""
    logger.info("Iniciando verificação de segurança...")
    
    response = await send_agent_command(
        agent_id="seguranca",
        action="security_audit",
        parameters={
            "scan_depth": "deep",
            "include_dependencies": True
        }
    )
    
    if response.status == "success":
        logger.info("Verificação de segurança concluída!")
        vulnerabilities = response.data.get("vulnerabilities", []) if response.data else []
        logger.info(f"Vulnerabilidades encontradas: {len(vulnerabilities)}")
        for vuln in vulnerabilities:
            logger.info(f"  - {vuln.get('severity', 'Unknown')}: {vuln.get('description', 'No description')}")
    else:
        logger.error(f"Erro na verificação de segurança: {response.error_message}")
    
    return response

async def exemplo_broadcast_status():
    """Exemplo de broadcast para todos os agentes"""
    logger.info("Enviando comando de status para todos os agentes...")
    
    responses = await broadcast_to_agents(
        action="get_health",
        parameters={"detailed": True}
    )
    
    logger.info(f"Respostas recebidas de {len(responses)} agentes:")
    for agent_id, response in responses.items():
        status_text = "OK" if response.status == "success" else f"ERRO: {response.error_message}"
        logger.info(f"  - {agent_id}: {status_text}")
    
    return responses

async def exemplo_otimizacao():
    """Exemplo de otimização usando o agente de otimização"""
    logger.info("Iniciando otimização do sistema...")
    
    response = await send_agent_command(
        agent_id="otimizacao",
        action="optimize_system",
        parameters={
            "target_areas": ["cache", "database", "endpoints"],
            "aggressive_mode": False
        }
    )
    
    if response.status == "success":
        logger.info("Otimização concluída com sucesso!")
        improvements = response.data.get("improvements", []) if response.data else []
        logger.info(f"Melhorias aplicadas: {len(improvements)}")
        for improvement in improvements:
            logger.info(f"  - {improvement}")
    else:
        logger.error(f"Erro na otimização: {response.error_message}")
    
    return response

async def exemplo_coleta_metricas():
    """Exemplo de coleta de métricas usando o agente de coleta"""
    logger.info("Iniciando coleta de métricas...")
    
    response = await send_agent_command(
        agent_id="coleta",
        action="collect_metrics",
        parameters={
            "metrics": ["cpu", "memory", "disk", "network"],
            "duration": 60  # segundos
        }
    )
    
    if response.status == "success":
        logger.info("Coleta de métricas concluída com sucesso!")
        metrics = response.data.get("metrics", {}) if response.data else {}
        for metric_name, metric_value in metrics.items():
            logger.info(f"  - {metric_name}: {metric_value}")
    else:
        logger.error(f"Erro na coleta de métricas: {response.error_message}")
    
    return response

async def exemplo_verificar_historico():
    """Exemplo de verificação do histórico de comunicações"""
    logger.info("Verificando histórico de comunicações...")
    
    # Obter histórico de todos os agentes (últimas 5 comunicações)
    all_history = get_agent_history(limit=5)
    logger.info(f"Últimas {len(all_history)} comunicações com todos os agentes:")
    for entry in all_history:
        timestamp = entry.get("timestamp", "Unknown")
        agent_id = entry.get("request", {}).get("agent_id", "Unknown")
        action = entry.get("request", {}).get("action", "Unknown")
        status = entry.get("response", {}).get("status", "Unknown")
        logger.info(f"  - {timestamp}: {agent_id} / {action} → {status}")
    
    # Obter histórico específico do agente de diagnóstico
    diag_history = get_agent_history(agent_id="diagnostico", limit=3)
    logger.info(f"Últimas {len(diag_history)} comunicações com o agente de diagnóstico:")
    for entry in diag_history:
        timestamp = entry.get("timestamp", "Unknown")
        action = entry.get("request", {}).get("action", "Unknown")
        status = entry.get("response", {}).get("status", "Unknown")
        logger.info(f"  - {timestamp}: {action} → {status}")

async def main():
    """Função principal que demonstra todos os exemplos"""
    logger.info("=== Iniciando Exemplos de Comunicação MPC ===")
    
    # Verificar status de todos os agentes
    logger.info("\n=== Verificando Status dos Agentes ===")
    all_status = await get_agent_status()
    logger.info(f"Status: {json.dumps(all_status, indent=2)}")
    
    # Exemplos com agentes individuais
    logger.info("\n=== Exemplo de Diagnóstico ===")
    await exemplo_diagnostico_sistema()
    
    logger.info("\n=== Exemplo de Correção Automática ===")
    await exemplo_correcao_automatica()
    
    logger.info("\n=== Exemplo de Verificação de Segurança ===")
    await exemplo_verificacao_seguranca()
    
    logger.info("\n=== Exemplo de Otimização ===")
    await exemplo_otimizacao()
    
    logger.info("\n=== Exemplo de Coleta de Métricas ===")
    await exemplo_coleta_metricas()
    
    # Broadcast para todos os agentes
    logger.info("\n=== Exemplo de Broadcast ===")
    await exemplo_broadcast_status()
    
    # Verificar histórico
    logger.info("\n=== Exemplo de Verificação de Histórico ===")
    await exemplo_verificar_historico()
    
    logger.info("\n=== Exemplos Concluídos ===")

if __name__ == "__main__":
    try:
        # Executar todos os exemplos
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Execução interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro durante a execução: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
