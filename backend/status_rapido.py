"""
Script simples para verificar o status dos agentes New Relic e automações MPC
"""

import os
import sys
import json
from datetime import datetime
import subprocess
import re

def check_newrelic_agents():
    """Verifica o status dos agentes New Relic de forma simples"""
    print("\n=== Status dos Agentes New Relic ===\n")
    
    # 1. Verificar se as chaves da API estão configuradas
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    api_key_found = False
    account_id_found = False
    
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                env_content = f.read()
                api_key_found = "NEW_RELIC_API_KEY" in env_content
                account_id_found = "NEW_RELIC_ACCOUNT_ID" in env_content
        except Exception:
            pass
    
    if api_key_found and account_id_found:
        print("✅ Chaves de API New Relic encontradas no arquivo .env")
    else:
        print("❌ Chaves de API New Relic NÃO encontradas no arquivo .env")
        if not api_key_found:
            print("   - NEW_RELIC_API_KEY está faltando")
        if not account_id_found:
            print("   - NEW_RELIC_ACCOUNT_ID está faltando")
    
    # 2. Verificar se o arquivo de coletor existe
    collector_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "utils", "newrelic_collector.py")
    if os.path.exists(collector_path):
        print("✅ Arquivo do coletor New Relic encontrado")
        
        # Verificar se o método de coleta de dependências está implementado
        try:
            with open(collector_path, 'r') as f:
                collector_content = f.read()
                if "async def collect_entity_dependencies" in collector_content:
                    print("✅ Método collect_entity_dependencies implementado")
                else:
                    print("❌ Método collect_entity_dependencies NÃO implementado")
        except Exception:
            print("❌ Não foi possível ler o arquivo do coletor")
    else:
        print("❌ Arquivo do coletor New Relic NÃO encontrado")
    
    # 3. Verificar processos relacionados ao New Relic
    try:
        import psutil
        newrelic_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                cmdline_str = ' '.join([str(cmd) for cmd in cmdline if cmd])
                if 'newrelic' in cmdline_str.lower():
                    newrelic_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmd': cmdline_str
                    })
            except:
                pass
        
        if newrelic_processes:
            print(f"✅ {len(newrelic_processes)} processos relacionados ao New Relic encontrados")
            for proc in newrelic_processes:
                print(f"   - PID: {proc['pid']}, Nome: {proc['name']}")
        else:
            print("ℹ️ Nenhum processo explicitamente relacionado ao New Relic encontrado")
            print("   (Isso é normal se os agentes estiverem incorporados em outros processos)")
    except ImportError:
        print("ℹ️ Não foi possível verificar processos (biblioteca psutil não encontrada)")

def check_mpc_automations():
    """Verifica o status das automações MPC de forma simples"""
    print("\n=== Status das Automações MPC ===\n")
    
    # 1. Verificar se os arquivos principais do MPC existem
    core_router_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core_router.py")
    if os.path.exists(core_router_path):
        print("✅ Arquivo core_router.py encontrado")
    else:
        print("❌ Arquivo core_router.py NÃO encontrado")
    
    # 2. Verificar se há arquivos de configuração MPC
    config_files = []
    for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
        for file in files:
            if file.endswith('.json') and ('config' in file.lower() or 'mpc' in file.lower()):
                config_files.append(os.path.join(root, file))
    
    if config_files:
        print(f"✅ {len(config_files)} arquivos de configuração MPC encontrados")
        for config_file in config_files[:3]:  # Mostrar apenas os 3 primeiros
            print(f"   - {os.path.basename(config_file)}")
        if len(config_files) > 3:
            print(f"   - ... e mais {len(config_files) - 3} arquivo(s)")
    else:
        print("❌ Nenhum arquivo de configuração MPC encontrado")
    
    # 3. Verificar processos relacionados ao MPC
    try:
        import psutil
        mpc_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                cmdline_str = ' '.join([str(cmd) for cmd in cmdline if cmd])
                if 'mpc' in cmdline_str.lower() or 'core_router' in cmdline_str.lower():
                    mpc_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmd': cmdline_str
                    })
            except:
                pass
        
        if mpc_processes:
            print(f"✅ {len(mpc_processes)} processos relacionados ao MPC encontrados")
            for proc in mpc_processes:
                print(f"   - PID: {proc['pid']}, Nome: {proc['name']}")
        else:
            print("❌ Nenhum processo relacionado ao MPC encontrado")
    except ImportError:
        print("ℹ️ Não foi possível verificar processos (biblioteca psutil não encontrada)")

def main():
    print("\n==================================================")
    print("         VERIFICAÇÃO RÁPIDA DO SISTEMA")
    print("==================================================")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("==================================================")
    
    check_newrelic_agents()
    check_mpc_automations()
    
    print("\n==================================================")
    print("         RESUMO DO STATUS DO SISTEMA")
    print("==================================================")
    
    # Verificar se o sistema unificado está em execução
    try:
        import psutil
        unified_running = False
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                cmdline_str = ' '.join([str(cmd) for cmd in cmdline if cmd])
                if 'start_unified.py' in cmdline_str or 'unified_backend.py' in cmdline_str:
                    unified_running = True
                    break
            except:
                pass
        
        if unified_running:
            print("✅ Sistema unificado está em execução")
        else:
            print("❌ Sistema unificado NÃO está em execução")
            print("\nPara iniciar o sistema completo, execute:")
            print("   python start_unified.py")
    except ImportError:
        print("ℹ️ Não foi possível verificar se o sistema está em execução")
    
    print("\n==================================================")
    print(" Para detalhes completos, execute os scripts:")
    print("   - python verificar_agentes_newrelic.py")
    print("   - python verificar_automacoes_mpc.py")
    print("   - python verificar_status_sistema.py")
    print("==================================================\n")

if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        try:
            print("Instalando biblioteca psutil...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
            import psutil
        except:
            print("Não foi possível instalar a biblioteca psutil. Continuando sem verificação de processos.")
    
    main()
