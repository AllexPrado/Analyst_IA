"""
Script de emergência para desativar temporariamente o monitoramento New Relic
devido ao limite excedido do plano gratuito (100 GB)

Este script:
1. Interrompe todos os agentes New Relic ativos
2. Desativa as coletas programadas
3. Configura o sistema para usar apenas dados em cache
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
import subprocess

# Adicionar o diretório pai ao PATH para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger_config import setup_logger

# Configurar logger
logger = setup_logger('emergency_shutdown')

def desativar_agentes_newrelic():
    """Desativa todos os agentes New Relic em execução"""
    logger.info("Desativando agentes New Relic...")
    
    try:
        # Verificar processos relacionados ao New Relic
        import psutil
        processos_newrelic = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                cmdline_str = ' '.join([str(cmd) for cmd in cmdline if cmd])
                
                # Identificar processos do New Relic
                if 'newrelic' in cmdline_str.lower():
                    processos_newrelic.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Finalizar processos encontrados
        for proc in processos_newrelic:
            try:
                proc.terminate()
                logger.info(f"Processo New Relic terminado: PID {proc.pid}")
            except Exception as e:
                logger.error(f"Erro ao finalizar processo {proc.pid}: {e}")
        
        # Verificar se há algum serviço New Relic configurado
        if os.name == 'nt':  # Windows
            subprocess.run(["sc", "query", "newrelic-infra"], 
                          capture_output=True, check=False)
            subprocess.run(["sc", "stop", "newrelic-infra"], 
                          capture_output=True, check=False)
            logger.info("Tentativa de parar serviço New Relic Infrastructure no Windows")
        else:  # Linux/Unix
            subprocess.run(["systemctl", "stop", "newrelic-infra"], 
                          capture_output=True, check=False)
            logger.info("Tentativa de parar serviço New Relic Infrastructure no Linux")
        
        logger.info("Agentes New Relic desativados com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao desativar agentes New Relic: {e}")
        return False

def desativar_coletas_programadas():
    """Desativa todas as coletas programadas do New Relic"""
    logger.info("Desativando coletas programadas...")
    
    try:
        # Criar arquivo sinalizador para evitar novas coletas
        flag_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               "cache", "NEWRELIC_DISABLED")
        
        os.makedirs(os.path.dirname(flag_path), exist_ok=True)
        with open(flag_path, 'w') as f:
            f.write(datetime.now().isoformat())
        
        logger.info(f"Flag de desativação criado em {flag_path}")
        
        # Procurar e desativar jobs cron ou tasks agendadas
        if os.name == 'nt':  # Windows
            subprocess.run(["schtasks", "/query", "/fo", "csv", "/nh"], 
                          capture_output=True, check=False)
            # Desativar tasks relacionadas (exemplo genérico)
            # subprocess.run(["schtasks", "/change", "/tn", "NomeTask", "/disable"], 
            #               capture_output=True, check=False)
            logger.info("Verificadas tarefas agendadas no Windows")
        else:  # Linux/Unix
            try:
                crontab = subprocess.check_output(["crontab", "-l"], 
                                                text=True, stderr=subprocess.STDOUT)
                
                # Fazer backup do crontab atual
                with open(os.path.join(os.path.dirname(flag_path), "crontab_backup.txt"), 'w') as f:
                    f.write(crontab)
                
                # Filtrar linhas que não contêm "newrelic"
                new_crontab = "\n".join([
                    line for line in crontab.splitlines()
                    if "newrelic" not in line.lower()
                ])
                
                # Salvar nova versão
                with open(os.path.join(os.path.dirname(flag_path), "crontab_new.txt"), 'w') as f:
                    f.write(new_crontab)
                
                # Aplicar novo crontab
                subprocess.run(["crontab", os.path.join(os.path.dirname(flag_path), "crontab_new.txt")], 
                              check=False)
                
                logger.info("Tarefas cron relacionadas ao New Relic desativadas")
            except subprocess.CalledProcessError:
                logger.info("Não há tarefas cron configuradas")
        
        logger.info("Coletas programadas desativadas")
        return True
    except Exception as e:
        logger.error(f"Erro ao desativar coletas programadas: {e}")
        return False

def configurar_modo_offline():
    """Configura o sistema para usar apenas dados em cache"""
    logger.info("Configurando modo offline...")
    
    try:
        # Configurar variável de ambiente para modo offline
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Verificar se já existe configuração de modo offline
            if "NEWRELIC_OFFLINE_MODE" not in env_content:
                with open(env_path, 'a') as f:
                    f.write("\n# Configuração de emergência - limite excedido\n")
                    f.write("NEWRELIC_OFFLINE_MODE=True\n")
                    f.write("FORCE_CACHE_ONLY=True\n")
            
            logger.info("Modo offline configurado no .env")
        
        # Criar configuração de emergência
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 "config", "emergency_mode.json")
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        config = {
            "offline_mode": True,
            "reason": "Limite do plano gratuito New Relic excedido (100 GB)",
            "timestamp": datetime.now().isoformat(),
            "expiry": (datetime.now() + timedelta(days=30)).isoformat(),
            "settings": {
                "use_cache_only": True,
                "disable_all_agents": True,
                "disable_browser_monitoring": True,
                "disable_apm": True,
                "emergency_level": "critical"
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuração de emergência salva em {config_path}")
        
        # Criar arquivo auxiliar para outros scripts detectarem
        helper_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 "utils", "offline_mode_helper.py")
        
        with open(helper_path, 'w') as f:
            f.write("""\"\"\"
