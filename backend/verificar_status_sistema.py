"""
Script para verificar o status geral do sistema (New Relic e automações MPC)
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from tabulate import tabulate as tabulate_func

# Adicionar o diretório pai ao PATH para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger_config import setup_logger
from utils.newrelic_plan_checker import plan_checker, is_free_plan

# Configurar logger
logger = setup_logger('status_sistema')

async def verificar_status_geral():
    logger.info("Verificando status geral do sistema...")
    
    # Verificar o plano do New Relic
    await plan_checker.check_plan_status()
    plano_tipo = "Free (Gratuito)" if is_free_plan() else "Pago"
    logger.info(f"Plano New Relic atual: {plano_tipo}")
    plano_info = plan_checker.get_settings()
    
    # Verificar se os scripts necessários existem
    scripts = {
        "agentes_newrelic": os.path.join(os.path.dirname(os.path.abspath(__file__)), "verificar_agentes_newrelic.py"),
        "automacoes_mpc": os.path.join(os.path.dirname(os.path.abspath(__file__)), "verificar_automacoes_mpc.py")
    }
    
    for script_name, script_path in scripts.items():
        if not os.path.exists(script_path):
            logger.error(f"Script {script_name} não encontrado em: {script_path}")
            return False
    
    # Executar verificação dos agentes New Relic
    logger.info("Executando verificação dos agentes New Relic...")
    agentes_result = None
    try:
        import subprocess
        result = subprocess.run([sys.executable, scripts["agentes_newrelic"]], 
                               capture_output=True, text=True, check=False)
        logger.info(f"Resultado da verificação dos agentes New Relic: {result.returncode}")
        agentes_status = "✅ Ativo" if result.returncode == 0 else "❌ Inativo"
        agentes_result = result.stdout
    except Exception as e:
        logger.error(f"Erro ao verificar agentes New Relic: {e}")
        agentes_status = "❌ Erro"
    
    # Executar verificação das automações MPC
    logger.info("Executando verificação das automações MPC...")
    mpc_data = None
    try:
        result = subprocess.run([sys.executable, scripts["automacoes_mpc"]], 
                               capture_output=True, text=True, check=False)
        logger.info(f"Resultado da verificação das automações MPC: {result.returncode}")
        
        # Tentar extrair o JSON da saída
        try:
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if line.strip().startswith('{') and line.strip().endswith('}'):
                    mpc_data = json.loads(line)
                    break
            
            if not mpc_data:
                # Tentar extrair de outra forma
                import re
                json_match = re.search(r'(\{.*\})', result.stdout, re.DOTALL)
                if json_match:
                    mpc_data = json.loads(json_match.group(1))
        except Exception as e:
            logger.error(f"Erro ao processar saída JSON das automações MPC: {e}")
        
        if mpc_data:
            mpc_status = "✅ Ativo" if mpc_data.get("status_geral") == "ativo" else "❌ Inativo"
        else:
            mpc_status = "❌ Erro"
    except Exception as e:
        logger.error(f"Erro ao verificar automações MPC: {e}")
        mpc_status = "❌ Erro"
    
    # Verificar processos relevantes em execução
    processos = []
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                cmdline_str = ' '.join([str(cmd) for cmd in cmdline if cmd])
                
                # Verificar se o processo está relacionado ao nosso sistema
                if any(keyword in cmdline_str.lower() for keyword in ['newrelic', 'mcp', 'analyst_ia', 'core_router']):
                    processos.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmd': cmdline_str[:50] + ('...' if len(cmdline_str) > 50 else '')
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        logger.error(f"Erro ao verificar processos: {e}")
    
    # Preparar relatório
    status_report = {
        "timestamp": datetime.now().isoformat(),
        "new_relic_plan": {
            "tipo": plano_tipo,
            "detalhes": plano_info
        },
        "agentes_newrelic": {
            "status": agentes_status,
            "detalhes": agentes_result
        },
        "automacoes_mpc": {
            "status": mpc_status,
            "detalhes": mpc_data
        },
        "processos_relevantes": processos
    }
    
    # Salvar relatório
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status_sistema.json")
    with open(report_path, "w") as f:
        json.dump(status_report, f, indent=2)
    
    # Exibir tabela com resumo
    print("\n" + "=" * 80)
    print("STATUS DO SISTEMA ANALYST IA")
    print("=" * 80)
    
    tabela_status = [
        ["Componente", "Status", "Detalhes"],
        ["Plano New Relic", plano_tipo, f"Limite: {plano_info.get('max_data_ingest_gb', 'N/A')} GB/mês"],
        ["Agentes New Relic", agentes_status, "Verificar logs para detalhes"],
        ["Automações MPC", mpc_status, "Verificar status_automacoes_mpc.json para detalhes"]
    ]
    
    print(tabulate_func(tabela_status, headers="firstrow", tablefmt="grid"))
    
    print("\nProcessos Relevantes em Execução:")
    if processos:
        tabela_processos = [["PID", "Nome", "Comando"]]
        for p in processos:
            tabela_processos.append([p['pid'], p['name'], p['cmd']])
        print(tabulate_func(tabela_processos, headers="firstrow", tablefmt="grid"))
    else:
        print("Nenhum processo relacionado ao sistema encontrado em execução.")
    
    print(f"\nRelatório completo salvo em: {report_path}")
    print("=" * 80)
    
    logger.info(f"Status geral do sistema verificado e salvo em: {report_path}")
    return True

if __name__ == "__main__":
    try:
        from tabulate import tabulate as tabulate_test
    except ImportError:
        print("Instalando dependência tabulate...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate"])
        from tabulate import tabulate as tabulate_test
    
    try:
        import psutil
    except ImportError:
        print("Instalando dependência psutil...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
    
    success = asyncio.run(verificar_status_geral())
    sys.exit(0 if success else 1)
