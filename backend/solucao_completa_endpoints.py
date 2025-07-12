#!/usr/bin/env python
"""
Solução completa para o problema dos endpoints /agno (ATUALIZADA)
Este script:
1. Corrige o arquivo main.py
2. Reinicia o servidor (opcional)
3. Testa os endpoints
"""
import os
import sys
import subprocess
import time
import logging
import re
import json
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("solucao_completa")

def executar_comando(comando, descricao, capturar_saida=True):
    """Executa um comando e retorna o resultado"""
    logger.info(f"Executando: {descricao}")
    
    try:
        if capturar_saida:
            resultado = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if resultado.returncode == 0:
                logger.info(f"Comando executado com sucesso: {descricao}")
                return True, resultado.stdout
            else:
                logger.error(f"Erro ao executar {descricao}: {resultado.stderr}")
                return False, resultado.stderr
        else:
            # Executar sem capturar saída (mostra em tempo real)
            subprocess.run(
                comando,
                shell=True,
                check=True
            )
            return True, ""
    except Exception as e:
        logger.error(f"Erro ao executar {descricao}: {e}")
        return False, str(e)

def finalizar_processos_na_porta(porta=8000):
    """Finaliza quaisquer processos que estejam usando a porta especificada."""
    logger.info(f"Verificando processos na porta {porta}...")
    
    try:
        # No Windows, usamos o comando netstat
        resultado = subprocess.run(
            f'netstat -ano | findstr :{porta}',
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if resultado.stdout:
            linhas = resultado.stdout.strip().split('\n')
            for linha in linhas:
                if f":{porta}" in linha and "LISTENING" in linha:
                    partes = linha.strip().split()
                    pid = partes[-1]
                    logger.info(f"Finalizando processo PID {pid} na porta {porta}")
                    try:
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=True)
                        logger.info(f"Processo {pid} finalizado com sucesso")
                        return True
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"Erro ao finalizar processo {pid}: {e}")
            return False
        else:
            logger.info(f"Nenhum processo encontrado na porta {porta}")
            return True
    except Exception as e:
        logger.error(f"Erro ao verificar processos: {e}")
        return False

def main():
    """Função principal para executar a solução completa."""
    logger.info("=" * 60)
    logger.info("SOLUÇÃO COMPLETA PARA ENDPOINTS AGNO")
    logger.info("=" * 60)
    
    # Diretório raiz do projeto
    diretorio_projeto = os.path.abspath(os.path.dirname(__file__))
    os.chdir(diretorio_projeto)
    logger.info(f"Diretório do projeto: {diretorio_projeto}")
    
    # 1. Instalar o middleware de proxy
    logger.info("1. Instalando o middleware de proxy...")
    sucesso, saida = executar_comando(
        "python instalar_middleware_proxy.py",
        "Instalação do middleware de proxy",
        False
    )
    
    if not sucesso:
        logger.error("Falha ao instalar o middleware de proxy. Abortando.")
        return 1
        
    # 2. Finalizar processos existentes na porta
    logger.info("2. Finalizando processos na porta 8000...")
    if not finalizar_processos_na_porta(8000):
        logger.warning("Alguns processos na porta 8000 podem ainda estar em execução.")
    
    # 3. Iniciar o servidor
    logger.info("3. Iniciando o servidor...")
    servidor_comando = "start powershell -NoExit -Command \"python start_unified.py\""
    sucesso, _ = executar_comando(servidor_comando, "Iniciar servidor", False)
    
    if not sucesso:
        logger.error("Falha ao iniciar o servidor. Abortando.")
        return 1
        
    # 4. Aguardar o servidor inicializar
    logger.info("4. Aguardando o servidor inicializar (15 segundos)...")
    time.sleep(15)
    
    # 5. Testar os endpoints
    logger.info("5. Testando endpoints...")
    sucesso, _ = executar_comando("python testar_agno_endpoints.py", "Teste de endpoints", False)
    
    if not sucesso:
        logger.warning("Alguns testes de endpoint falharam.")
        
    logger.info("=" * 60)
    logger.info("PROCESSO DE CORREÇÃO CONCLUÍDO")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Verifique os resultados dos testes acima.")
    logger.info("Se algum endpoint ainda não estiver funcionando, verifique os logs do servidor.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
