"""
Script para testar a inicialização do servidor MPC e capturar qualquer erro
"""
import subprocess
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_mpc_server")

def main():
    try:
        logger.info("Iniciando teste do servidor MPC...")
        
        # Verificar se existe config e deletar para forçar nova criação
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "mpc_agents.json")
        if os.path.exists(config_path):
            os.remove(config_path)
            logger.info(f"Arquivo de configuração removido: {config_path}")
        
        # Escrever logs em um arquivo
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "test_mpc_server.log")
        with open(log_file, "w") as f:
            f.write(f"Iniciando teste em: {logging.Formatter().formatTime()} \n")
        
        # Iniciar processo em modo não-shell para capturar output
        logger.info("Iniciando servidor MPC na porta 8765...")
        process = subprocess.Popen(
            ["python", "mpc_server.py", "--port", "8765"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Ler as primeiras linhas da saída para verificar se iniciou corretamente
        stdout, stderr = process.communicate(timeout=10)
        
        # Escrever saída no arquivo de log
        with open(log_file, "a") as f:
            f.write("--- STDOUT ---\n")
            f.write(stdout)
            f.write("\n--- STDERR ---\n")
            f.write(stderr if stderr else "Nenhum erro reportado")
        
        logger.info("Saída do servidor MPC:")
        logger.info(stdout)
        
        if stderr:
            logger.error("Erros do servidor MPC:")
            logger.error(stderr)
            
        logger.info("Teste concluído!")
        
        # Encerrar processo
        process.terminate()
        
    except subprocess.TimeoutExpired:
        logger.info("Servidor MPC iniciou corretamente (timeout após 10s)")
    except Exception as e:
        logger.error(f"Erro durante o teste: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
