"""
Script de inicialização do sistema Analyst IA com verificações e reparos automatizados.
Este script garante que todos os componentes necessários estão funcionando corretamente.
"""
import os
import sys
import asyncio
import logging
import time
import subprocess
from pathlib import Path
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Diretórios importantes
BASE_DIR = Path(__file__).parent
DADOS_DIR = BASE_DIR / "dados"
HISTORICO_DIR = BASE_DIR / "historico"

# Arquivos importantes
CACHE_FILE = HISTORICO_DIR / "cache_completo.json"
CHAT_HISTORY_FILE = DADOS_DIR / "chat_history.json"

# Configuração
CRIAR_ARQUIVOS_FALTANTES = True
REPARAR_CACHE = True
REINICIAR_SERVIDOR = True

async def verificar_diretorios():
    """Verifica e cria diretórios necessários"""
    diretorios = [DADOS_DIR, HISTORICO_DIR]
    for diretorio in diretorios:
        if not diretorio.exists():
            logger.info(f"Criando diretório: {diretorio}")
            diretorio.mkdir(parents=True, exist_ok=True)
        else:
            logger.info(f"Diretório existente: {diretorio}")
    return True

async def verificar_arquivo_cache():
    """Verifica se o arquivo de cache existe e é válido"""
    if not CACHE_FILE.exists():
        logger.warning(f"Arquivo de cache não encontrado: {CACHE_FILE}")
        return False
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        if not isinstance(cache_data, dict):
            logger.warning("Arquivo de cache existe, mas não é um dicionário válido")
            return False
            
        if 'timestamp' not in cache_data or 'entidades' not in cache_data:
            logger.warning("Arquivo de cache existe, mas está incompleto")
            return False
            
        logger.info(f"Arquivo de cache válido: {CACHE_FILE}")
        logger.info(f"Timestamp do cache: {cache_data.get('timestamp')}")
        logger.info(f"Número de entidades: {len(cache_data.get('entidades', []))}")
        return True
        
    except Exception as e:
        logger.warning(f"Erro ao verificar arquivo de cache: {e}")
        return False

async def verificar_chat_history():
    """Verifica se o arquivo de histórico de chat existe e é válido"""
    if not CHAT_HISTORY_FILE.exists():
        logger.warning(f"Arquivo de histórico de chat não encontrado: {CHAT_HISTORY_FILE}")
        
        if CRIAR_ARQUIVOS_FALTANTES:
            logger.info("Criando arquivo de histórico de chat inicial...")
            try:
                with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump([
                        {
                            "pergunta": "status",
                            "resposta": "O sistema está operacional e monitorando seus ambientes através do New Relic. Use este chat para obter análises e insights sobre seus serviços.",
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000000")
                        }
                    ], f, ensure_ascii=False, indent=2)
                logger.info(f"Arquivo de histórico de chat criado: {CHAT_HISTORY_FILE}")
                return True
            except Exception as e:
                logger.error(f"Erro ao criar arquivo de histórico de chat: {e}")
                return False
        return False
    
    try:
        with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        if not isinstance(history_data, list):
            logger.warning("Arquivo de histórico de chat existe, mas não é uma lista válida")
            return False
            
        logger.info(f"Arquivo de histórico de chat válido: {CHAT_HISTORY_FILE}")
        logger.info(f"Número de conversas: {len(history_data)}")
        return True
        
    except Exception as e:
        logger.warning(f"Erro ao verificar arquivo de histórico de chat: {e}")
        return False

async def reparar_cache_se_necessario():
    """Executa o script de reparo de cache se necessário"""
    if not REPARAR_CACHE:
        return True
        
    if await verificar_arquivo_cache():
        logger.info("Cache válido, não é necessário reparar")
        return True
    
    logger.info("Executando script de verificação e reparo de cache...")
    try:
        # Executar o script verificar_reparar_cache.py
        process = subprocess.Popen(
            [sys.executable, "verificar_reparar_cache.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=BASE_DIR
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.info("Script de reparo de cache executado com sucesso")
            return True
        else:
            logger.error(f"Erro ao executar script de reparo de cache: {stderr}")
            
            # Se o reparo falhou, tentar atualização completa
            logger.info("Tentando executar atualização completa do cache...")
            process = subprocess.Popen(
                [sys.executable, "atualizar_cache_completo.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=BASE_DIR
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                logger.info("Atualização completa do cache executada com sucesso")
                return True
            else:
                logger.error(f"Erro ao executar atualização completa do cache: {stderr}")
                return False
    except Exception as e:
        logger.error(f"Erro ao tentar reparar cache: {e}")
        return False

async def iniciar_servidor():
    """Inicia o servidor backend"""
    if not REINICIAR_SERVIDOR:
        return True
        
    logger.info("Iniciando servidor backend...")
    try:
        # Verificar se já existe um processo uvicorn rodando
        if os.name == 'nt':  # Windows
            output = subprocess.check_output("tasklist | findstr uvicorn", shell=True, text=True, stderr=subprocess.DEVNULL)
            if "uvicorn" in output:
                logger.info("Servidor já está em execução")
                return True
        else:  # Linux/Mac
            output = subprocess.check_output("ps -ef | grep uvicorn | grep -v grep", shell=True, text=True, stderr=subprocess.DEVNULL)
            if output.strip():
                logger.info("Servidor já está em execução")
                return True
    except subprocess.CalledProcessError:
        # Nenhum processo uvicorn encontrado
        pass
        
    # Iniciar o servidor
    try:
        # Usar o script main.py para iniciar o servidor
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=BASE_DIR
        )
        
        # Aguardar um pouco para verificar se o servidor iniciou
        time.sleep(5)
        
        if process.poll() is None:
            logger.info("Servidor backend iniciado com sucesso")
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Erro ao iniciar servidor: {stderr.decode('utf-8')}")
            return False
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
        return False

async def main():
    """Função principal"""
    logger.info("=" * 80)
    logger.info("INICIANDO ANALYST IA COM VERIFICAÇÕES AUTOMATIZADAS")
    logger.info("=" * 80)
    
    # Verificar e criar diretórios
    await verificar_diretorios()
    
    # Verificar arquivos essenciais
    await verificar_chat_history()
    
    # Reparar cache se necessário
    await reparar_cache_se_necessario()
    
    # Iniciar o servidor
    await iniciar_servidor()
    
    logger.info("=" * 80)
    logger.info("SYSTEM READY!")
    logger.info("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
