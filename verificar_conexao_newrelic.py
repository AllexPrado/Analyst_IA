"""
Script para verificar a conectividade com os serviços do New Relic
e diagnosticar problemas na configuração.
"""
import os
import sys
import json
import requests
import socket
from dotenv import load_dotenv
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def carregar_variaveis_ambiente():
    """Carrega as variáveis de ambiente do arquivo .env"""
    load_dotenv()
    
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
    api_key = os.getenv('NEW_RELIC_API_KEY')
    use_simulated = os.getenv('USE_SIMULATED_DATA', 'false').lower() == 'true'
    
    return account_id, api_key, use_simulated

def verificar_conectividade_dns():
    """Verifica se é possível resolver os domínios do New Relic"""
    dominios = [
        'api.newrelic.com',
        'insights-api.newrelic.com',
        'one.newrelic.com'
    ]
    
    logger.info("Verificando resolução DNS para domínios do New Relic...")
    
    for dominio in dominios:
        try:
            ip = socket.gethostbyname(dominio)
            logger.info(f"✅ {dominio} -> {ip}")
        except socket.gaierror:
            logger.error(f"❌ Não foi possível resolver o domínio {dominio}")
            return False
    
    return True

def verificar_api_key(account_id, api_key):
    """Verifica se a API key é válida"""
    if not account_id or not api_key:
        logger.error("❌ Account ID ou API Key não configurados")
        return False
        
    logger.info(f"Verificando API Key para a conta {account_id}...")
    
    headers = {
        'Api-Key': api_key,
    }
    
    url = f"https://api.newrelic.com/graphql"
    query = """
    {
      actor {
        account(id: ACCOUNT_ID) {
          id
          name
        }
      }
    }
    """.replace("ACCOUNT_ID", account_id)
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            json={"query": query},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and data["data"].get("actor") and data["data"]["actor"].get("account"):
                account_name = data["data"]["actor"]["account"]["name"]
                logger.info(f"✅ API Key válida para a conta: {account_name}")
                return True
            else:
                logger.error(f"❌ API Key inválida ou não tem acesso à conta {account_id}")
                return False
        else:
            logger.error(f"❌ Erro ao verificar API Key: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro de conexão ao verificar API Key: {e}")
        return False

def verificar_consulta_nrql(account_id, api_key):
    """Verifica se é possível executar consultas NRQL"""
    logger.info("Verificando consulta NRQL simples...")
    
    headers = {
        'Api-Key': api_key,
    }
    
    url = f"https://insights-api.newrelic.com/v1/accounts/{account_id}/query"
    payload = {
        "nrql": "SELECT count(*) FROM Transaction SINCE 1 day ago"
    }
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Consulta NRQL executada com sucesso: {data}")
            return True
        else:
            logger.error(f"❌ Erro ao executar consulta NRQL: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro de conexão ao executar consulta NRQL: {e}")
        return False

def verificar_configuracao_cache():
    """Verifica se os arquivos de cache estão presentes e válidos"""
    logger.info("Verificando arquivos de cache...")
    
    arquivos_cache = [
        "historico/cache_completo.json",
        "backend/cache/kubernetes_metrics.json",
        "backend/cache/infrastructure_detailed.json",
        "backend/cache/service_topology.json"
    ]
    
    for arquivo in arquivos_cache:
        caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), arquivo)
        if os.path.exists(caminho):
            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"✅ {arquivo}: Arquivo válido e contém dados JSON")
            except json.JSONDecodeError:
                logger.error(f"❌ {arquivo}: Arquivo contém JSON inválido")
            except Exception as e:
                logger.error(f"❌ {arquivo}: Erro ao ler arquivo: {e}")
        else:
            logger.warning(f"⚠️ {arquivo}: Arquivo não encontrado")

