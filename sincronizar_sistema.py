"""
Script para sincronização completa do sistema.
Este módulo implementa a sincronização avançada de todas as entidades do New Relic,
atualização do frontend e integração completa dos dados.
"""

import os
import sys
import asyncio
import logging
import traceback
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/sincronizacao.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Garantir que o diretório de logs existe
os.makedirs("logs", exist_ok=True)

# Adicionar diretórios ao path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "backend"))

# Importar os módulos necessários
from backend.utils.new_relic_full_collector import NewRelicFullCollector
from backend.utils.frontend_data_integrator import FrontendDataIntegrator

async def sincronizar_tudo(
    force_collect: bool = False,
    max_age_hours: int = 24,
    update_frontend: bool = True,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Realiza a sincronização completa do sistema:
    1. Coleta todas as entidades do New Relic se necessário
    2. Atualiza o frontend com os dados coletados
    3. Retorna estatísticas da sincronização
    
    Args:
        force_collect: Se True, força a coleta mesmo que tenha dados recentes
        max_age_hours: Idade máxima dos dados em horas antes de coletar novamente
        update_frontend: Se True, atualiza o frontend após a coleta
        verbose: Se True, exibe logs detalhados
        
    Returns:
        Dict com estatísticas da sincronização
    """
    start_time = time.time()
    stats = {
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "duration_seconds": 0,
        "collection_performed": False,
        "frontend_updated": False,
        "errors": []
    }
    
    logger.info("=== SINCRONIZAÇÃO COMPLETA DO SISTEMA ANALYST_IA ===")
    
    try:
        # 1. Verificar se é necessário coletar novamente
        need_collect = force_collect
        if not need_collect:
            need_collect = verificar_necessidade_coleta(max_age_hours)
        
        # 2. Realizar coleta de dados do New Relic
        if need_collect:
            logger.info("🔄 Iniciando coleta completa do New Relic...")
            
            # Instanciar e executar o coletor avançado
            collector = NewRelicFullCollector()
            collection_stats = await collector.collect_all_data(save_to_cache=True)
            
            stats["collection_performed"] = True
            stats["collection_stats"] = collection_stats
            
            logger.info(f"✅ Coleta completa finalizada. {collection_stats.get('entities_total', 0)} entidades coletadas.")
        else:
            logger.info("✅ Cache atualizado encontrado. Pulando coleta.")
            stats["collection_performed"] = False
            stats["collection_stats"] = {"status": "skipped", "reason": "recent_data_available"}
        
        # 3. Atualizar frontend com os dados coletados
        if update_frontend:
            logger.info("🔄 Atualizando frontend com os dados coletados...")
            
            # Instanciar e executar o integrador de frontend
            integrator = FrontendDataIntegrator()
            frontend_stats = await integrator.process_and_export_all_data()
            
            stats["frontend_updated"] = True
            stats["frontend_stats"] = frontend_stats
            
            logger.info(f"✅ Frontend atualizado com sucesso!")
        else:
            logger.info("⏩ Atualização do frontend ignorada conforme solicitado.")
            stats["frontend_updated"] = False
        
        # 4. Calcular duração total
        end_time = time.time()
        duration = int(end_time - start_time)
        stats["end_time"] = datetime.now().isoformat()
        stats["duration_seconds"] = duration
        
        logger.info(f"🏁 Sincronização completa finalizada em {duration} segundos")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erro durante a sincronização: {e}")
        logger.error(traceback.format_exc())
        
        # Atualizar estatísticas
        end_time = time.time()
        stats["end_time"] = datetime.now().isoformat()
        stats["duration_seconds"] = int(end_time - start_time)
        stats["success"] = False
        stats["errors"].append(str(e))
        stats["error_traceback"] = traceback.format_exc()
        
        return stats

def verificar_necessidade_coleta(max_age_hours: int = 24) -> bool:
    """
    Verifica se é necessário realizar uma nova coleta baseado na idade do cache.
    
    Args:
        max_age_hours: Idade máxima dos dados em horas antes de coletar novamente
        
    Returns:
        True se for necessário coletar, False caso contrário
    """
    try:
        # Verificar se o relatório de cobertura existe
        cache_dir = Path("cache") / "newrelic"
        coverage_file = cache_dir / "coverage_report.json"
        
        if not coverage_file.exists():
            logger.info("Relatório de cobertura não encontrado. Coleta necessária.")
            return True
        
        # Verificar a idade do relatório
        with open(coverage_file, "r", encoding="utf-8") as f:
            coverage_data = json.load(f)
        
        last_updated_str = coverage_data.get("timestamp")
        if not last_updated_str:
            logger.info("Timestamp não encontrado no relatório. Coleta necessária.")
            return True
        
        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            now = datetime.now()
            age_hours = (now - last_updated).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                logger.info(f"Dados com {age_hours:.1f} horas de idade (limite: {max_age_hours}). Coleta necessária.")
                return True
            else:
                logger.info(f"Dados atualizados há {age_hours:.1f} horas (dentro do limite de {max_age_hours}). Coleta não necessária.")
                return False
                
        except Exception as e:
            logger.warning(f"Erro ao analisar timestamp: {e}. Forçando coleta.")
            return True
            
    except Exception as e:
        logger.warning(f"Erro ao verificar necessidade de coleta: {e}. Forçando coleta.")
        return True

async def atualizar_frontend():
    """
    Atualiza apenas o frontend com os dados já coletados.
    """
    try:
        logger.info("🔄 Atualizando frontend com os dados existentes...")
        
        # Instanciar e executar o integrador de frontend
        integrator = FrontendDataIntegrator()
        frontend_stats = await integrator.process_and_export_all_data()
        
        logger.info(f"✅ Frontend atualizado com sucesso!")
        return {"success": True, "stats": frontend_stats}
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar frontend: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

async def main():
    """Função principal para execução direta do script"""
    import argparse
    
    # Configurar argumentos de linha de comando
    parser = argparse.ArgumentParser(description='Sincronização completa do sistema Analyst_IA')
    parser.add_argument('--force', action='store_true', help='Forçar coleta mesmo que tenha dados recentes')
    parser.add_argument('--max-age', type=int, default=24, help='Idade máxima dos dados em horas antes de coletar novamente')
    parser.add_argument('--no-frontend', action='store_true', help='Não atualizar o frontend após a coleta')
    parser.add_argument('--frontend-only', action='store_true', help='Apenas atualizar o frontend, sem coletar dados')
    parser.add_argument('--verbose', action='store_true', help='Exibir logs detalhados')
    
    args = parser.parse_args()
    
    if args.frontend_only:
        # Apenas atualizar o frontend
        await atualizar_frontend()
    else:
        # Sincronizar tudo
        await sincronizar_tudo(
            force_collect=args.force, 
            max_age_hours=args.max_age,
            update_frontend=not args.no_frontend,
            verbose=args.verbose
        )

if __name__ == "__main__":
    asyncio.run(main())
