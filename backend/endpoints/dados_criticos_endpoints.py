
from fastapi import APIRouter, HTTPException
import logging
import asyncio
from datetime import datetime

# Garantir import do coletor, independente do path
import sys
import os
from pathlib import Path
_utils_path = Path(__file__).parent.parent / 'utils'
if str(_utils_path) not in sys.path:
    sys.path.insert(0, str(_utils_path))
try:
    from advanced_newrelic_collector import AdvancedNewRelicCollector
except ImportError:
    # fallback para import absoluto se rodando do root
    from backend.utils.advanced_newrelic_collector import AdvancedNewRelicCollector

logger = logging.getLogger(__name__)
router = APIRouter()

# Instância global do coletor para reuso
collector = None
def get_collector():
    global collector
    if collector is None:
        collector = AdvancedNewRelicCollector()
    return collector


@router.get("/logs")
async def get_logs():
    """
    Endpoint para obter dados reais de logs do New Relic.
    """
    try:
        collector = get_collector()
        # Automatizar detecção de evento válido para logs, mas permitir qualquer evento se não houver candidato
        log_event_candidates = ["LogRecord", "Log", "LogMessage", "NrConsumption"]
        valid_event = await collector.suggest_valid_event_for_query(log_event_candidates, allow_any=True)
        if not valid_event:
            eventos = await collector.list_event_types()
            return {
                "erro": True,
                "mensagem": "Nenhum evento válido de log encontrado na conta New Relic.",
                "eventos_disponiveis": eventos,
                "timestamp": datetime.now().isoformat()
            }
        nrql = f"SELECT * FROM {valid_event} SINCE 1 DAY AGO LIMIT 100"
        result = await collector.execute_nrql_query(nrql)
        if result and "results" in result and result["results"]:
            return {"logs": result["results"], "timestamp": datetime.now().isoformat(), "nrql": nrql, "evento_utilizado": valid_event}
        if result and "error" in result:
            logger.error(f"Erro NRQL logs: {result}")
        return {
            "erro": True,
            "mensagem": f"Não foram encontrados dados reais de logs. Última resposta: {result}",
            "evento_utilizado": valid_event,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao buscar logs do New Relic: {e}")
        return {"erro": True, "mensagem": f"Erro ao buscar logs do New Relic: {e}", "timestamp": datetime.now().isoformat()}


@router.get("/alertas")
async def get_alertas():
    """
    Endpoint para obter dados reais de alertas do New Relic.
    """
    try:
        collector = get_collector()
        policies = await collector.get_all_alert_policies()
        if policies:
            return {"alertas": policies, "timestamp": datetime.now().isoformat()}
        return {"erro": True, "mensagem": f"Não foram encontrados dados reais de alertas. Última resposta: {policies}", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Erro ao buscar alertas do New Relic: {e}")
        return {"erro": True, "mensagem": f"Erro ao buscar alertas do New Relic: {e}", "timestamp": datetime.now().isoformat()}


@router.get("/dashboards")
async def get_dashboards():
    """
    Endpoint para obter dados reais de dashboards do New Relic.
    """
    try:
        collector = get_collector()
        dashboards = await collector.get_dashboards_list()
        if dashboards:
            return {"dashboards": dashboards, "timestamp": datetime.now().isoformat()}
        return {"erro": True, "mensagem": f"Não foram encontrados dados reais de dashboards. Última resposta: {dashboards}", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Erro ao buscar dashboards do New Relic: {e}")
        return {"erro": True, "mensagem": f"Erro ao buscar dashboards do New Relic: {e}", "timestamp": datetime.now().isoformat()}


@router.get("/incidentes")
async def get_incidentes():
    """
    Endpoint para obter dados reais de incidentes do New Relic.
    """
    try:
        collector = get_collector()
        # Automatizar detecção de evento válido para incidentes, mas permitir qualquer evento se não houver candidato
        incident_event_candidates = ["NrAiIncident", "Incident", "AiIncident", "NrConsumption"]
        valid_event = await collector.suggest_valid_event_for_query(incident_event_candidates, allow_any=True)
        if not valid_event:
            eventos = await collector.list_event_types()
            return {
                "erro": True,
                "mensagem": "Nenhum evento válido de incidente encontrado na conta New Relic.",
                "eventos_disponiveis": eventos,
                "timestamp": datetime.now().isoformat()
            }
        nrql = f"SELECT * FROM {valid_event} SINCE 1 DAY AGO LIMIT 100"
        result = await collector.execute_nrql_query(nrql)
        if result and "results" in result and result["results"]:
            return {"incidentes": result["results"], "timestamp": datetime.now().isoformat(), "nrql": nrql, "evento_utilizado": valid_event}
        if result and "error" in result:
            logger.error(f"Erro NRQL incidentes: {result}")
        return {
            "erro": True,
            "mensagem": f"Não foram encontrados dados reais de incidentes. Última resposta: {result}",
            "evento_utilizado": valid_event,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao buscar incidentes do New Relic: {e}")
        return {"erro": True, "mensagem": f"Erro ao buscar incidentes do New Relic: {e}", "timestamp": datetime.now().isoformat()}

# Endpoint auxiliar para listar todos os eventos disponíveis (útil para configuração/admin)
@router.get("/eventos_disponiveis")
async def get_eventos_disponiveis():
    """
    Endpoint para listar todos os eventos disponíveis detectados via NRQL SHOW EVENT TYPES.
    """
    try:
        collector = get_collector()
        eventos = await collector.list_event_types()
        return {"eventos_disponiveis": eventos, "total": len(eventos), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Erro ao listar eventos disponíveis: {e}")
        return {"erro": True, "mensagem": f"Erro ao listar eventos disponíveis: {e}", "timestamp": datetime.now().isoformat()}
