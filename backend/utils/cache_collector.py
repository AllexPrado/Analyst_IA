"""
Implementação completa do coletor de contexto do New Relic.
Este módulo implementa funções para coletar contexto completo do New Relic,
incluindo entidades e suas métricas detalhadas.
"""

import os
import logging
import asyncio
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

from .newrelic_collector import (
    NewRelicCollector, NEW_RELIC_API_KEY, NEW_RELIC_ACCOUNT_ID,
    rate_controller, DOMINIOS_NEWRELIC, DOMINIOS_IGNORADOS
)

logger = logging.getLogger(__name__)

# Consultas NRQL para coletar métricas detalhadas para cada tipo de entidade
METRICAS_POR_DOMINIO = {
    "APM": {
        "apdex": "SELECT latest(apdex) FROM Metric WHERE entity.guid = '{guid}' {periodo}",
        "response_time": "SELECT average(duration) FROM Transaction WHERE entityGuid = '{guid}' {periodo}",
        "error_rate": "SELECT percentage(count(*), WHERE error is true) FROM Transaction WHERE entityGuid = '{guid}' {periodo}",
        "throughput": "SELECT rate(count(*), 1 minute) FROM Transaction WHERE entityGuid = '{guid}' {periodo}",
        "recent_errors": "SELECT * FROM TransactionError WHERE entityGuid = '{guid}' {periodo} LIMIT 5",
        "database_time": "SELECT average(databaseDuration) FROM Transaction WHERE entityGuid = '{guid}' {periodo}",
        "top_endpoints": "SELECT count(*) FROM Transaction WHERE entityGuid = '{guid}' {periodo} FACET name LIMIT 5"
    },
    "BROWSER": {
        "page_load_time": "SELECT average(duration) FROM PageView WHERE entityGuid = '{guid}' {periodo}",
        "ajax_response_time": "SELECT average(duration) FROM Ajax WHERE entityGuid = '{guid}' {periodo}",
        "ajax_error_rate": "SELECT percentage(count(*), WHERE error is true) FROM Ajax WHERE entityGuid = '{guid}' {periodo}",
        "js_errors": "SELECT count(*) FROM JavaScriptError WHERE entityGuid = '{guid}' {periodo}",
        "top_pages": "SELECT count(*) FROM PageView WHERE entityGuid = '{guid}' {periodo} FACET pageUrl LIMIT 5"
    },
    "INFRA": {
        "cpu_usage": "SELECT average(cpuPercent) FROM SystemSample WHERE entityGuid = '{guid}' {periodo}",
        "memory_usage": "SELECT average(memoryUsedPercent) FROM SystemSample WHERE entityGuid = '{guid}' {periodo}",
        "disk_usage": "SELECT average(diskUsedPercent) FROM SystemSample WHERE entityGuid = '{guid}' {periodo}",
        "disk_io": "SELECT average(ioUtilizationPercent) FROM SystemSample WHERE entityGuid = '{guid}' {periodo}",
        "network_io": "SELECT average(transmitBytesPerSecond + receiveBytesPerSecond) FROM SystemSample WHERE entityGuid = '{guid}' {periodo}"
    },
    "DB": {
        "queries_per_second": "SELECT average(queriesPerSecond) FROM DatastoreSample WHERE entityGuid = '{guid}' {periodo}",
        "connection_count": "SELECT average(connectionCount) FROM DatastoreSample WHERE entityGuid = '{guid}' {periodo}",
        "slow_queries": "SELECT count(*) FROM SlowQuery WHERE entityGuid = '{guid}' {periodo}",
        "db_size": "SELECT average(dbSize) FROM DatastoreSample WHERE entityGuid = '{guid}' {periodo}",
        "recent_slowest": "SELECT * FROM SlowQuery WHERE entityGuid = '{guid}' {periodo} LIMIT 3"
    },
    "MOBILE": {
        "crash_rate": "SELECT count(*) FROM Mobile WHERE entityGuid = '{guid}' AND crashCount > 0 {periodo}",
        "network_errors": "SELECT count(*) FROM MobileRequest WHERE entityGuid = '{guid}' AND error = true {periodo}",
        "http_errors": "SELECT count(*) FROM MobileRequestError WHERE entityGuid = '{guid}' {periodo}",
        "session_count": "SELECT count(*) FROM MobileSession WHERE entityGuid = '{guid}' {periodo}",
        "top_sessions": "SELECT duration FROM MobileSession WHERE entityGuid = '{guid}' {periodo} LIMIT 5"
    },
    "IOT": {
        "message_count": "SELECT count(*) FROM IoTDeviceSample WHERE entityGuid = '{guid}' {periodo}",
        "device_temperature": "SELECT average(temperature) FROM IoTDeviceSample WHERE entityGuid = '{guid}' {periodo}",
        "device_errors": "SELECT count(*) FROM IoTDeviceError WHERE entityGuid = '{guid}' {periodo}",
        "device_connected": "SELECT latest(connected) FROM IoTDeviceSample WHERE entityGuid = '{guid}' {periodo}",
        "recent_errors": "SELECT * FROM IoTDeviceError WHERE entityGuid = '{guid}' {periodo} LIMIT 5"
    },
    "SERVERLESS": {
        "invocation_count": "SELECT count(*) FROM ServerlessSample WHERE entityGuid = '{guid}' {periodo}",
        "duration_avg": "SELECT average(duration) FROM ServerlessSample WHERE entityGuid = '{guid}' {periodo}",
        "error_rate": "SELECT percentage(count(*), WHERE error IS TRUE) FROM ServerlessSample WHERE entityGuid = '{guid}' {periodo}",
        "cold_starts": "SELECT count(*) FROM ServerlessSample WHERE entityGuid = '{guid}' AND coldStart = 'true' {periodo}"
    },
    "SYNTH": {
        "success_rate": "SELECT percentage(count(*), WHERE result = 'SUCCESS') FROM SyntheticCheck WHERE entityGuid = '{guid}' {periodo}",
        "response_time": "SELECT average(duration) FROM SyntheticCheck WHERE entityGuid = '{guid}' {periodo}",
        "recent_failures": "SELECT * FROM SyntheticCheck WHERE entityGuid = '{guid}' AND result != 'SUCCESS' {periodo} LIMIT 5"
    },
    "EXT": {
        "status": "SELECT latest(status) FROM ExternalServiceSample WHERE entityGuid = '{guid}' {periodo}",
        "response_time": "SELECT average(duration) FROM ExternalServiceSample WHERE entityGuid = '{guid}' {periodo}",
        "error_rate": "SELECT percentage(count(*), WHERE error IS TRUE) FROM ExternalServiceSample WHERE entityGuid = '{guid}' {periodo}"
    }
}

