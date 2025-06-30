"""
Script simplificado para iniciar o frontend e o backend do Analyst IA.
Este script inicia os serviços e gera dados de demonstração para o sistema.
"""
import os
import sys
import subprocess
import logging
import time
import signal
import shutil
from pathlib import Path
import json

# Configurar o logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Variáveis globais
backend_process = None
frontend_process = None

def check_requirements():
    """Verifica se todas as dependências estão disponíveis"""
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

def copy_api_files():
    """Copia os arquivos necessários para implementar a API"""
    logger.info("Copiando arquivos da API...")
    
    # Criar estrutura de diretórios
    os.makedirs('backend/endpoints', exist_ok=True)
    os.makedirs('backend/dados', exist_ok=True)
    
    # Criar arquivos básicos da API
    
    # 1. __init__.py
    with open('backend/endpoints/__init__.py', 'w') as f:
        f.write("# Módulo de endpoints da API")
    
    # 2. insights_endpoints.py
    with open('backend/endpoints/insights_endpoints.py', 'w') as f:
        f.write("""
from fastapi import APIRouter, HTTPException
import logging
import json
import os
import random
from datetime import datetime, timedelta

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router
router = APIRouter()

# Dados simulados para desenvolvimento - serão substituídos por dados reais
def generate_sample_insights_data():
    \"\"\"Gera dados de insights para desenvolvimento\"\"\"
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
        "avaliacoes": round(random.uniform(20, 50)),
        "impactoSeries": [
            {
                "name": "Atual",
                "data": [
                    round(random.uniform(12000, 18000)),
                    round(random.uniform(20000, 30000)), 
                    round(random.uniform(30000, 40000)),
                    round(random.uniform(15000, 22000)),
                    round(random.uniform(25000, 35000))
                ]
            },
            {
                "name": "Potencial com otimizações",
                "data": [
                    round(random.uniform(15000, 22000)),
                    round(random.uniform(27000, 37000)),
                    round(random.uniform(37000, 47000)),
                    round(random.uniform(20000, 28000)),
                    round(random.uniform(32000, 42000))
                ]
            }
        ],
        "problemasSeries": [
            {
                "name": "Incidentes Ocorridos",
                "data": [18, 15, 12, 8, 7, 5, 4]
            },
            {
                "name": "Incidentes Evitados",
                "data": [5, 8, 12, 15, 18, 22, 25]
            }
        ],
        "recomendacoes": [
            {
                "titulo": "Otimização de queries SQL lentas",
                "descricao": "Adicionar índices para as queries que estão consumindo mais recursos",
                "categoria": "performance",
                "prioridade": "Alta",
                "impacto": 8.5,
                "esforco": "Médio"
            },
            {
                "titulo": "Implementar cache de dados de sessão",
                "descricao": "Reduzir chamadas ao banco utilizando Redis para armazenar dados de sessão",
                "categoria": "eficiencia",
                "prioridade": "Média",
                "impacto": 7.0,
                "esforco": "Baixo"
            },
            {
                "titulo": "Consolidar servidores de aplicação",
                "descricao": "Reduzir a quantidade de servidores subutilizados no ambiente de homologação",
                "categoria": "custo",
                "prioridade": "Média",
                "impacto": 6.5,
                "esforco": "Alto"
            }
        ]
    }

# Endpoint para insights
@router.get("/insights")
async def get_insights():
    try:
        # Verificar se existe um arquivo de dados reais
        insights_path = "dados/insights.json"
        if os.path.exists(insights_path):
            try:
                with open(insights_path, 'r') as file:
                    insights_data = json.load(file)
                    logger.info("Dados de insights carregados do arquivo")
                    return insights_data
            except Exception as e:
                logger.error(f"Erro ao ler dados de insights do arquivo: {e}")
        
        # Se não houver arquivo ou houver erro, gerar dados simulados
        insights_data = generate_sample_insights_data()
        
        # Salvar os dados gerados para uso futuro
        os.makedirs("dados", exist_ok=True)
        with open(insights_path, 'w') as file:
            json.dump(insights_data, file)
        
        logger.info("Dados de insights gerados e salvos")
        return insights_data
    except Exception as e:
        logger.error(f"Erro ao processar request de insights: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar insights: {str(e)}")
""")

    # 3. core_router.py
    with open('backend/core_router.py', 'w') as f:
        f.write("""
from fastapi import APIRouter, HTTPException
import logging
import os
import json
import random
from typing import Dict, List, Optional

# Importar os routers de endpoints específicos
from endpoints.insights_endpoints import router as insights_router

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router principal
api_router = APIRouter()

# Incluir os routers de endpoints específicos
api_router.include_router(insights_router, tags=["insights"])

# Endpoint de saúde para verificação
@api_router.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

# Endpoint para status do sistema
@api_router.get("/status")
async def get_status():
    return {
        "servidor": "online",
        "cache": "atualizado",
        "ultima_atualizacao": "2025-06-29T10:15:30Z",
        "servicos": {
            "coleta": "ativo",
            "analise": "ativo",
            "alerta": "ativo"
        }
    }

# Endpoint para cobertura
@api_router.get("/cobertura")
async def get_cobertura():
    return {
        "total_entidades": 180,
        "monitoradas": 155,
        "porcentagem": 86.1,
        "por_dominio": {
            "APM": {"total": 50, "monitoradas": 45, "criticas": 10},
            "BROWSER": {"total": 35, "monitoradas": 28, "criticas": 5},
            "INFRA": {"total": 70, "monitoradas": 62, "criticas": 15},
            "MOBILE": {"total": 15, "monitoradas": 10, "criticas": 3}
        }
    }

# Endpoint para KPIs
@api_router.get("/kpis")
async def get_kpis():
    return {
        "performance": {
            "apdex": 0.85,
            "tempo_resposta": 0.9,
            "tendencia": 5.3,
            "historico": [0.72, 0.75, 0.78, 0.82, 0.85]
        },
        "disponibilidade": {
            "uptime": 99.8,
            "total_servicos": 50,
            "servicos_disponiveis": 48,
            "tendencia": 0.2
        },
        "erros": {
            "taxa_erro": 0.8,
            "tendencia": -15.4,
            "total_requisicoes": 250000,
            "requisicoes_com_erro": 2000
        }
    }

# Endpoint para tendências
@api_router.get("/tendencias")
async def get_tendencias():
    return {
        "apdex": {
            "labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
            "series": [
                {"name": "Web", "data": [0.72, 0.75, 0.78, 0.82, 0.85, 0.87]},
                {"name": "Mobile", "data": [0.68, 0.71, 0.75, 0.79, 0.82, 0.84]},
                {"name": "API", "data": [0.81, 0.83, 0.84, 0.86, 0.88, 0.91]}
            ]
        }
    }

# Endpoint para resumo geral
@api_router.get("/resumo-geral")
async def get_resumo_geral():
    return {
        "status_geral": "SAUDÁVEL",
        "alertas_ativos": 2,
        "entidades_monitoradas": 155,
        "indicadores": {
            "apdex": 0.85,
            "erro": 0.8,
            "latencia": 0.9,
            "throughput": 3500
        }
    }

# Endpoint para entidades
@api_router.get("/entidades")
async def get_entidades():
    path = "dados/entidades.json"
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return []
""")

    # 4. Modificar o main.py para usar o router
    main_file = 'backend/main.py'
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Adicionar importação do router se necessário
    if "from core_router import api_router" not in content:
        import_line = "from core_router import api_router"
        if "import uvicorn" in content:
            content = content.replace("import uvicorn", f"import uvicorn\n{import_line}")
        else:
            content = f"{import_line}\n{content}"
    
    # Adicionar a inclusão do router se necessária
    if "app.include_router(api_router, prefix='/api')" not in content:
        if "app = FastAPI(" in content:
            app_def_end = content.find(")", content.find("app = FastAPI(")) + 1
            insert_pos = content.find("\n", app_def_end) + 1
            router_line = "\n# Incluir os endpoints do router principal\napp.include_router(api_router, prefix='/api')\n"
            content = content[:insert_pos] + router_line + content[insert_pos:]
    
    with open(main_file, 'w') as f:
        f.write(content)
    
    logger.info("Arquivos da API copiados com sucesso")
    return True

