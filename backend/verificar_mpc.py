"""
Script para verificar o status do servidor MPC
"""
import requests
import json
import sys
import os

def verificar_status_mpc(porta=10876):
    """Verifica o status do servidor MPC"""
    url = f"http://localhost:{porta}/agent/status"
    
    print(f"Verificando servidor MPC na porta {porta}...")
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Servidor MPC está rodando na porta {porta}")
            
            # Mostrar status de cada agente
            print("\nStatus dos agentes:")
            print("-" * 60)
            
            data = response.json()
            for agente, info in data.items():
                status = info.get("status", "desconhecido")
                saude = info.get("saúde", 0)
                ultima_atividade = info.get("última_atividade", "N/A")
                
                status_symbol = "✅" if status == "ativo" and saude >= 80 else "⚠️" if status == "ativo" else "❌"
                
                print(f"{status_symbol} {agente.ljust(15)} | Status: {status.ljust(10)} | Saúde: {str(saude).ljust(3)}% | Última atividade: {ultima_atividade}")
            
            print("-" * 60)
            return True
        else:
            print(f"❌ Servidor MPC retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Não foi possível conectar ao servidor MPC na porta {porta}")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar servidor MPC: {e}")
        return False

def verificar_config_mpc():
    """Verifica o arquivo de configuração do MPC"""
    config_path = os.path.join("config", "mpc_agents.json")
    
    print("\nVerificando arquivo de configuração do MPC...")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                
            base_url = config.get("base_url", "")
            print(f"✅ Arquivo de configuração encontrado: {config_path}")
            print(f"   URL base configurada: {base_url}")
            
            # Extrair porta da URL base
            try:
                port = int(base_url.split(":")[2].split("/")[0])
                print(f"   Porta configurada: {port}")
                return port
            except:
                print("❌ Não foi possível extrair a porta da URL base")
                return 10876
        except Exception as e:
            print(f"❌ Erro ao ler arquivo de configuração: {e}")
            return 10876
    else:
        print(f"❌ Arquivo de configuração não encontrado: {config_path}")
        return 10876

if __name__ == "__main__":
    # Verificar configuração
    porta_config = verificar_config_mpc()
    
    # Verificar status na porta configurada
    if not verificar_status_mpc(porta_config):
        print("\nTentando porta alternativa (10876)...")
        verificar_status_mpc(10876)
