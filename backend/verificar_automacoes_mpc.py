"""
Script para verificar o status das automações MPC (Model Context Protocol)
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
import json

# Adicionar o diretório pai ao PATH para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger_config import setup_logger

# Configurar logger
logger = setup_logger('verificar_automacoes_mpc')

# Caminho para o arquivo de status das automações MPC
STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status_automacoes_mpc.json")

async def verificar_automacoes_mpc():
    try:
        # Verificar se o core_router.py está ativo (parte central do MPC)
        logger.info("Verificando se o core_router do MPC está ativo...")
        
        # Verificar se há arquivos de configuração MPC
        config_files = []
        for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
            for file in files:
                if file.endswith('.json') and ('config' in file.lower() or 'mpc' in file.lower()):
                    config_files.append(os.path.join(root, file))
        
        if not config_files:
            logger.warning("Nenhum arquivo de configuração MPC encontrado")
        else:
            logger.info(f"Encontrados {len(config_files)} arquivos de configuração MPC")
            for config_file in config_files:
                logger.info(f"  - {os.path.basename(config_file)}")
        
        # Verificar processos relacionados ao MPC
        import psutil
        mpc_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                    
                cmdline_str = ' '.join([str(cmd) for cmd in cmdline if cmd])
                if 'mcp' in cmdline_str.lower() or 'model context protocol' in cmdline_str.lower() or 'core_router.py' in cmdline_str:
                    mpc_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if not mpc_processes:
            logger.warning("Nenhum processo MPC encontrado em execução")
        else:
            logger.info(f"Encontrados {len(mpc_processes)} processos MPC em execução")
            for proc in mpc_processes:
                logger.info(f"  - PID: {proc['pid']}, Nome: {proc['name']}")
        
        # Verificar integrações com New Relic (componente importante para automações)
        logger.info("Verificando integrações com New Relic...")
        newrelic_integration = False
        
        try:
            # Verificar se o módulo core_router existe e tem referências ao New Relic
            if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "core_router.py")):
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "core_router.py"), "r") as f:
                    core_router_content = f.read()
                    if "newrelic" in core_router_content.lower():
                        newrelic_integration = True
                        logger.info("✅ Integração com New Relic encontrada no core_router.py")
        except Exception as e:
            logger.error(f"Erro ao verificar integração com New Relic: {e}")
        
        if not newrelic_integration:
            logger.warning("⚠️ Integração com New Relic não encontrada explicitamente")
        
        # Gerar relatório de status
        status = {
            "timestamp": datetime.now().isoformat(),
            "configuracoes_mpc": {
                "encontradas": len(config_files) > 0,
                "quantidade": len(config_files),
                "arquivos": [os.path.basename(f) for f in config_files]
            },
            "processos_mpc": {
                "em_execucao": len(mpc_processes) > 0,
                "quantidade": len(mpc_processes),
                "detalhes": [{"pid": p["pid"], "nome": p["name"]} for p in mpc_processes]
            },
            "integracao_newrelic": newrelic_integration,
            "status_geral": "ativo" if (len(config_files) > 0 and len(mpc_processes) > 0) else "inativo"
        }
        
        # Salvar o status em um arquivo
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f, indent=4)
        
        logger.info(f"Status das automações MPC: {status['status_geral']}")
        logger.info(f"Detalhes salvos em: {STATUS_FILE}")
        
        return status
        
    except Exception as e:
        logger.error(f"Erro ao verificar automações MPC: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status_geral": "erro", "error": str(e)}

if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        logger.error("Biblioteca psutil não encontrada. Instalando...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        logger.info("psutil instalado com sucesso")
        import psutil
    
    status = asyncio.run(verificar_automacoes_mpc())
    print(json.dumps(status, indent=2))
    sys.exit(0 if status["status_geral"] == "ativo" else 1)
