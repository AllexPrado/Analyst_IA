"""
Script para garantir que o sistema Analyst_IA está usando dados reais do New Relic.
Este script faz as seguintes verificações:
1. Verifica se o arquivo .env tem as credenciais do New Relic
2. Verifica se a conectividade com o New Relic está funcionando
3. Atualiza o indicador de fonte de dados
4. Força a atualização do cache com dados reais
"""
import os
import sys
import json
import logging
import requests
import subprocess
from pathlib import Path
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def verificar_env():
    """Verificar e corrigir arquivo .env"""
    env_path = ".env"
    
    # Verificar se o arquivo existe
    if not Path(env_path).exists():
        logger.warning(f"Arquivo {env_path} não encontrado. Criando...")
        with open(env_path, "w") as f:
            f.write("""# Credenciais do New Relic
NEW_RELIC_API_KEY=your_api_key_here
NEW_RELIC_ACCOUNT_ID=your_account_id_here
NEW_RELIC_QUERY_KEY=your_query_key_here

# Configuração
USE_SIMULATED_DATA=false
""")
        logger.info(f"✅ Arquivo {env_path} criado. Por favor, edite-o com suas credenciais reais.")
        return False
    
    # Ler o arquivo
    with open(env_path, "r") as f:
        linhas = f.readlines()
    
    # Verificar se as credenciais estão configuradas
    credenciais_ok = True
    api_key_found = False
    account_id_found = False
    query_key_found = False
    simulated_data = True
    
    for linha in linhas:
        if linha.startswith("NEW_RELIC_API_KEY="):
            api_key = linha.strip().split("=", 1)[1]
            api_key_found = True
            if api_key == "your_api_key_here" or not api_key:
                credenciais_ok = False
        
        if linha.startswith("NEW_RELIC_ACCOUNT_ID="):
            account_id = linha.strip().split("=", 1)[1]
            account_id_found = True
            if account_id == "your_account_id_here" or not account_id:
                credenciais_ok = False
        
        if linha.startswith("NEW_RELIC_QUERY_KEY="):
            query_key = linha.strip().split("=", 1)[1]
            query_key_found = True
            if query_key == "your_query_key_here" or not query_key:
                credenciais_ok = False
        
        if linha.startswith("USE_SIMULATED_DATA="):
            simulated_data = linha.strip().split("=", 1)[1].lower() == "true"
    
    # Verificar se todas as credenciais foram encontradas
    if not api_key_found or not account_id_found or not query_key_found:
        logger.warning("Arquivo .env não contém todas as credenciais necessárias.")
        credenciais_ok = False
    
    # Corrigir configuração de dados simulados se necessário
    if credenciais_ok and simulated_data:
        logger.info("Configuração USE_SIMULATED_DATA=true encontrada. Alterando para false...")
        
        with open(env_path, "w") as f:
            for linha in linhas:
                if linha.startswith("USE_SIMULATED_DATA="):
                    f.write("USE_SIMULATED_DATA=false\n")
                else:
                    f.write(linha)
        
        logger.info("✅ Configuração de dados simulados alterada para false.")
    
    return credenciais_ok

def verificar_conectividade_new_relic():
    """Verifica se é possível conectar à API do New Relic"""
    logger.info("Verificando conectividade com New Relic...")
    
    # Carregar variáveis de ambiente
    from dotenv import load_dotenv
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
        
        logger.info("Enviando requisição de teste para New Relic...")
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

def atualizar_indicador_dados_reais():
    """Atualiza o indicador de dados reais"""
    logger.info("Atualizando indicador de dados reais...")
    
    indicador_path = "backend/cache/data_source_indicator.json"
    
    # Garantir que o diretório existe
    os.makedirs(os.path.dirname(indicador_path), exist_ok=True)
    
    indicador = {
        "using_real_data": True,
        "timestamp": datetime.now().isoformat(),
        "source": "New Relic API",
        "configured_by": "configurar_dados_reais.py"
    }
    
    with open(indicador_path, "w") as f:
        json.dump(indicador, f, indent=2)
    
    logger.info(f"✅ Indicador de dados reais atualizado em {indicador_path}")
    return True

def forcar_atualizacao_cache():
    """Força a atualização do cache com dados reais"""
    logger.info("Forçando atualização do cache com dados reais...")
    
    try:
        # Verificar se o script existe
        if Path("backend/check_and_fix_cache.py").exists():
            subprocess.run(["python", "backend/check_and_fix_cache.py"], check=True)
            logger.info("✅ Cache atualizado com sucesso.")
            return True
        else:
            logger.error("❌ Script check_and_fix_cache.py não encontrado.")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro ao atualizar cache: {str(e)}")
        return False

def verificar_corrigir_consultas():
    """Verifica e corrige as consultas GraphQL/NRQL com problemas"""
    logger.info("Verificando e corrigindo consultas GraphQL/NRQL...")
    
    try:
        # Verificar se o script existe
        if Path("corrigir_consultas_newrelic.py").exists():
            subprocess.run(["python", "corrigir_consultas_newrelic.py"], check=True)
            logger.info("✅ Consultas corrigidas com sucesso.")
            return True
        else:
            logger.warning("⚠️ Script corrigir_consultas_newrelic.py não encontrado.")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro ao corrigir consultas: {str(e)}")
        return False

def main():
    """Função principal"""
    logger.info("="*50)
    logger.info("Configuração de Dados Reais - Analyst_IA")
    logger.info("="*50)
    
    # 1. Verificar arquivo .env
    logger.info("1. Verificando arquivo .env...")
    env_ok = verificar_env()
    if not env_ok:
        logger.warning("⚠️ Verifique suas credenciais no arquivo .env antes de continuar.")
    
    # 2. Verificar consultas GraphQL/NRQL
    logger.info("\n2. Verificando consultas GraphQL/NRQL...")
    verificar_corrigir_consultas()
    
    # 3. Verificar conectividade com New Relic
    logger.info("\n3. Verificando conectividade com New Relic...")
    conectividade_ok = verificar_conectividade_new_relic()
    if not conectividade_ok:
        logger.error("❌ Não foi possível conectar ao New Relic. Verifique suas credenciais e conexão de rede.")
        sys.exit(1)
    
    # 4. Atualizar indicador de dados reais
    logger.info("\n4. Atualizando indicador de dados reais...")
    atualizar_indicador_dados_reais()
    
    # 5. Forçar atualização do cache
    logger.info("\n5. Forçando atualização do cache...")
    forcar_atualizacao_cache()
    
    # Conclusão
    logger.info("\n="*50)
    logger.info("✅ Configuração concluída com sucesso!")
    logger.info("O sistema agora está configurado para usar dados reais do New Relic.")
    logger.info("="*50)
    logger.info("Para iniciar o sistema, execute:")
    logger.info("- PowerShell: .\\iniciar_sistema_completo.ps1")
    logger.info("- Ou utilize as tasks do VS Code")
    logger.info("="*50)

if __name__ == "__main__":
    main()
