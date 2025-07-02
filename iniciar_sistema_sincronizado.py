"""
Script para iniciar o sistema completo (backend e frontend) com sincronização avançada.
Este script sincroniza completamente todos os dados do New Relic (entidades, métricas, 
logs, dashboards, alertas), atualiza o frontend e inicia os serviços.
"""

import os
import sys
import asyncio
import subprocess
import logging
import json
from pathlib import Path
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/inicializacao.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Garantir que o diretório de logs existe
os.makedirs("logs", exist_ok=True)

# Adicionar diretórios ao path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

async def sincronizar_entidades(
    force_sync: bool = False, 
    max_age_hours: int = 24
) -> Dict[str, Any]:
    """
    Sincroniza todos os dados do New Relic usando o coletor avançado.
    
    Args:
        force_sync: Se True, força a sincronização mesmo que tenha dados recentes
        max_age_hours: Idade máxima dos dados em horas antes de sincronizar novamente
        
    Returns:
        Dict com estatísticas da sincronização
    """
    try:
        # Importar o script de sincronização
        from sincronizar_sistema import sincronizar_tudo
        
        logger.info("🔄 Iniciando sincronização completa do New Relic...")
        stats = await sincronizar_tudo(
            force_collect=force_sync,
            max_age_hours=max_age_hours,
            update_frontend=True
        )
        
        if "errors" in stats and stats["errors"]:
            logger.error(f"❌ Falha na sincronização completa: {stats['errors'][0]}")
            return stats
        else:
            logger.info("✅ Sincronização completa concluída com sucesso!")
            
            # Mostrar estatísticas
            if "collection_stats" in stats and stats["collection_stats"]:
                cs = stats["collection_stats"]
                logger.info(f"Estatísticas da coleta:")
                logger.info(f"  - Entidades coletadas: {cs.get('entities_total', 'N/A')}")
                logger.info(f"  - Dashboards: {cs.get('dashboards', 'N/A')}")
                logger.info(f"  - Políticas de alerta: {cs.get('alert_policies', 'N/A')}")
            
            return stats
    except Exception as e:
        logger.error(f"❌ Erro ao sincronizar entidades: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "errors": [str(e)], "timestamp": datetime.now().isoformat()}

def iniciar_backend(check_cache: bool = True):
    """
    Inicia o servidor backend.
    
    Args:
        check_cache: Se True, executa a verificação e correção do cache antes de iniciar
    """
    logger.info("🚀 Iniciando servidor backend...")
    
    try:
        backend_dir = current_dir / "backend"
        os.chdir(backend_dir)
        
        # Executar verificação de cache se solicitado
        if check_cache:
            logger.info("Verificando e corrigindo cache...")
            proc = subprocess.run(
                ["python", "check_and_fix_cache.py"],
                shell=True,
                cwd=backend_dir,
                capture_output=True,
                text=True
            )
            
            if proc.returncode == 0:
                logger.info("✅ Cache verificado e corrigido com sucesso")
            else:
                logger.warning(f"⚠️ Verificação de cache retornou código {proc.returncode}")
                logger.warning(f"Saída: {proc.stdout}")
                logger.error(f"Erro: {proc.stderr}")
        
        # Dar tempo para o cache ser verificado
        time.sleep(2)
        
        # Iniciar o servidor backend
        backend_process = subprocess.Popen(
            ["python", "main.py"],
            shell=True,
            cwd=backend_dir
        )
        
        # Voltar para o diretório original
        os.chdir(current_dir)
        
        logger.info("✅ Servidor backend iniciado!")
        return backend_process
    except Exception as e:
        logger.error(f"Erro ao iniciar backend: {e}")
        return None

def iniciar_frontend():
    """Inicia o servidor frontend."""
    logger.info("Iniciando servidor frontend...")
    
    try:
        frontend_dir = current_dir / "frontend"
        os.chdir(frontend_dir)
        
        # Iniciar o servidor frontend
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            shell=True,
            cwd=frontend_dir
        )
        
        # Voltar para o diretório original
        os.chdir(current_dir)
        
        logger.info("✅ Servidor frontend iniciado!")
        return frontend_process
    except Exception as e:
        logger.error(f"Erro ao iniciar frontend: {e}")
        return None

