"""
Script simples para inicializar o backend do Analyst_IA com tratamento de erros.
Este script tenta identificar e corrigir problemas comuns antes de iniciar o backend.
"""
import os
import sys
import subprocess
import logging
import time

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("logs/start.log"),
                        logging.StreamHandler(sys.stdout)
                    ])
logger = logging.getLogger(__name__)

def verificar_instalacao_markdown():
    """
    Verifica se o pacote markdown está instalado e instala se necessário.
    """
    try:
        import markdown
        logger.info("Pacote markdown já está instalado.")
        return True
    except ImportError:
        logger.info("Pacote markdown não encontrado, tentando instalar...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown"])
            logger.info("Pacote markdown instalado com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro ao instalar markdown: {str(e)}")
            return False

def verificar_arquivo(caminho):
    """
    Verifica se um arquivo existe.
    """
    if os.path.exists(caminho):
        return True
    
    logger.warning(f"Arquivo não encontrado: {caminho}")
    return False

def executar_script(nome_script):
    """
    Executa um script Python.
    """
    if nome_script.endswith(".py"):
        script_path = nome_script
    else:
        script_path = f"{nome_script}.py"
        
    if not os.path.exists(script_path):
        logger.error(f"Script não encontrado: {script_path}")
        return False
        
    try:
        logger.info(f"Executando script: {script_path}")
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Exibir saída em tempo real
        for line in process.stdout:
            print(line, end='')
            
        process.wait()
        
        if process.returncode == 0:
            logger.info(f"Script {script_path} executado com sucesso")
            return True
        else:
            stderr = process.stderr.read()
            logger.error(f"Erro ao executar {script_path}: {process.returncode}")
            logger.error(f"Erro: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Exceção ao executar {script_path}: {str(e)}")
        return False

def main():
    """
    Função principal que executa a inicialização do backend.
    """
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    logger.info("Iniciando processo de inicialização do backend")
    
    # Verificar e instalar markdown
    verificar_instalacao_markdown()
    
    # Verificar se temos um script de reparo
    if verificar_arquivo("repair_backend.py"):
        logger.info("Executando script de reparo...")
        if executar_script("repair_backend"):
            logger.info("Reparo concluído com sucesso!")
            return 0
        else:
            logger.warning("Reparo encontrou problemas, tentando inicialização direta...")
    
    # Tentar inicializar diretamente
    if verificar_arquivo("start_backend.py"):
        logger.info("Tentando inicializar com start_backend.py")
        if executar_script("start_backend"):
            logger.info("Backend iniciado com sucesso!")
            return 0
    elif verificar_arquivo("start_backend_safe.py"):
        logger.info("Tentando inicializar com start_backend_safe.py")
        if executar_script("start_backend_safe"):
            logger.info("Backend iniciado com sucesso!")
            return 0
    elif verificar_arquivo("main.py"):
        logger.info("Tentando inicializar com uvicorn main:app")
        try:
            logger.info("Iniciando backend com uvicorn...")
            subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--reload"])
            return 0
        except Exception as e:
            logger.error(f"Erro ao iniciar uvicorn: {str(e)}")
    
    logger.error("Falha em todas as tentativas de inicialização do backend")
    return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Inicialização interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Erro fatal durante inicialização: {str(e)}")
        sys.exit(1)
