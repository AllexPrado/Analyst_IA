"""
Script para sincronização periódica do New Relic.
Este módulo implementa um sistema de coleta periódica e agendada dos dados do New Relic,
garantindo que o cache esteja sempre atualizado com dados completos.
"""

import os
import sys
import asyncio
import logging
import time
import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import signal
import concurrent.futures
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/sync_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Garantir que o diretório de logs existe
os.makedirs("logs", exist_ok=True)

# Adicionar diretórios ao path
current_dir = Path(__file__).resolve().parent
if current_dir.name != "backend":
    sys.path.append(str(current_dir))
    backend_dir = current_dir / "backend"
    if backend_dir.exists():
        sys.path.append(str(backend_dir))
        
    utils_dir = backend_dir / "utils"
    if utils_dir.exists():
        sys.path.append(str(utils_dir))

# Importar o coletor completo
try:
    from backend.utils.new_relic_full_collector import NewRelicFullCollector
except ImportError:
    try:
        from utils.new_relic_full_collector import NewRelicFullCollector
    except ImportError:
        try:
            from new_relic_full_collector import NewRelicFullCollector
        except ImportError:
            logger.error("Não foi possível importar o NewRelicFullCollector")
            sys.exit(1)

# Importar módulos de atualização do frontend
try:
    from backend.atualizar_frontend import main as atualizar_frontend
except ImportError:
    try:
        sys.path.append("backend")
        from atualizar_frontend import main as atualizar_frontend
    except ImportError:
        logger.warning("Módulo de atualização do frontend não encontrado")
        atualizar_frontend = None