def generate_demo_data():
    """Gera dados de demonstração básicos para o sistema"""
    logger.info("Gerando dados de demonstração básicos...")
    
    # Criar diretório de dados se não existir
    data_dir = Path('backend/dados')
    data_dir.mkdir(exist_ok=True)
    
    # Dados de insights simples
    insights = {
        "roiMonitoramento": 5.8,
        "roiAumento": 12.5,
        "aumentoProdutividade": 22.3,
        "produtividadeComparativo": 8.2,
        "horasEconomizadas": 120,
        "economiaTotal": 45000.00,
        "economiaAumento": 15.3,
        "incidentesEvitados": 30,
        "satisfacao": 8.7,
        "satisfacaoAumento": 0.8,
        "avaliacoes": 35,
        "impactoSeries": [
            {
                "name": "Atual",
                "data": [15000, 25000, 35000, 18000, 29000]
            },
            {
                "name": "Potencial com otimizações",
                "data": [18000, 32000, 42000, 24000, 38000]
            }
        ],
        "problemasSeries": [
            {
                "name": "Incidentes Ocorridos",
                "data": [18, 15, 12, 8, 7, 5, 4]
            },
            {
                "name": "Incidentes Evitados",
                "data": [5, 8, 12, 15, 18, 22, 25]
            }
        ]
    }
    
    # Salvar dados de insights
    with open('backend/dados/insights.json', 'w') as f:
        json.dump(insights, f, indent=2)
    
    logger.info("Dados de demonstração básicos gerados com sucesso")
    return True

