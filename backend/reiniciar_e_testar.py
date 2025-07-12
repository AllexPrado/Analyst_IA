"""
Script para reiniciar o servidor FastAPI com as alterações de roteamento
"""
import os
import sys
import subprocess
import time
import logging
import requests
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("restart_server")

def kill_existing_server(port=8000):
    """Finaliza qualquer processo em execução na porta especificada"""
    try:
        logger.info(f"Verificando processos na porta {port}...")
        # No Windows, usamos o comando netstat
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    pid = parts[-1]
                    logger.info(f"Finalizando processo com PID {pid} na porta {port}")
                    try:
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=True)
                        logger.info(f"Processo {pid} finalizado com sucesso")
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"Erro ao finalizar processo {pid}: {e}")
        else:
            logger.info(f"Nenhum processo encontrado na porta {port}")
    except Exception as e:
        logger.error(f"Erro ao verificar processos: {e}")

def start_server():
    """Inicia o servidor FastAPI usando o unified_backend.py"""
    logger.info("Iniciando o servidor...")
    
    try:
        # Executar o servidor em um processo separado
        server_process = subprocess.Popen(
            [sys.executable, "unified_backend.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Aguardar alguns segundos para o servidor iniciar
        logger.info("Aguardando o servidor iniciar...")
        time.sleep(5)
        
        # Verificar se o servidor está rodando
        try:
            response = requests.get("http://localhost:8000/api/health")
            if response.status_code == 200:
                logger.info("Servidor iniciado com sucesso!")
                return True
            else:
                logger.error(f"Servidor retornou status code {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Erro ao conectar ao servidor: {e}")
            
            # Capturar a saída do processo para diagnóstico
            stdout, stderr = server_process.communicate(timeout=1)
            logger.error(f"Saída do servidor: {stdout}")
            logger.error(f"Erros do servidor: {stderr}")
            
            return False
            
    except Exception as e:
        logger.error(f"Erro ao iniciar o servidor: {e}")
        return False

def test_endpoints():
    """Executa o script de teste de endpoints"""
    logger.info("Executando testes de endpoints...")
    try:
        result = subprocess.run(
            [sys.executable, "testar_endpoints_agno.py"],
            capture_output=True,
            text=True
        )
        
        logger.info("Resultado dos testes:")
        print(result.stdout)
        
        if result.returncode == 0:
            logger.info("Testes concluídos com sucesso!")
            return True
        else:
            logger.error("Alguns testes falharam!")
            logger.error(f"Saída de erro: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Erro ao executar testes: {e}")
        return False

if __name__ == "__main__":
    logger.info("Iniciando processo de reinício do servidor...")
    
    # Matar qualquer servidor existente
    kill_existing_server()
    
    # Iniciar o servidor
    if start_server():
        # Esperar mais alguns segundos para garantir que tudo está carregado
        time.sleep(3)
        
        # Testar os endpoints
        test_endpoints()
    else:
        logger.error("Falha ao iniciar o servidor. Verifique os logs para mais detalhes.")
        sys.exit(1)
