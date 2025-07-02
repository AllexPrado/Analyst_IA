#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para agendar a sincronização periódica de dados reais do New Relic.
Este script executa em segundo plano e sincroniza os dados periodicamente.
"""

import os
import sys
import time
import logging
import argparse
import signal
import traceback
import asyncio
import json
from datetime import datetime, timedelta
import subprocess
from typing import Dict, Any, List, Optional
import threading

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/sincronizacao_periodica.log", mode='a')
    ]
)

logger = logging.getLogger(__name__)
os.makedirs("logs", exist_ok=True)

# Controle de sincronização
sincronizacao_ativa = True
ultima_sincronizacao = None
intervalo_padrao = 30  # minutos

def executar_sincronizacao():
    """Executa a sincronização de dados do New Relic"""
    global ultima_sincronizacao
    
    try:
        logger.info("Iniciando sincronização de dados do New Relic...")
        
        # Verificar credenciais
        account_id = os.environ.get("NEW_RELIC_ACCOUNT_ID")
        api_key = os.environ.get("NEW_RELIC_API_KEY")
        
        if account_id and api_key:
            # Usando dados reais
            logger.info("Credenciais do New Relic encontradas. Usando dados reais.")
            cmd = [sys.executable, "integrar_dados_reais_newrelic.py"]
        else:
            # Usando dados simulados
            logger.info("Credenciais do New Relic não encontradas. Usando dados simulados.")
            cmd = [sys.executable, "integrar_dados_reais_newrelic.py", "--simulated"]
        
        # Executar o script de integração
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Sincronização concluída com sucesso!")
            # Atualizar timestamp da última sincronização
            ultima_sincronizacao = datetime.now()
            
            # Salvar log da sincronização
            with open("logs/ultima_sincronizacao.json", 'w') as f:
                json.dump({
                    "timestamp": ultima_sincronizacao.isoformat(),
                    "status": "success",
                    "modo": "real" if (account_id and api_key) else "simulado"
                }, f, indent=2)
        else:
            logger.error(f"Erro na sincronização: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Erro ao executar sincronização: {e}")
        traceback.print_exc()

def tratar_sinal(sig, frame):
    """Trata sinais de interrupção (CTRL+C)"""
    global sincronizacao_ativa
    logger.info("Recebido sinal de interrupção. Encerrando sincronização periódica...")
    sincronizacao_ativa = False
    sys.exit(0)

def sincronizacao_loop(intervalo_minutos):
    """Loop principal para sincronização periódica"""
    global sincronizacao_ativa, ultima_sincronizacao
    
    logger.info(f"Iniciando loop de sincronização a cada {intervalo_minutos} minutos")
    
    while sincronizacao_ativa:
        # Executar sincronização
        executar_sincronizacao()
        
        # Aguardar pelo próximo intervalo
        logger.info(f"Próxima sincronização em {intervalo_minutos} minutos")
        
        # Esperar em pequenos intervalos para poder interromper suavemente
        espera_total = intervalo_minutos * 60  # segundos
        intervalo_verificacao = 10  # segundos
        
        for _ in range(espera_total // intervalo_verificacao):
            if not sincronizacao_ativa:
                break
            time.sleep(intervalo_verificacao)
            
        # Se ainda precisar esperar mais um pouco
        tempo_restante = espera_total % intervalo_verificacao
        if tempo_restante > 0 and sincronizacao_ativa:
            time.sleep(tempo_restante)

def iniciar_sincronizacao_background(intervalo_minutos=None):
    """Inicia a sincronização em segundo plano"""
    if not intervalo_minutos:
        intervalo_minutos = intervalo_padrao
        
    # Criar uma thread para executar a sincronização em segundo plano
    thread = threading.Thread(target=sincronizacao_loop, args=(intervalo_minutos,))
    thread.daemon = True
    thread.start()
    
    return thread

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Sincronizador periódico de dados do New Relic")
    parser.add_argument('--intervalo', type=int, default=intervalo_padrao,
                       help=f"Intervalo em minutos entre sincronizações (padrão: {intervalo_padrao})")
    parser.add_argument('--once', action='store_true',
                       help="Executar apenas uma sincronização e sair")
    args = parser.parse_args()
    
    # Registrar handler de sinais
    signal.signal(signal.SIGINT, tratar_sinal)
    signal.signal(signal.SIGTERM, tratar_sinal)
    
    if args.once:
        logger.info("Executando uma única sincronização...")
        executar_sincronizacao()
        logger.info("Sincronização única concluída.")
        return
        
    try:
        logger.info(f"Iniciando sincronização periódica a cada {args.intervalo} minutos...")
        logger.info("Pressione CTRL+C para encerrar")
        
        # Executar loop de sincronização
        sincronizacao_loop(args.intervalo)
    except KeyboardInterrupt:
        logger.info("Sincronização encerrada pelo usuário")
    except Exception as e:
        logger.error(f"Erro na sincronização: {e}")
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
