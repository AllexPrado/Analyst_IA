import logging
import os
from datetime import datetime

def setup_logger(name, log_level=logging.INFO):
    """
    Configura e retorna um logger com o nome especificado.
    
    Args:
        name (str): Nome do logger
        log_level (int, opcional): Nível de log (default: logging.INFO)
        
    Returns:
        logging.Logger: Um objeto logger configurado
    """
    # Cria o logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Remove handlers existentes para evitar duplicação
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Cria um handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Define o formato dos logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Adiciona o handler ao logger
    logger.addHandler(console_handler)
    
    # Cria um handler para arquivo se o diretório de logs existir
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    if os.path.exists(logs_dir):
        log_file = os.path.join(logs_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger