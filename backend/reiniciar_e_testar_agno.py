"""
Script para reiniciar o servidor unificado e verificar se os endpoints do Agno
estão funcionando corretamente após o reinício.
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("reiniciar_servidor")

def finalizar_processos_na_porta(porta=8000):
    """Finaliza quaisquer processos que estejam usando a porta especificada."""
    try:
        logger.info(f"Verificando processos na porta {porta}...")
        # No Windows, usamos o comando netstat
        resultado = subprocess.run(
            f'netstat -ano | findstr :{porta}',
            shell=True,
            capture_output=True,
            text=True
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

def iniciar_servidor():
    """Inicia o servidor unificado em um processo separado."""
    logger.info("Iniciando servidor unificado...")
    
    try:
        script_start = "start_unified.py"
        if not os.path.exists(script_start):
            logger.warning(f"Script {script_start} não encontrado. Tentando iniciar unified_backend.py diretamente.")
            script_start = "unified_backend.py"
        
        # Iniciar o servidor em uma nova janela do PowerShell
        comando = f"start powershell -NoExit -Command \"python {script_start}\""
        subprocess.run(comando, shell=True)
        
        logger.info("Comando para iniciar servidor executado.")
        logger.info("Aguardando o servidor inicializar (10 segundos)...")
        time.sleep(10)
        
        return True
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
        return False

def testar_endpoints():
    """Executa o script de teste de endpoints."""
    logger.info("Testando endpoints Agno IA...")
    
    try:
        # Configurar a execução do script com a codificação correta
        comando = "python testar_agno_endpoints.py"
        
        # Executar o comando diretamente para exibir saída em tempo real
        logger.info("Executando testes de endpoint...")
        process = subprocess.Popen(
            comando,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # Capturar saída
        stdout, stderr = process.communicate()
        
        print("\nRESULTADO DOS TESTES:")
        print(stdout)
        
        if "Todos os tipos de endpoints estão funcionando" in stdout:
            logger.info("[OK] Todos os endpoints estão funcionando corretamente!")
            return True
        else:
            logger.warning("[AVISO] Alguns endpoints ainda apresentam problemas.")
            if stderr:
                logger.error(f"Erros: {stderr}")
            return False
    except Exception as e:
        logger.error(f"Erro ao executar testes: {e}")
        return False

def main():
    """Função principal para reiniciar o servidor e testar endpoints."""
    logger.info("=" * 60)
    logger.info("REINICIALIZAÇÃO DO SERVIDOR E TESTE DE ENDPOINTS")
    logger.info("=" * 60)
    
    # 1. Finalizar processos existentes na porta
    if not finalizar_processos_na_porta():
        logger.warning("Não foi possível finalizar todos os processos na porta 8000.")
        escolha = input("Deseja continuar mesmo assim? (s/n): ")
        if escolha.lower() != 's':
            logger.info("Operação cancelada pelo usuário.")
            return 1
    
    # 2. Iniciar o servidor
    if not iniciar_servidor():
        logger.error("Falha ao iniciar o servidor.")
        return 1
    
    # 3. Testar os endpoints
    logger.info("Servidor iniciado. Testando endpoints...")
    if not testar_endpoints():
        logger.warning("Nem todos os endpoints foram verificados com sucesso.")
        return 1
    
    logger.info("=" * 60)
    logger.info("✨ PROCESSO CONCLUÍDO COM SUCESSO! ✨")
    logger.info("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
