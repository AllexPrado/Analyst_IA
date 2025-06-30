"""
Script para iniciar tanto o backend quanto o frontend simultaneamente.
Gera também dados de demonstração para uma experiência completa.
"""
import os
import sys
import subprocess
import logging
import time
import signal
import shutil
import json
from pathlib import Path

# Configurar o logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Processos globais
backend_process = None
frontend_process = None

def check_requirements():
    """Verifica se todas as dependências estão disponíveis"""
    # Verificar Python
    logger.info("Verificando requisitos...")
    
    # Verificar diretórios principais
    backend_dir = Path('backend')
    frontend_dir = Path('frontend')
    
    if not backend_dir.exists() or not backend_dir.is_dir():
        logger.error("Diretório backend não encontrado")
        return False
    
    if not frontend_dir.exists() or not frontend_dir.is_dir():
        logger.error("Diretório frontend não encontrado")
        return False
    
    # Verificar package.json no frontend
    if not (frontend_dir / 'package.json').exists():
        logger.error("package.json não encontrado no frontend")
        return False
    
    # Verificar main.py no backend
    if not (backend_dir / 'main.py').exists():
        logger.error("main.py não encontrado no backend")
        return False
    
    logger.info("Todos os requisitos verificados com sucesso")
    return True

def generate_demo_data():
    """Gera dados de demonstração para o sistema"""
    logger.info("Gerando dados de demonstração...")
    original_dir = os.getcwd()
    try:
        # Mudar para o diretório do backend
        os.chdir('backend')
        
        # Tentar executar o script principal de geração de dados
        try:
            subprocess.run([sys.executable, 'gerar_todos_dados_demo.py'], check=True)
            logger.info("Dados gerados pelo script completo")
        except Exception as e:
            logger.warning(f"Erro ao executar gerar_todos_dados_demo.py: {e}")
            # Tentar o script de backup
            try:
                subprocess.run([sys.executable, 'gerar_dados_demo.py'], check=True)
                logger.info("Dados gerados pelo script de backup")
            except Exception as e2:
                logger.error(f"Erro ao executar gerar_dados_demo.py: {e2}")
                raise Exception("Falha em todos os scripts de geração de dados")
        
        # Voltar ao diretório original
        os.chdir(original_dir)
        
        logger.info("Dados de demonstração gerados com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao gerar dados de demonstração: {e}")
        # Garantir que estamos no diretório original
        os.chdir(original_dir)
        return False

