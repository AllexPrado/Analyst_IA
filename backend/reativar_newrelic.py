"""
Script para reativar o New Relic quando o limite mensal for resetado.
Este script reverte as alterações feitas pelo script de emergência e configura
monitoramento otimizado para não exceder o limite de 100 GB novamente.
"""

import os
import sys
import json
import logging
from datetime import datetime
import subprocess
import argparse
import shutil

# Adicionar o diretório pai ao PATH para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger_config import setup_logger
import asyncio

# Configurar logger
logger = setup_logger('reativar_newrelic')

async def verificar_disponibilidade():
    """Verifica se o New Relic já está disponível novamente"""
    try:
        # Importar verificador de disponibilidade
        from verificar_newrelic_disponibilidade import verificar_status_newrelic
        
        status = await verificar_status_newrelic()
        if status["status"] == "disponivel":
            logger.info("New Relic está disponível!")
            return True
        else:
            logger.warning(f"New Relic ainda não está disponível: {status['mensagem']}")
            return False
    except Exception as e:
        logger.error(f"Erro ao verificar disponibilidade: {e}")
        return False

def remover_flags_emergencia():
    """Remove os arquivos e flags criados durante a emergência"""
    logger.info("Removendo flags de emergência...")
    
    flags = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "NEWRELIC_DISABLED"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "emergency_mode.json")
    ]
    
    for flag in flags:
        if os.path.exists(flag):
            try:
                os.remove(flag)
                logger.info(f"Flag removida: {flag}")
            except Exception as e:
                logger.error(f"Erro ao remover flag {flag}: {e}")

def atualizar_env_config():
    """Atualiza o arquivo .env removendo configurações de emergência"""
    logger.info("Atualizando arquivo .env...")
    
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            # Fazer backup do arquivo .env
            backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "cache", f"env_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(env_path, backup_path)
            
            # Ler conteúdo atual
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Filtrar linhas com configurações de emergência
            updated_lines = []
            for line in lines:
                if not any(emergency in line for emergency in [
                    "NEWRELIC_OFFLINE_MODE=", 
                    "FORCE_CACHE_ONLY=", 
                    "# Configuração de emergência"
                ]):
                    updated_lines.append(line)
            
            # Gravar arquivo atualizado
            with open(env_path, 'w') as f:
                f.writelines(updated_lines)
            
            logger.info(f"Arquivo .env atualizado. Backup em {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar .env: {e}")
            return False
    else:
        logger.warning("Arquivo .env não encontrado")
        return False

def configurar_modo_otimizado():
    """Configura o New Relic para modo otimizado para não exceder limites"""
    logger.info("Configurando modo otimizado...")
    
    try:
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
        os.makedirs(config_dir, exist_ok=True)
        
        config_path = os.path.join(config_dir, "newrelic_optimized.json")
        
        config = {
            "modo": "otimizado",
            "timestamp": datetime.now().isoformat(),
            "configuracao": {
                "cache_ttl_hours": 48,  # Cache mais longo para reduzir chamadas
                "disable_browser_monitoring": True,  # Desativar monitoramento de browser
                "max_entities": 20,  # Limitar número de entidades monitoradas
                "sampling_rate": 0.2,  # Amostragem de 20% dos logs
                "metrics_interval_seconds": 60,  # 1 minuto entre coletas de métricas
                "use_compression": True,  # Comprimir dados enviados
                "alerts_only_critical": True,  # Apenas alertas críticos
                "data_retention_days": 7,  # Retenção de dados por 7 dias
                "max_attributes_per_event": 16  # Limitar atributos por evento
            },
            "limites": {
                "max_gb_per_day": 3.3,  # ~100 GB / 30 dias
                "max_api_calls_per_minute": 10,
                "max_queries_per_minute": 5
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuração otimizada salva em {config_path}")
        return True
    except Exception as e:
        logger.error(f"Erro ao configurar modo otimizado: {e}")
        return False

def iniciar_agentes():
    """Inicia os agentes do New Relic"""
    logger.info("Iniciando agentes New Relic...")
    
    try:
        # Em sistemas Windows, verifique e inicie o serviço
        if os.name == 'nt':
            subprocess.run(["sc", "start", "newrelic-infra"], 
                          capture_output=True, check=False)
        else:
            # Em sistemas Linux
            subprocess.run(["systemctl", "start", "newrelic-infra"], 
                          capture_output=True, check=False)
        
        # Iniciar coleta otimizada
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                                  "otimizar_coleta_newrelic.py")], 
                      check=False)
        
        logger.info("Agentes New Relic iniciados")
        return True
    except Exception as e:
        logger.error(f"Erro ao iniciar agentes: {e}")
        return False

async def reativar_newrelic(modo_otimizado=True, forcar=False):
    """Reativa o New Relic após o limite ter sido excedido"""
    logger.info(f"Iniciando reativação do New Relic (Modo otimizado: {modo_otimizado}, Forçar: {forcar})")
    
    if not forcar:
        # Verificar se o New Relic está disponível
        disponivel = await verificar_disponibilidade()
        if not disponivel:
            logger.error("New Relic ainda não está disponível. Use --force para forçar a reativação.")
            return False
    
    # Remover flags de emergência
    remover_flags_emergencia()
    
    # Atualizar arquivo .env
    atualizar_env_config()
    
    # Configurar modo otimizado se solicitado
    if modo_otimizado:
        configurar_modo_otimizado()
    
    # Iniciar agentes
    iniciar_agentes()
    
    logger.info("New Relic reativado com sucesso!")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reativar o New Relic após exceder limite")
    parser.add_argument("--otimizado", action="store_true", help="Reativar em modo otimizado")
    parser.add_argument("--force", action="store_true", help="Forçar reativação mesmo se não estiver disponível")
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("REATIVAÇÃO DO NEW RELIC")
    print("=" * 80)
    
    resultado = asyncio.run(reativar_newrelic(args.otimizado, args.force))
    
    if resultado:
        print("\nNew Relic reativado com sucesso!")
        if args.otimizado:
            print("\nModo otimizado configurado para evitar exceder limite de 100 GB:")
            print("- Cache estendido para 48h")
            print("- Monitoramento de browser desativado")
            print("- Número limitado de entidades monitoradas")
            print("- Amostragem de logs em 20%")
    else:
        print("\nFalha ao reativar o New Relic. Verifique os logs para mais detalhes.")
        print("Você pode forçar a reativação com: python reativar_newrelic.py --force")
    
    print("\nPróximos passos:")
    print("1. Execute 'python verificar_status_sistema.py' para confirmar status")
    print("2. Monitore regularmente o uso com 'python otimizar_coleta_newrelic.py'")
    print("3. Continue usando o monitoramento local como backup")
    
    print("=" * 80)
    
    sys.exit(0 if resultado else 1)