async def main():
    """Função principal para iniciar todo o sistema com sincronização completa."""
    import argparse
    
    # Configurar argumentos de linha de comando
    parser = argparse.ArgumentParser(description='Iniciar sistema Analyst_IA com sincronização completa')
    parser.add_argument('--no-sync', action='store_true', help='Pular sincronização de dados')
    parser.add_argument('--force-sync', action='store_true', help='Forçar sincronização completa')
    parser.add_argument('--max-age', type=int, default=24, help='Idade máxima dos dados em horas antes de sincronizar')
    parser.add_argument('--no-cache-check', action='store_true', help='Pular verificação de cache')
    args = parser.parse_args()
    
    logger.info("=== INICIANDO SISTEMA ANALYST IA COMPLETO ===")
    start_time = time.time()
    
    try:
        # Passo 1: Sincronizar dados com New Relic
        if not args.no_sync:
            sync_stats = await sincronizar_entidades(
                force_sync=args.force_sync,
                max_age_hours=args.max_age
            )
            
            if "errors" in sync_stats and sync_stats["errors"]:
                logger.warning("⚠️ Sincronização teve erros, mas o sistema continuará inicializando")
        else:
            logger.info("⏩ Sincronização ignorada conforme solicitado")
        
        # Passo 2: Iniciar backend
        backend_process = iniciar_backend(check_cache=not args.no_cache_check)
        
        if backend_process:
            # Dar tempo para o backend inicializar
            logger.info("⏳ Aguardando backend inicializar...")
            time.sleep(5)
            
            # Passo 3: Iniciar frontend
            frontend_process = iniciar_frontend()
            
            if frontend_process:
                end_time = time.time()
                duration = int(end_time - start_time)
                
                logger.info("\n" + "=" * 70)
                logger.info(f"✅ SISTEMA ANALYST_IA INICIADO COM SUCESSO! ({duration}s)")
                logger.info(f"📊 Backend: http://localhost:8000")
                logger.info(f"🌐 Frontend: http://localhost:5173")
                logger.info(f"📁 Cache: {current_dir / 'cache' / 'newrelic'}")
                logger.info(f"📝 Logs: {current_dir / 'logs'}")
                logger.info("=" * 70)
                
                # Salvar status de inicialização
                status_file = current_dir / "logs" / "system_status.json"
                status = {
                    "timestamp": datetime.now().isoformat(),
                    "status": "running",
                    "backend_pid": backend_process.pid,
                    "frontend_pid": frontend_process.pid,
                    "startup_time_seconds": duration,
                    "endpoints": {
                        "backend": "http://localhost:8000",
                        "frontend": "http://localhost:5173",
                        "api_docs": "http://localhost:8000/docs"
                    }
                }
                
                with open(status_file, "w", encoding="utf-8") as f:
                    json.dump(status, f, indent=2)
                
                # Aguardar os processos
                try:
                    logger.info("Sistema em execução. Pressione Ctrl+C para encerrar.")
                    while True:
                        backend_status = backend_process.poll()
                        frontend_status = frontend_process.poll()
                        
                        if backend_status is not None:
                            logger.error(f"⛔ Processo do backend encerrado com código {backend_status}")
                            break
                            
                        if frontend_status is not None:
                            logger.error(f"⛔ Processo do frontend encerrado com código {frontend_status}")
                            break
                            
                        await asyncio.sleep(2)
                        
                except KeyboardInterrupt:
                    logger.info("🛑 Encerrando sistema (Ctrl+C detectado)...")
                    if backend_process:
                        backend_process.terminate()
                    if frontend_process:
                        frontend_process.terminate()
                        
                    # Atualizar status
                    status["status"] = "stopped"
                    status["end_time"] = datetime.now().isoformat()
                    
                    with open(status_file, "w", encoding="utf-8") as f:
                        json.dump(status, f, indent=2)
                        
                    logger.info("✅ Sistema encerrado com sucesso!")
            else:
                logger.error("❌ Falha ao iniciar frontend")
                if backend_process:
                    backend_process.terminate()
        else:
            logger.error("❌ Falha ao iniciar backend")
            
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar sistema: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Tentar encerrar quaisquer processos em execução
        try:
            if 'backend_process' in locals() and backend_process:
                backend_process.terminate()
            if 'frontend_process' in locals() and frontend_process:
                frontend_process.terminate()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