# Períodos de tempo para coleta de métricas
PERIODOS = {
    "30min": "SINCE 30 MINUTES AGO",
    "24h": "SINCE 24 HOURS AGO",
    "7d": "SINCE 7 DAYS AGO",
    "30d": "SINCE 30 DAYS AGO"
}

async def coletar_metricas_entidade(entidade: Dict[str, Any], collector: NewRelicCollector) -> Dict[str, Any]:
    """
    Coleta métricas detalhadas para uma entidade específica.
    
    Args:
        entidade: Dados básicos da entidade (guid, name, domain, etc.)
        collector: Instância do coletor New Relic para executar queries
        
    Returns:
        Métricas coletadas para diferentes períodos de tempo
    """
    guid = entidade.get("guid")
    dominio = entidade.get("domain")
    
    # Se não tem GUID ou domínio, retorna vazio
    if not guid or not dominio:
        return {}
    
    # Se domínio não está no mapa de consultas, retorna vazio
    if dominio not in METRICAS_POR_DOMINIO:
        return {}
    
    metricas = {
        "30min": {},
        "24h": {},
        "7d": {},
        "30d": {}
    }
    
    # Para cada período, coletar as métricas
    for periodo_key, periodo_nrql in PERIODOS.items():
        # Para cada métrica do domínio, executar a query NRQL
        for metrica_key, query_template in METRICAS_POR_DOMINIO[dominio].items():
            try:
                # Formatar a query com o GUID da entidade e o período
                query = query_template.format(guid=guid, periodo=periodo_nrql)
                
                # Executar a query NRQL
                resultado = await collector.execute_nrql_query(query)
                
                # Armazenar o resultado
                metricas[periodo_key][metrica_key] = resultado
            except Exception as e:
                # Em caso de erro, registra e continua
                logger.warning(f"Erro ao coletar métrica {metrica_key} para entidade {guid}: {e}")
                metricas[periodo_key][metrica_key] = None
                
                # Se houve muitos erros consecutivos, não tenta mais métricas para esta entidade
                if rate_controller.consecutive_failures > 5:
                    logger.error(f"Muitos erros consecutivos, abortando coleta para entidade {guid}")
                    return metricas
    
    return metricas