def verificar_consulta_graphql(account_id, api_key):
    """Verifica se é possível executar consultas GraphQL"""
    logger.info("Verificando consulta GraphQL simples...")
    
    headers = {
        'Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    url = "https://api.newrelic.com/graphql"
    query = """
    {
      actor {
        account(id: ACCOUNT_ID) {
          nrql(query: "SELECT count(*) FROM Transaction SINCE 1 hour ago") {
            results
          }
        }
      }
    }
    """.replace("ACCOUNT_ID", account_id)
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            json={"query": query},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                logger.error(f"❌ Erro na consulta GraphQL: {data['errors']}")
                return False
            else:
                logger.info(f"✅ Consulta GraphQL executada com sucesso")
                return True
        else:
            logger.error(f"❌ Erro ao executar consulta GraphQL: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro de conexão ao executar consulta GraphQL: {e}")
        return False

def verificar_entidade_collector(account_id, api_key):
    """Verifica se o coletor de entidades está configurado corretamente"""
    logger.info("Verificando módulo newrelic_advanced_collector...")
    
    try:
        from backend.utils.newrelic_advanced_collector import fetch_entities_with_metrics
        logger.info("✅ Módulo importado com sucesso")
        
        # Vamos verificar o código-fonte em busca de problemas comuns
        import inspect
        import backend.utils.newrelic_advanced_collector as collector
        
        source = inspect.getsource(collector)
        
        if "Duplicate input field name" in source:
            logger.warning("⚠️ Possível problema encontrado: campos duplicados na consulta GraphQL")
        
        if "entity_guid entity_guid" in source:
            logger.warning("⚠️ Campo duplicado detectado: entity_guid")
            
        if "domain domain" in source:
            logger.warning("⚠️ Campo duplicado detectado: domain")
            
        return True
    except ImportError:
        logger.error("❌ Não foi possível importar o módulo newrelic_advanced_collector")
        return False
    except Exception as e:
        logger.error(f"❌ Erro ao verificar collector: {e}")
        return False

def corrigir_campo_duplicado():
    """Tenta corrigir o problema de campos duplicados no coletor"""
    logger.info("Tentando corrigir problema de campos duplicados...")
    
    arquivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                         "backend/utils/newrelic_advanced_collector.py")
    
    if not os.path.exists(arquivo):
        logger.error(f"❌ Arquivo não encontrado: {arquivo}")
        return False
        
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            
        # Procura e corrige campos duplicados
        conteudo_corrigido = conteudo
        padroes_duplicados = [
            ("entity_guid entity_guid", "entity_guid"),
            ("domain domain", "domain"),
            ("type type", "type"),
            ("name name", "name"),
            ("account account", "account"),
            ("entityType entityType", "entityType")
        ]
        
        for padrao, correcao in padroes_duplicados:
            if padrao in conteudo:
                conteudo_corrigido = conteudo_corrigido.replace(padrao, correcao)
                logger.info(f"✅ Corrigido: {padrao} -> {correcao}")
                
        if conteudo != conteudo_corrigido:
            # Faz backup do arquivo original
            with open(f"{arquivo}.bak", 'w', encoding='utf-8') as f:
                f.write(conteudo)
                
            # Escreve a versão corrigida
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo_corrigido)
                
            logger.info("✅ Arquivo corrigido e backup criado")
            return True
        else:
            logger.info("ℹ️ Nenhum padrão duplicado encontrado para correção")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao corrigir arquivo: {e}")
        return False

def exibir_recomendacoes(account_id, api_key, use_simulated):
    """Exibe recomendações com base nos resultados da verificação"""
    logger.info("\n=== RECOMENDAÇÕES ===")
    
    if not account_id or not api_key:
        logger.info("""
1. Configure corretamente as credenciais do New Relic no arquivo .env:
   NEW_RELIC_ACCOUNT_ID=seu_account_id
   NEW_RELIC_API_KEY=sua_api_key
        """)
    
    if use_simulated:
        logger.info("""
2. Você está usando dados simulados. Para usar dados reais:
   Altere USE_SIMULATED_DATA=false no arquivo .env
        """)
    
    logger.info("""
3. Execute o script para corrigir cache:
   python backend/check_and_fix_cache.py
   
4. Para iniciar o sistema corretamente no PowerShell:
   .\iniciar_sistema_completo.ps1
   
5. Se os problemas persistirem, verifique:
   - Firewall e restrições de rede
   - Validade das credenciais do New Relic
   - Formato das consultas GraphQL no arquivo newrelic_advanced_collector.py
        """)

def main():
    logger.info("=== VERIFICAÇÃO DE CONEXÃO COM NEW RELIC ===")
    
    account_id, api_key, use_simulated = carregar_variaveis_ambiente()
    
    if use_simulated:
        logger.warning("⚠️ Sistema configurado para usar DADOS SIMULADOS")
    else:
        logger.info("✅ Sistema configurado para usar DADOS REAIS")
    
    conectividade_ok = verificar_conectividade_dns()
    
    if not conectividade_ok:
        logger.error("❌ Problemas de conectividade DNS detectados")
        logger.info("Isso pode indicar problemas de rede ou firewall")
    
    if account_id and api_key:
        api_key_ok = verificar_api_key(account_id, api_key)
        
        if api_key_ok:
            consulta_nrql_ok = verificar_consulta_nrql(account_id, api_key)
            consulta_graphql_ok = verificar_consulta_graphql(account_id, api_key)
            
            if not consulta_graphql_ok:
                logger.info("Verificando problemas conhecidos no coletor...")
                verificar_entidade_collector(account_id, api_key)
                
                logger.info("Tentando corrigir campos duplicados...")
                corrigido = corrigir_campo_duplicado()
                
                if corrigido:
                    logger.info("✅ Correções aplicadas, tente reiniciar o sistema")
    else:
        logger.error("❌ Credenciais do New Relic não encontradas no arquivo .env")
    
    verificar_configuracao_cache()
    
    exibir_recomendacoes(account_id, api_key, use_simulated)
    
if __name__ == "__main__":
    main()