class NewRelicSyncScheduler:
    """
    Implementa a sincronização periódica e completa do New Relic.
    """
    
    def __init__(self, interval_minutes=15, cache_dir="backend"):
        """
        Inicializa o agendador de sincronização.
        
        Args:
            interval_minutes: Intervalo de sincronização em minutos
            cache_dir: Diretório onde o cache será armazenado
        """
        self.interval_minutes = interval_minutes
        self.cache_dir = Path(cache_dir)
        self.collector = NewRelicFullCollector(cache_dir=cache_dir)
        self.running = False
        self.last_sync = None
        self.sync_count = 0
        self.failures = 0
        
        # Status da sincronização
        self.status = {
            "state": "initialized",
            "last_sync": None,
            "next_sync": None,
            "success_count": 0,
            "failure_count": 0,
            "last_error": None,
            "uptime": 0
        }
        
        # Arquivo de status
        self.status_file = self.cache_dir / "sync_status.json"
        
        logger.info(f"Agendador de sincronização inicializado com intervalo de {interval_minutes} minutos")
    
    async def start(self):
        """
        Inicia o agendador de sincronização.
        """
        self.running = True
        self.start_time = time.time()
        self.status["state"] = "running"
        self.save_status()
        
        logger.info("Agendador de sincronização iniciado")
        
        try:
            while self.running:
                # Atualizar status
                self.status["uptime"] = time.time() - self.start_time
                self.save_status()
                
                # Verificar se é hora de sincronizar
                should_sync = False
                
                if self.last_sync is None:
                    # Primeira sincronização
                    should_sync = True
                    logger.info("Iniciando primeira sincronização")
                else:
                    # Verificar intervalo
                    elapsed = datetime.now() - self.last_sync
                    if elapsed.total_seconds() >= (self.interval_minutes * 60):
                        should_sync = True
                        logger.info(f"Intervalo de {self.interval_minutes} minutos atingido, iniciando sincronização")
                
                if should_sync:
                    try:
                        # Atualizar status
                        self.status["state"] = "syncing"
                        self.status["next_sync"] = None
                        self.save_status()
                        
                        # Realizar sincronização
                        success = await self.perform_sync()
                        
                        # Atualizar contadores
                        if success:
                            self.sync_count += 1
                            self.status["success_count"] += 1
                        else:
                            self.failures += 1
                            self.status["failure_count"] += 1
                        
                        # Atualizar timestamp
                        self.last_sync = datetime.now()
                        self.status["last_sync"] = self.last_sync.isoformat()
                        self.status["next_sync"] = (self.last_sync + timedelta(minutes=self.interval_minutes)).isoformat()
                        self.status["state"] = "running"
                        self.save_status()
                        
                    except Exception as e:
                        logger.error(f"Erro durante sincronização: {e}")
                        logger.error(traceback.format_exc())
                        self.failures += 1
                        self.status["failure_count"] += 1
                        self.status["last_error"] = str(e)
                        self.status["state"] = "running"
                        self.save_status()
                
                # Aguardar antes da próxima verificação
                await asyncio.sleep(60)  # Verificar a cada minuto
        
        except asyncio.CancelledError:
            logger.info("Agendador de sincronização cancelado")
        
        except Exception as e:
            logger.error(f"Erro no agendador de sincronização: {e}")
            logger.error(traceback.format_exc())
            self.status["state"] = "error"
            self.status["last_error"] = str(e)
            self.save_status()
        
        finally:
            self.running = False
            self.status["state"] = "stopped"
            self.save_status()
            logger.info("Agendador de sincronização parado")
    
    async def stop(self):
        """
        Para o agendador de sincronização.
        """
        logger.info("Parando agendador de sincronização")
        self.running = False
        self.status["state"] = "stopping"
        self.save_status()
    
    async def perform_sync(self):
        """
        Realiza uma sincronização completa.
        
        Returns:
            bool: True se a sincronização foi bem-sucedida, False caso contrário
        """
        logger.info("Iniciando sincronização completa")
        start_time = time.time()
        
        try:
            # Coletar dados do New Relic
            success = await self.collector.collect_all_data()
            
            if not success:
                logger.error("Falha ao coletar dados do New Relic")
                return False
            
            # Atualizar frontend
            if atualizar_frontend:
                try:
                    logger.info("Atualizando frontend com os novos dados")
                    await atualizar_frontend()
                except Exception as e:
                    logger.error(f"Erro ao atualizar frontend: {e}")
            
            # Finalizar
            elapsed = time.time() - start_time
            logger.info(f"Sincronização completa finalizada em {elapsed:.2f} segundos")
            return True
            
        except Exception as e:
            logger.error(f"Erro durante sincronização: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def save_status(self):
        """
        Salva o status atual do agendador.
        """
        try:
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(self.status, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar status: {e}")

async def run_scheduler(interval_minutes, cache_dir, single_run=False):
    """
    Executa o agendador de sincronização.
    
    Args:
        interval_minutes: Intervalo de sincronização em minutos
        cache_dir: Diretório onde o cache será armazenado
        single_run: Se True, executa apenas uma sincronização e termina
    """
    if single_run:
        logger.info("Modo de execução única")
        collector = NewRelicFullCollector(cache_dir=cache_dir)
        success = await collector.collect_all_data()
        
        if success and atualizar_frontend:
            try:
                logger.info("Atualizando frontend com os novos dados")
                await atualizar_frontend()
            except Exception as e:
                logger.error(f"Erro ao atualizar frontend: {e}")
        
        return
    
    # Executar agendador
    scheduler = NewRelicSyncScheduler(interval_minutes=interval_minutes, cache_dir=cache_dir)
    
    # Configurar manipulador de sinal
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Sinal de encerramento recebido")
        asyncio.create_task(scheduler.stop())
    
    # Registrar manipuladores de sinal
    for signame in ('SIGINT', 'SIGTERM'):
        try:
            loop.add_signal_handler(
                getattr(signal, signame),
                signal_handler
            )
        except NotImplementedError:
            # Windows não suporta alguns sinais
            pass
    
    # Iniciar agendador
    await scheduler.start()

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Sincronizador periódico de dados do New Relic')
    parser.add_argument('--interval', type=int, default=15, help='Intervalo de sincronização em minutos')
    parser.add_argument('--cache-dir', type=str, default='backend', help='Diretório do cache')
    parser.add_argument('--single', action='store_true', help='Executar apenas uma vez e terminar')
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_scheduler(args.interval, args.cache_dir, args.single))
    except KeyboardInterrupt:
        logger.info("Programa interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro não tratado: {e}")
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