def entidade_tem_dados(entidade: Dict[str, Any], min_metrics: int = 3) -> bool:
    """
    Verifica se uma entidade tem dados mínimos para ser considerada válida.
    
    Args:
        entidade: Dados da entidade incluindo métricas
        min_metrics: Número mínimo de métricas com valores para considerar a entidade válida
        
    Returns:
        True se a entidade tem dados suficientes, False caso contrário
    """
    if not entidade:
        return False
    
    metricas = entidade.get("metricas", {})
    if not metricas:
        return False
    
    # Verifica o período mais recente (30min)
    metricas_recentes = metricas.get("30min", {})
    if not metricas_recentes:
        # Se não tem métricas recentes, verifica as últimas 24h
        metricas_recentes = metricas.get("24h", {})
    
    # Conta quantas métricas têm dados válidos
    metricas_com_dados = sum(1 for valor in metricas_recentes.values() if valor is not None and valor != {})
    
    return metricas_com_dados >= min_metrics

async def coletar_contexto_completo(top_n=5):
    """
    Coleta contexto completo com dados do New Relic, incluindo entidades e suas métricas.
    Implementa fallback seguro em caso de rate limit massivo.
    
    Args:
        top_n: Número máximo de resultados para consultas paginadas
        
    Returns:
        Contexto completo coletado do New Relic
    """
    logger.info("Iniciando coleta de contexto completo")
    
    # Inicializa o contexto com estrutura básica
    contexto = {
        "apm": [],
        "browser": [],
        "infra": [],
        "db": [],
        "mobile": [],
        "iot": [],
        "serverless": [],
        "synth": [],
        "ext": [],
        "alertas": [],
        "entidades": []
    }
    
    # Inicializa o coletor
    collector = NewRelicCollector(NEW_RELIC_API_KEY, NEW_RELIC_ACCOUNT_ID)
    
    try:
        # Coleta todas as entidades
        entidades = await collector.collect_entities()
        
        if not entidades:
            logger.error("Nenhuma entidade encontrada na coleta do contexto completo")
            return contexto
        
        logger.info(f"Coletadas {len(entidades)} entidades básicas")
        
        # Filtra apenas entidades que estão reportando
        entidades_reportando = [e for e in entidades if e.get("reporting")]
        logger.info(f"Entidades reportando: {len(entidades_reportando)} de {len(entidades)}")
        
        # Coleta métricas para cada entidade (processamento em lotes para evitar sobrecarga)
        batch_size = 5
        total_processadas = 0
        entidades_com_metricas = []
        total_batches = (len(entidades_reportando) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(entidades_reportando))
            batch = entidades_reportando[start_idx:end_idx]
            
            logger.info(f"Processando lote {batch_num + 1}/{total_batches} ({len(batch)} entidades)")
            
            # Processa entidades no lote
            for ent in batch:
                try:
                    guid = ent.get("guid")
                    name = ent.get("name", "Desconhecido")
                    domain = ent.get("domain")
                    
                    logger.debug(f"Coletando métricas para entidade: {name} ({domain})")
                    metricas = await coletar_metricas_entidade(ent, collector)
                    
                    # Cria um item completo com entidade + métricas
                    item = {
                        "name": name,
                        "guid": guid,
                        "domain": domain,
                        "entityType": ent.get("entityType"),
                        "tags": ent.get("tags", []),
                        "reporting": ent.get("reporting", True),
                        "metricas": metricas
                    }
                    
                    # Verifica se a entidade tem dados suficientes
                    if entidade_tem_dados(item):
                        # Adiciona à lista de entidades com métricas
                        entidades_com_metricas.append(item)
                        
                        # Adiciona à categoria específica por domínio
                        dominio_chave = domain.lower() if domain and domain.lower() in contexto else "ext"
                        if dominio_chave in contexto:
                            contexto[dominio_chave].append(item)
                    else:
                        logger.warning(f"Entidade sem métricas suficientes: {name} ({domain})")
                    
                    total_processadas += 1
                
                except Exception as e:
                    logger.error(f"Erro ao processar entidade {ent.get('name')}: {e}")
            
            # Pequena pausa entre lotes para evitar sobrecarga
            if batch_num < total_batches - 1:
                await asyncio.sleep(1)
        
        # Adiciona lista consolidada de entidades válidas
        contexto["entidades"] = entidades_com_metricas
        
        # Adiciona metadados sobre a coleta
        contexto["metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "total_entidades_originais": len(entidades),
            "total_entidades_reportando": len(entidades_reportando),
            "total_entidades_com_metricas": len(entidades_com_metricas),
            "rate_limit_failures": rate_controller.consecutive_failures,
            "coleta_bem_sucedida": len(entidades_com_metricas) > 0
        }
        
        # Log de estatísticas
        logger.info(f"Contexto completo coletado com sucesso:")
        logger.info(f"Total de entidades: {len(entidades)}")
        logger.info(f"Entidades reportando: {len(entidades_reportando)}")
        logger.info(f"Entidades com métricas: {len(entidades_com_metricas)}")
        
        # Log de entidades por domínio
        for dominio, lista in contexto.items():
            if dominio not in ["entidades", "metadata", "alertas"]:
                logger.info(f"  {dominio.upper()}: {len(lista)} entidades")
        
        return contexto
    
    except Exception as e:
        logger.error(f"Erro crítico durante coleta do contexto completo: {e}")
        logger.error(traceback.format_exc())
        
        # Retorna o contexto padrão (vazio) em caso de falha crítica
        contexto["metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "coleta_bem_sucedida": False
        }
        
        return contexto

