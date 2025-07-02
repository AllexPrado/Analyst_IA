#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import asyncio
import json
import logging
import time
import argparse
from datetime import datetime, timedelta

# Configurar path para importar módulos do backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Importar o coletor avançado
from utils.advanced_newrelic_collector import AdvancedNewRelicCollector

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'sincronizar_newrelic_avancado.log'), mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Certificar-se de que o diretório de logs existe
os.makedirs(os.path.join(os.path.dirname(__file__), 'logs'), exist_ok=True)

# Diretório do cache
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'backend', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

async def sincronizar_dados(full_sync=False, report_file=None):
    """
    Sincroniza dados do New Relic para o cache local.
    
    Args:
        full_sync: Se True, faz uma sincronização completa, caso contrário, faz uma sincronização incremental
        report_file: Caminho para salvar o relatório de cobertura
    """
    logger.info(f"Iniciando sincronização {'completa' if full_sync else 'incremental'} do New Relic")
    
    start_time = datetime.now()
    
    try:
        collector = AdvancedNewRelicCollector()
        
        if full_sync:
            logger.info("Executando sincronização completa - todos os dados serão coletados")
            data = await collector.collect_full_entity_data()
        else:
            logger.info("Executando sincronização incremental - apenas dados atualizados serão coletados")
            # Podemos implementar uma lógica mais sofisticada de sincronização incremental no futuro
            # Por enquanto, coletar apenas os principais dados
            
            data = {
                "collected_at": datetime.now().isoformat(),
                "entities": {}
            }
            
            # Coletar entidades por domínio
            domains = ["APM", "BROWSER", "MOBILE", "INFRA", "SYNTH"]
            for domain in domains:
                logger.info(f"Coletando entidades para domínio: {domain}")
                data["entities"][domain] = await collector.fetch_entities_by_domain(domain)
            
            # Coletar dados de alertas (são relativamente pequenos e mudam frequentemente)
            logger.info("Coletando alertas")
            data["alerts"] = await collector.fetch_alerts()
            
            # Coletar uma amostra de logs recentes
            logger.info("Coletando amostra de logs recentes")
            data["logs"] = {"sample": await collector.fetch_logs_sample(limit=50)}
        
        # Calcular tempo decorrido
        elapsed_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Sincronização concluída em {elapsed_time:.2f} segundos")
        
        # Adicionar detalhes da sincronização
        data["sync_info"] = {
            "sync_type": "full" if full_sync else "incremental",
            "start_time": start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "elapsed_seconds": elapsed_time
        }
        
        # Salvar os dados em cache
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cache_filename = f"newrelic_data_{'full' if full_sync else 'incremental'}_{timestamp}.json"
        cache_path = os.path.join(CACHE_DIR, cache_filename)
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Dados salvos em: {cache_path}")
        
        # Criar um link simbólico para o arquivo mais recente (ou cópia em sistemas Windows)
        latest_path = os.path.join(CACHE_DIR, "newrelic_data_latest.json")
        
        # No Windows não há link simbólico fácil, então criar uma cópia
        if os.path.exists(latest_path):
            os.remove(latest_path)
            
        with open(cache_path, 'r', encoding='utf-8') as f_source:
            with open(latest_path, 'w', encoding='utf-8') as f_dest:
                f_dest.write(f_source.read())
        
        logger.info(f"Arquivo 'latest' atualizado em: {latest_path}")
        
        # Salvar relatório de cobertura se solicitado
        if report_file:
            coverage_report = {
                "timestamp": datetime.now().isoformat(),
                "sync_type": "full" if full_sync else "incremental",
                "elapsed_seconds": elapsed_time
            }
            
            if "coverage_report" in data:
                coverage_report["coverage"] = data["coverage_report"]
                
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(coverage_report, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Relatório de cobertura salvo em: {report_file}")
        
        return True, {"elapsed_seconds": elapsed_time, "cache_path": cache_path}
        
    except Exception as e:
        logger.error(f"Erro durante a sincronização: {e}")
        return False, {"error": str(e)}

async def sincronizar_periodicamente(intervalo_minutos=60, total_execucoes=None):
    """
    Executa sincronização periódica em um intervalo especificado.
    
    Args:
        intervalo_minutos: Intervalo em minutos entre sincronizações
        total_execucoes: Número máximo de execuções (None para executar indefinidamente)
    """
    logger.info(f"Iniciando sincronização periódica a cada {intervalo_minutos} minutos")
    
    execucoes = 0
    
    try:
        while total_execucoes is None or execucoes < total_execucoes:
            # Primeira execução é uma sincronização completa, depois incrementais
            full_sync = (execucoes == 0)
            
            # Gerar nome de arquivo para relatório
            report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(
                os.path.dirname(__file__), 
                'reports', 
                f"coverage_report_{report_timestamp}.json"
            )
            
            # Certificar-se de que o diretório reports existe
            os.makedirs(os.path.join(os.path.dirname(__file__), 'reports'), exist_ok=True)
            
            # Executar sincronização
            logger.info(f"Executando sincronização #{execucoes+1}" + 
                        (f" (restantes: {total_execucoes - execucoes - 1})" if total_execucoes else ""))
            
            success, result = await sincronizar_dados(full_sync=full_sync, report_file=report_file)
            
            if success:
                logger.info(f"Sincronização #{execucoes+1} concluída com sucesso em {result['elapsed_seconds']:.2f} segundos")
            else:
                logger.error(f"Sincronização #{execucoes+1} falhou: {result.get('error', 'Erro desconhecido')}")
            
            execucoes += 1
            
            # Verificar se deve continuar
            if total_execucoes is not None and execucoes >= total_execucoes:
                break
                
            # Aguardar até a próxima execução
            next_run = datetime.now() + timedelta(minutes=intervalo_minutos)
            logger.info(f"Próxima sincronização agendada para: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Aguardar o intervalo (em segundos)
            await asyncio.sleep(intervalo_minutos * 60)
            
    except KeyboardInterrupt:
        logger.info("Sincronização periódica interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro durante sincronização periódica: {e}")

def main():
    parser = argparse.ArgumentParser(description="Sincronização avançada de dados do New Relic")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--once", action="store_true", help="Executar apenas uma sincronização completa")
    group.add_argument("--periodic", action="store_true", help="Executar sincronização periódica")
    
    parser.add_argument("--interval", type=int, default=60, 
                        help="Intervalo em minutos entre sincronizações periódicas (padrão: 60)")
    parser.add_argument("--executions", type=int, default=None,
                        help="Número de execuções para sincronização periódica (padrão: sem limite)")
    
    args = parser.parse_args()
    
    if args.once:
        # Executar uma vez com sincronização completa
        asyncio.run(sincronizar_dados(full_sync=True, 
                                      report_file="coverage_report_full.json"))
    elif args.periodic:
        # Executar sincronização periódica
        asyncio.run(sincronizar_periodicamente(
            intervalo_minutos=args.interval,
            total_execucoes=args.executions
        ))
    else:
        # Se nenhuma opção foi especificada, mostrar ajuda
        parser.print_help()

if __name__ == "__main__":
    main()
