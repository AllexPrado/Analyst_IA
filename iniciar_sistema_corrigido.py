"""
Script simplificado para iniciar o sistema usando os novos arquivos de configuração.
Este script garante que todos os diretórios necessários sejam encontrados e acessados corretamente.
"""
import os
import sys
import subprocess
import logging
import time
import signal
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

def check_structure():
    """Verifica e corrige a estrutura de diretórios se necessário"""
    # Verificar diretórios principais
    backend_dir = Path('backend')
    frontend_dir = Path('frontend')
    dados_dir_root = Path('dados')
    dados_dir_backend = Path('backend/dados')
    
    if not backend_dir.exists():
        logger.error(f"Diretório backend não encontrado: {backend_dir.absolute()}")
        return False
    
    if not frontend_dir.exists():
        logger.error(f"Diretório frontend não encontrado: {frontend_dir.absolute()}")
        return False
    
    # Verificar/criar diretórios de dados
    if not dados_dir_root.exists():
        dados_dir_root.mkdir(exist_ok=True)
        logger.info(f"Diretório de dados criado: {dados_dir_root.absolute()}")
    
    if not dados_dir_backend.exists():
        dados_dir_backend.mkdir(exist_ok=True)
        logger.info(f"Diretório de dados backend criado: {dados_dir_backend.absolute()}")
    
    # Se temos arquivos em apenas um dos diretórios de dados, copiar para o outro
    if dados_dir_root.exists() and dados_dir_backend.exists():
        root_files = list(dados_dir_root.glob('*.json'))
        backend_files = list(dados_dir_backend.glob('*.json'))
        
        if len(root_files) > 0 and len(backend_files) == 0:
            logger.info("Copiando arquivos de dados da raiz para o backend...")
            for json_file in root_files:
                try:
                    target_path = dados_dir_backend / json_file.name
                    with open(json_file, 'r', encoding='utf-8') as source_file:
                        data = json.load(source_file)
                        with open(target_path, 'w', encoding='utf-8') as target_file:
                            json.dump(data, target_file, ensure_ascii=False, indent=2)
                    logger.info(f"  - Arquivo {json_file.name} copiado")
                except Exception as e:
                    logger.error(f"  - Erro ao copiar arquivo {json_file.name}: {e}")
        elif len(backend_files) > 0 and len(root_files) == 0:
            logger.info("Copiando arquivos de dados do backend para a raiz...")
            for json_file in backend_files:
                try:
                    target_path = dados_dir_root / json_file.name
                    with open(json_file, 'r', encoding='utf-8') as source_file:
                        data = json.load(source_file)
                        with open(target_path, 'w', encoding='utf-8') as target_file:
                            json.dump(data, target_file, ensure_ascii=False, indent=2)
                    logger.info(f"  - Arquivo {json_file.name} copiado")
                except Exception as e:
                    logger.error(f"  - Erro ao copiar arquivo {json_file.name}: {e}")
    
    # Verificar/criar diretório de endpoints
    endpoints_dir = Path('backend/endpoints')
    if not endpoints_dir.exists():
        endpoints_dir.mkdir(exist_ok=True)
        # Criar arquivo __init__.py
        with open(endpoints_dir / '__init__.py', 'w') as f:
            f.write("# Módulo de endpoints da API")
        logger.info(f"Diretório de endpoints criado: {endpoints_dir.absolute()}")
    
    # Verificar se existe pelo menos um arquivo de endpoint
    insights_endpoint_file = endpoints_dir / 'insights_endpoints.py'
    if not insights_endpoint_file.exists():
        logger.warning("Arquivo de endpoint de insights não encontrado. Criando um básico...")
        with open(insights_endpoint_file, 'w') as f:
            f.write('''
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import random
from pathlib import Path

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router
router = APIRouter()

# Dados simulados para desenvolvimento - serão substituídos por dados reais
def generate_sample_insights_data():
    """Gera dados de insights para desenvolvimento"""
    return {
        "roiMonitoramento": round(random.uniform(3.5, 8.5), 1),
        "roiAumento": round(random.uniform(5, 15), 1),
        "aumentoProdutividade": round(random.uniform(15, 35), 1),
        "produtividadeComparativo": round(random.uniform(5, 15), 1),
        "horasEconomizadas": round(random.uniform(80, 150)),
        "economiaTotal": round(random.uniform(25000, 75000), 2),
        "economiaAumento": round(random.uniform(5, 20), 1),
        "incidentesEvitados": round(random.uniform(15, 45)),
        "satisfacao": round(random.uniform(7.5, 9.5), 1),
        "satisfacaoAumento": round(random.uniform(0.2, 1.2), 1),
        "avaliacoes": round(random.uniform(20, 50))
    }

# Endpoint para insights
@router.get("/insights")
async def get_insights():
    try:
        # Lista de possíveis localizações para o arquivo de insights
        possible_paths = [
            "dados/insights.json",               # Relativo ao diretório atual
            "backend/dados/insights.json",       # Relativo ao diretório raiz
            "../dados/insights.json",            # Um nível acima (se estamos em backend)
            "../backend/dados/insights.json"     # Um nível acima, então em backend
        ]
        
        # Tentar cada caminho
        for insights_path in possible_paths:
            if os.path.exists(insights_path):
                try:
                    with open(insights_path, 'r', encoding='utf-8') as file:
                        insights_data = json.load(file)
                        logger.info(f"Dados de insights carregados do arquivo: {insights_path}")
                        return insights_data
                except Exception as e:
                    logger.error(f"Erro ao ler dados de insights do arquivo {insights_path}: {e}")
        
        # Se não encontrou em nenhum lugar, procurar em qualquer lugar usando Path.glob
        root_dir = Path('.').resolve()
        for data_file in root_dir.glob('**/dados/insights.json'):
            try:
                with open(data_file, 'r', encoding='utf-8') as file:
                    insights_data = json.load(file)
                    logger.info(f"Dados de insights carregados do arquivo (busca global): {data_file}")
                    return insights_data
            except Exception as e:
                logger.error(f"Erro ao ler dados de insights do arquivo {data_file}: {e}")
        
        # Se não houver arquivo ou houver erro, gerar dados simulados
        logger.warning("Nenhum arquivo de dados de insights encontrado. Gerando dados simulados.")
        insights_data = generate_sample_insights_data()
        
        # Tentar salvar os dados simulados para uso futuro (em pelo menos um local)
        try:
            for path in ["dados/insights.json", "backend/dados/insights.json"]:
                dir_path = os.path.dirname(path)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                    
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(insights_data, f, ensure_ascii=False, indent=2)
                logger.info(f"Dados simulados salvos em {path}")
        except Exception as e:
            logger.error(f"Erro ao salvar dados simulados: {e}")
            
        return insights_data
    except Exception as e:
        logger.error(f"Erro ao processar requisição de insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))
''')
        logger.info("Arquivo de endpoint de insights criado")
    
    return True

def start_backend():
    """Inicia o servidor backend"""
    global backend_process
    logger.info("Iniciando servidor backend...")
    try:
        # Construir o comando - usar o script corrigido
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
        # Construir o comando para npm
        frontend_cmd = ["npm", "run", "dev"]
        
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
    
    # Verificar e corrigir estrutura de diretórios
    if not check_structure():
        logger.error("Falha ao verificar/corrigir estrutura de diretórios. Abortando.")
        sys.exit(1)
    
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