async def main():
    """Função para teste direto deste módulo"""
    # Configurar logging para teste
    logging.basicConfig(level=logging.INFO)
    
    print("== TESTE DE COLETA DE CONTEXTO COMPLETO ==")
    start_time = datetime.now()
    contexto = await coletar_contexto_completo()
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"Coleta completa realizada em {duration:.2f} segundos")
    
    # Estatísticas básicas
    entidades = contexto.get("entidades", [])
    print(f"Total de entidades coletadas: {len(entidades)}")
    
    # Entidades por domínio
    print("\nEntidades por domínio:")
    for dominio, lista in contexto.items():
        if dominio not in ["entidades", "metadata", "alertas"]:
            print(f"  {dominio.upper()}: {len(lista)} entidades")
    
    # Amostra de métricas
    if entidades:
        print("\nAmostra de métricas da primeira entidade:")
        primeira = entidades[0]
        print(f"Nome: {primeira.get('name')}")
        print(f"Domínio: {primeira.get('domain')}")
        
        metricas = primeira.get("metricas", {})
        for periodo, dados in metricas.items():
            print(f"\n  Período: {periodo}")
            for metrica, valor in dados.items():
                print(f"    {metrica}: {valor is not None}")
    
    # Salvar para análise
    output_path = "contexto_teste.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(contexto, f, indent=2)
    print(f"\nContexto completo salvo em: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