def start_backend():
    """Inicia o servidor backend"""
    global backend_process
    logger.info("Iniciando servidor backend...")
    try:
        # Verificar se o módulo endpoints existe e copiar se necessário
        endpoints_src = Path('backend/endpoints')
        if not endpoints_src.exists():
            logger.error("Módulo de endpoints não encontrado. Criando...")
            os.makedirs('backend/endpoints', exist_ok=True)
            # Copiar os arquivos __init__.py e insights_endpoints.py
            with open('backend/endpoints/__init__.py', 'w') as f:
                f.write("# Módulo de endpoints da API")
            
            # Garantir que temos o arquivo de endpoints de insights
            if not Path('backend/endpoints/insights_endpoints.py').exists():
                # Código simplificado para insights_endpoints.py
                with open('backend/endpoints/insights_endpoints.py', 'w') as f:
                    f.write("""
from fastapi import APIRouter, HTTPException
import logging
import json
import os
import random
from pathlib import Path

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router
router = APIRouter()

@router.get("/insights")
async def get_insights():
    try:
        # Verificar se existe um arquivo de dados reais
        # Primeiro tentar com caminho direto (isso é para quando o backend roda no diretório raiz)
        insights_path = "dados/insights.json"
        if os.path.exists(insights_path):
            try:
                with open(insights_path, 'r') as file:
                    insights_data = json.load(file)
                    return insights_data
            except Exception as e:
                logger.error(f"Erro ao ler dados de insights: {e}")
        
        # Tentar com caminho relativo ao backend
        insights_path = "backend/dados/insights.json"
        if os.path.exists(insights_path):
            try:
                with open(insights_path, 'r') as file:
                    insights_data = json.load(file)
                    return insights_data
            except Exception as e:
                logger.error(f"Erro ao ler dados de insights: {e}")
                
        # Se ainda não encontrou, procurar acima do diretório atual
        insights_path = Path("../dados/insights.json").absolute()
        if os.path.exists(insights_path):
            try:
                with open(insights_path, 'r') as file:
                    insights_data = json.load(file)
                    return insights_data
            except Exception as e:
                logger.error(f"Erro ao ler dados de insights: {e}")
        
        # Retornar dados de fallback
        return {"mensagem": "Dados de insights não disponíveis"}
    except Exception as e:
        logger.error(f"Erro ao processar request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
""")
        
        # Criar um link simbólico ou copiar os dados da pasta backend/dados para Analyst_IA/dados se necessário
        backend_dados = Path('backend/dados')
        dados_dir = Path('dados')
        
        # Verificar se os dados existem no diretório backend/dados mas não em Analyst_IA/dados
        if backend_dados.exists() and not dados_dir.exists():
            logger.info("Copiando dados do backend para o diretório raiz...")
            try:
                # Criar o diretório de dados no diretório raiz se não existir
                dados_dir.mkdir(exist_ok=True)
                
                # Copiar todos os arquivos JSON do backend/dados para dados/
                for json_file in backend_dados.glob('*.json'):
                    target_path = dados_dir / json_file.name
                    with open(json_file, 'r', encoding='utf-8') as source_file:
                        data = json.load(source_file)
                        with open(target_path, 'w', encoding='utf-8') as target_file:
                            json.dump(data, target_file, ensure_ascii=False, indent=2)
                    logger.info(f"Arquivo {json_file.name} copiado para diretório raiz")
            except Exception as e:
                logger.error(f"Erro ao copiar dados: {e}")
        
        # Construir o comando
        backend_cmd = [sys.executable, 'backend/main.py']
        
        # Iniciar o processo em modo não-bloqueante
        backend_process = subprocess.Popen(
            backend_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Aguardar um momento para o servidor iniciar
        time.sleep(2)
        
        # Verificar se o processo está em execução
        if backend_process.poll() is None:
            logger.info("Servidor backend iniciado com sucesso na porta 8000")
            return True
        else:
            stdout, stderr = backend_process.communicate()
            logger.error(f"Erro ao iniciar o backend: {stderr}")
            return False
    except Exception as e:
        logger.error(f"Erro ao iniciar o backend: {e}")
        return False

def start_frontend():
    """Inicia o servidor de desenvolvimento frontend"""
    global frontend_process
    logger.info("Iniciando servidor frontend...")
    try:
        # Construir o comando (usar npm ou yarn dependendo do que estiver disponível)
        npm_cmd = shutil.which('npm')
        if not npm_cmd:
            logger.error("npm não encontrado no PATH")
            return False
        
        # Comando para iniciar o frontend
        frontend_cmd = [npm_cmd, 'run', 'dev']
        
        # Mudar para o diretório do frontend
        os.chdir('frontend')
        
        # Iniciar o processo em modo não-bloqueante
        frontend_process = subprocess.Popen(
            frontend_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Voltar ao diretório original
        os.chdir('..')
        
        # Aguardar um momento para o servidor iniciar
        time.sleep(3)
        
        # Verificar se o processo está em execução
        if frontend_process.poll() is None:
            logger.info("Servidor frontend iniciado com sucesso na porta 5173")
            return True
        else:
            stdout, stderr = frontend_process.communicate()
            logger.error(f"Erro ao iniciar o frontend: {stderr}")
            return False
    except Exception as e:
        # Garantir que estamos no diretório correto
        if not os.path.basename(os.getcwd()) == 'Analyst_IA':
            os.chdir('..')
        logger.error(f"Erro ao iniciar o frontend: {e}")
        return False

def cleanup(signum=None, frame=None):
    """Limpa os processos em execução ao encerrar o script"""
    logger.info("Encerrando processos...")
    
    if backend_process and backend_process.poll() is None:
        logger.info("Encerrando servidor backend...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
    
    if frontend_process and frontend_process.poll() is None:
        logger.info("Encerrando servidor frontend...")
        frontend_process.terminate()
        try:
            frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            frontend_process.kill()
    
    logger.info("Todos os processos encerrados")
    sys.exit(0)

def main():
    """Função principal"""
    # Registrar handler para encerramento limpo
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Verificar requisitos
    if not check_requirements():
        logger.error("Requisitos não satisfeitos. Abortando.")
        sys.exit(1)
    
    # Gerar dados de demonstração
    if not generate_demo_data():
        logger.warning("Não foi possível gerar dados de demonstração. Continuando mesmo assim.")
    
    # Iniciar backend
    if not start_backend():
        logger.error("Não foi possível iniciar o backend. Abortando.")
        cleanup()
    
    # Iniciar frontend
    if not start_frontend():
        logger.error("Não foi possível iniciar o frontend. Abortando.")
        cleanup()
    
    logger.info("======================================================")
    logger.info("Sistema iniciado com sucesso!")
    logger.info("  - Backend: http://localhost:8000")
    logger.info("  - Frontend: http://localhost:5173")
    logger.info("Pressione Ctrl+C para encerrar todos os serviços")
    logger.info("======================================================")
    
    try:
        # Manter o script em execução
        while True:
            time.sleep(1)
            
            # Verificar se os processos ainda estão em execução
            if backend_process.poll() is not None:
                logger.error("O servidor backend encerrou inesperadamente")
                cleanup()
            
            if frontend_process.poll() is not None:
                logger.error("O servidor frontend encerrou inesperadamente")
                cleanup()
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário")
        cleanup()

if __name__ == "__main__":
    main()
