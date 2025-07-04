"""
Script para verificar e validar o sistema Analyst_IA após as correções
Este script faz uma verificação completa e inicia o sistema
"""
import os
import sys
import logging
import subprocess
import time
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def verificar_ambiente():
    """Verificar se o ambiente está configurado corretamente"""
    logger.info("=== Verificando ambiente ===")
    
    # Verificar se estamos na raiz do projeto
    if not (Path('.env').exists() or Path('backend').exists() or Path('frontend').exists()):
        logger.error("❌ Este script deve ser executado na raiz do projeto")
        return False
    
    # Verificar se o Python está instalado
    try:
        subprocess.run(["python", "--version"], check=True, capture_output=True)
        logger.info("✅ Python instalado")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("❌ Python não está instalado ou não está no PATH")
        return False
    
    # Verificar se o Node.js está instalado
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        logger.info("✅ Node.js instalado")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("❌ Node.js não está instalado ou não está no PATH")
        return False
    
    # Verificar dependências do frontend
    if not Path('frontend/node_modules').exists():
        logger.warning("⚠️ Pasta node_modules não encontrada. Instalando dependências...")
        try:
            subprocess.run(["npm", "install"], cwd="frontend", check=True)
            logger.info("✅ Dependências do frontend instaladas")
        except subprocess.CalledProcessError:
            logger.error("❌ Erro ao instalar dependências do frontend")
            return False
    else:
        logger.info("✅ Dependências do frontend encontradas")
    
    # Verificar arquivo .env
    if not Path('.env').exists():
        logger.warning("⚠️ Arquivo .env não encontrado. Criando...")
        with open('.env', 'w') as f:
            f.write("""# Credenciais do New Relic
NEW_RELIC_API_KEY=your_api_key_here
NEW_RELIC_ACCOUNT_ID=your_account_id_here
NEW_RELIC_QUERY_KEY=your_query_key_here

# Configuração
USE_SIMULATED_DATA=true
""")
        logger.info("✅ Arquivo .env criado com configuração padrão")
    else:
        logger.info("✅ Arquivo .env encontrado")
    
    return True

def corrigir_consultas_newrelic():
    """Corrigir consultas do New Relic"""
    logger.info("=== Corrigindo consultas New Relic ===")
    
    if Path('corrigir_consultas_newrelic.py').exists():
        try:
            subprocess.run(["python", "corrigir_consultas_newrelic.py"], check=True)
            logger.info("✅ Consultas corrigidas com sucesso")
            return True
        except subprocess.CalledProcessError:
            logger.error("❌ Erro ao corrigir consultas")
            return False
    else:
        logger.warning("⚠️ Script corrigir_consultas_newrelic.py não encontrado")
        return False

def verificar_e_corrigir_cache():
    """Verificar e corrigir o cache"""
    logger.info("=== Verificando e corrigindo cache ===")
    
    try:
        subprocess.run(["python", "backend/check_and_fix_cache.py"], check=True)
        logger.info("✅ Cache verificado e corrigido")
        return True
    except subprocess.CalledProcessError:
        logger.error("❌ Erro ao verificar e corrigir cache")
        return False

def verificar_tasks_vscode():
    """Verificar se o arquivo tasks.json está correto"""
    logger.info("=== Verificando tasks.json ===")
    
    tasks_path = Path('.vscode/tasks.json')
    if not tasks_path.exists():
        logger.warning("⚠️ Arquivo tasks.json não encontrado")
        return False
    
    with open(tasks_path, 'r') as f:
        content = f.read()
    
    # Verificar se há operadores && no arquivo
    if ' && ' in content:
        logger.warning("⚠️ Operadores '&&' encontrados em tasks.json. Este operador não é compatível com PowerShell.")
        logger.info("Substituindo operadores '&&' por ';' para compatibilidade com PowerShell")
        
        content = content.replace(' && ', ' ; ')
        
        with open(tasks_path, 'w') as f:
            f.write(content)
        
        logger.info("✅ tasks.json corrigido")
    else:
        logger.info("✅ tasks.json está correto")
    
    return True

def iniciar_sistema():
    """Iniciar o sistema"""
    logger.info("=== Iniciando sistema ===")
    
    # Verificar se o script PowerShell existe
    if Path('iniciar_sistema_completo.ps1').exists():
        logger.info("Iniciando sistema usando o script PowerShell...")
        try:
            subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", "iniciar_sistema_completo.ps1"], 
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            logger.info("✅ Sistema inicializado")
            return True
        except subprocess.CalledProcessError:
            logger.error("❌ Erro ao iniciar o sistema")
            return False
    else:
        logger.warning("⚠️ Script iniciar_sistema_completo.ps1 não encontrado.")
        logger.info("Iniciando sistema manualmente...")
        
        try:
            # Iniciar backend
            subprocess.Popen(
                ["powershell", "-Command", "cd backend; python main.py"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # Aguardar um pouco para o backend iniciar
            time.sleep(2)
            
            # Iniciar frontend
            subprocess.Popen(
                ["powershell", "-Command", "cd frontend; npm run dev"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            logger.info("✅ Sistema inicializado manualmente")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar o sistema manualmente: {str(e)}")
            return False

def main():
    """Função principal"""
    logger.info("========================================")
    logger.info("Verificador e Inicializador do Analyst_IA")
    logger.info("========================================")
    
    # Verificar ambiente
    if not verificar_ambiente():
        logger.error("❌ Problemas encontrados no ambiente. Corrigindo...")
    
    # Verificar tasks.json
    verificar_tasks_vscode()
    
    # Corrigir consultas NewRelic
    corrigir_consultas_newrelic()
    
    # Verificar e corrigir cache
    verificar_e_corrigir_cache()
    
    # Iniciar sistema
    iniciar_sistema()
    
    logger.info("========================================")
    logger.info("Sistema verificado e iniciado!")
    logger.info("========================================")
    logger.info("Frontend: http://localhost:5173")
    logger.info("Backend: http://localhost:8000")
    logger.info("========================================")

if __name__ == "__main__":
    main()
