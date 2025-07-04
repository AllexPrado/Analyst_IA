"""
Script para diagnosticar e corrigir problemas com a integração do New Relic
"""
import os
import sys
import json
import socket
import requests
import logging
import subprocess
from pathlib import Path
from dotenv import load_dotenv, set_key

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def verificar_credenciais():
    """Verificar se as credenciais do New Relic estão configuradas"""
    load_dotenv()
    
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
    api_key = os.getenv('NEW_RELIC_API_KEY')
    query_key = os.getenv('NEW_RELIC_QUERY_KEY')
    
    issues = []
    
    if not account_id:
        issues.append("NEW_RELIC_ACCOUNT_ID não configurado")
    
    if not api_key:
        issues.append("NEW_RELIC_API_KEY não configurado")
        
    if not query_key:
        issues.append("NEW_RELIC_QUERY_KEY não configurado")
    
    if issues:
        logger.warning("❌ Problemas de credenciais detectados:")
        for issue in issues:
            logger.warning(f"  - {issue}")
        return False
    else:
        logger.info("✅ Credenciais configuradas corretamente")
        return True

def verificar_conectividade_dns():
    """Verificar se é possível resolver os domínios do New Relic"""
    dominios = [
        'api.newrelic.com',
        'insights-api.newrelic.com',
        'one.newrelic.com'
    ]
    
    logger.info("Verificando resolução DNS para domínios do New Relic...")
    
    falhas = []
    for dominio in dominios:
        try:
            ip = socket.gethostbyname(dominio)
            logger.info(f"✅ {dominio} -> {ip}")
        except socket.gaierror:
            logger.error(f"❌ Não foi possível resolver o domínio {dominio}")
            falhas.append(dominio)
    
    if falhas:
        return False
    
    return True

def verificar_conectividade_api():
    """Verificar se é possível conectar à API do New Relic"""
    load_dotenv()
    
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
    api_key = os.getenv('NEW_RELIC_API_KEY')
    
    if not account_id or not api_key:
        logger.error("❌ Credenciais não configuradas")
        return False
    
    try:
        url = "https://api.newrelic.com/graphql"
        headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }
        query = """
        {
          actor {
            user {
              email
              name
            }
          }
        }
        """
        
        response = requests.post(url, json={"query": query}, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                logger.error(f"❌ Erro na API: {data['errors']}")
                return False
                
            if "data" in data and "actor" in data["data"]:
                user = data["data"]["actor"].get("user", {})
                name = user.get("name", "Usuário")
                email = user.get("email", "")
                
                logger.info(f"✅ Conectado à API como {name} ({email})")
                return True
            else:
                logger.error("❌ Resposta da API não contém dados do usuário")
                return False
        else:
            logger.error(f"❌ Falha na conexão: Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao conectar à API: {str(e)}")
        return False

def configurar_dados_simulados(usar_simulados=True):
    """Configura o sistema para usar dados simulados ou reais"""
    env_path = Path(".env")
    
    if env_path.exists():
        load_dotenv()
        valor_atual = os.getenv('USE_SIMULATED_DATA', 'true').lower() == 'true'
        
        if valor_atual != usar_simulados:
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            with open(env_path, 'w') as f:
                for line in lines:
                    if line.startswith('USE_SIMULATED_DATA='):
                        f.write(f'USE_SIMULATED_DATA={"true" if usar_simulados else "false"}\n')
                    else:
                        f.write(line)
            
            logger.info(f"✅ Sistema configurado para usar dados {'simulados' if usar_simulados else 'reais'}")
        else:
            logger.info(f"✓ Sistema já configurado para usar dados {'simulados' if usar_simulados else 'reais'}")
    else:
        logger.error("❌ Arquivo .env não encontrado")

def corrigir_consultas_newrelic():
    """Executa o script para corrigir consultas do New Relic"""
    script_path = Path("corrigir_consultas_newrelic.py")
    
    if script_path.exists():
        logger.info("Corrigindo consultas do New Relic...")
        try:
            subprocess.run(["python", str(script_path)], check=True)
            logger.info("✅ Consultas corrigidas com sucesso")
            return True
        except subprocess.CalledProcessError:
            logger.error("❌ Erro ao corrigir consultas")
            return False
    else:
        logger.warning("⚠️ Script corrigir_consultas_newrelic.py não encontrado")
        return False

def main():
    logger.info("=== Diagnóstico do New Relic ===")
    
    credenciais_ok = verificar_credenciais()
    dns_ok = verificar_conectividade_dns()
    
    # Se não conseguir resolver os domínios, não adianta testar a API
    if not dns_ok:
        logger.error("❌ Problemas de DNS detectados. Verificar conexão com a internet.")
        logger.info("⚠️ Configurando sistema para usar dados simulados.")
        configurar_dados_simulados(True)
        return False
    
    api_ok = verificar_conectividade_api()
    
    # Corrigir consultas independentemente da conectividade
    corrigir_consultas_newrelic()
    
    if not credenciais_ok or not api_ok:
        logger.warning("⚠️ Problemas na integração com New Relic detectados.")
        logger.info("⚠️ Configurando sistema para usar dados simulados.")
        configurar_dados_simulados(True)
        return False
    
    logger.info("✅ Integração com New Relic verificada com sucesso!")
    logger.info("✅ Configurando sistema para usar dados reais.")
    configurar_dados_simulados(False)
    return True

if __name__ == "__main__":
    status_ok = main()
    sys.exit(0 if status_ok else 1)