def start_backend():
    """Inicia o servidor backend"""
    global backend_process
    logger.info("Iniciando servidor backend...")
    
    # Salvar diretório atual
    original_dir = os.getcwd()
    
    try:
        # Mudar para o diretório backend
        os.chdir('backend')
        
        # Construir o comando
        backend_cmd = [sys.executable, 'main.py']
        
        # Iniciar o processo em modo não-bloqueante
        backend_process = subprocess.Popen(
            backend_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Voltar ao diretório original
        os.chdir(original_dir)
        
        # Aguardar um momento para o servidor iniciar
        time.sleep(2)
        
        # Verificar se o processo está em execução
        if backend_process.poll() is None:
            logger.info("Servidor backend iniciado com sucesso na porta 8000")
            return True
        else:
            stdout, stderr = backend_process.communicate()
            logger.error(f"Erro ao iniciar o backend: {stderr}")
            # Voltar ao diretório original
            os.chdir(original_dir)
            return False
    except Exception as e:
        logger.error(f"Erro ao iniciar o backend: {e}")
        # Voltar ao diretório original se houver erro
        os.chdir(original_dir)
        return False

def start_frontend():
    """Inicia o servidor de desenvolvimento frontend"""
    global frontend_process
    logger.info("Iniciando servidor frontend...")
    
    # Salvar diretório atual
    original_dir = os.getcwd()
    
    try:
        # Mudar para o diretório frontend
        os.chdir('frontend')
        
        # Verificar qual comando está disponível (npm ou yarn)
        npm_cmd = shutil.which('npm')
        if not npm_cmd:
            logger.error("npm não encontrado no PATH")
            os.chdir(original_dir)
            return False
        
        # Construir o comando
        frontend_cmd = [npm_cmd, 'run', 'dev']
        
        # Iniciar o processo em modo não-bloqueante
        frontend_process = subprocess.Popen(
            frontend_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Voltar ao diretório original
        os.chdir(original_dir)
        
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
        logger.error(f"Erro ao iniciar o frontend: {e}")
        # Garantir que estamos no diretório original
        os.chdir(original_dir)
        return False

def cleanup(signum=None, frame=None):
    """Limpa processos em execução ao encerrar o script"""
    logger.info("Encerrando processos...")
    
    # Encerrar processo do backend
    if backend_process and backend_process.poll() is None:
        logger.info("Encerrando servidor backend...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
    
    # Encerrar processo do frontend
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
    # Registrar handlers para encerramento limpo
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Verificar requisitos
    if not check_requirements():
        logger.error("Requisitos não satisfeitos. Abortando.")
        sys.exit(1)
    
    # Copiar arquivos da API
    if not copy_api_files():
        logger.error("Falha ao copiar arquivos da API. Abortando.")
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
    logger.info("  - Backend: http://localhost:8000/api/health")
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