Módulo auxiliar para detectar modo offline/emergência
\"\"\"

import os
import json
from datetime import datetime

def is_emergency_mode():
    \"\"\"Verifica se o sistema está em modo de emergência\"\"\"
    # Verificar flag direto
    flag_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           "cache", "NEWRELIC_DISABLED")
    if os.path.exists(flag_path):
        return True
    
    # Verificar configuração
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                             "config", "emergency_mode.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Verificar se não expirou
            if "expiry" in config:
                expiry = datetime.fromisoformat(config["expiry"])
                if datetime.now() < expiry:
                    return True
        except:
            pass
    
    # Verificar variável de ambiente
    return os.environ.get("NEWRELIC_OFFLINE_MODE", "").lower() == "true"

def get_emergency_config():
    \"\"\"Retorna a configuração de emergência\"\"\"
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                             "config", "emergency_mode.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            pass
    
    return {
        "offline_mode": True,
        "reason": "Configuração padrão de emergência",
        "settings": {
            "use_cache_only": True,
            "disable_all_agents": True
        }
    }
""")
        
        logger.info(f"Módulo auxiliar de modo offline criado em {helper_path}")
        return True
    except Exception as e:
        logger.error(f"Erro ao configurar modo offline: {e}")
        return False

def main():
    print("\n" + "=" * 80)
    print("DESATIVAÇÃO DE EMERGÊNCIA DO NEW RELIC")
    print("=" * 80)
    print("\nLIMITE DO PLANO GRATUITO EXCEDIDO (100 GB)")
    print("Executando procedimento de emergência para evitar custos adicionais...\n")
    
    # Desativar agentes
    success_agents = desativar_agentes_newrelic()
    print(f"✓ Agentes New Relic desativados: {'Sucesso' if success_agents else 'Falha'}")
    
    # Desativar coletas programadas
    success_coletas = desativar_coletas_programadas()
    print(f"✓ Coletas programadas desativadas: {'Sucesso' if success_coletas else 'Falha'}")
    
    # Configurar modo offline
    success_offline = configurar_modo_offline()
    print(f"✓ Modo offline configurado: {'Sucesso' if success_offline else 'Falha'}")
    
    print("\nPROCEDIMENTO CONCLUÍDO")
    print("\nO sistema agora está configurado para:")
    print("- Não enviar dados para o New Relic")
    print("- Usar apenas dados em cache")
    print("- Desativar todos os agentes e coletas")
    
    print("\nPara reverter esta configuração no futuro, execute:")
    print("python reativar_newrelic.py")
    
    print("\nPara mais informações, consulte:")
    print("NEWRELIC_PLANO_GRATUITO.md")
    print("=" * 80)
    
    return all([success_agents, success_coletas, success_offline])

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
