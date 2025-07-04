from fastapi import APIRouter, HTTPException
import logging
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

def load_json_data(filename):
    paths = [
        f"dados/{filename}",
        f"backend/dados/{filename}",
        f"../dados/{filename}",
        f"../backend/dados/{filename}"
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao ler {path}: {e}")
    return None

@router.get("/logs")
async def get_logs():
    """
    Endpoint para obter dados reais de logs.
    Carrega dados do arquivo logs.json e retorna ao frontend.
    """
    logs_data = load_json_data("logs.json")
    if not logs_data:
        return {"erro": True, "mensagem": "Não foram encontrados dados reais de logs.", "timestamp": datetime.now().isoformat()}
    return logs_data

@router.get("/alertas")
async def get_alertas():
    """
    Endpoint para obter dados reais de alertas.
    Carrega dados do arquivo alertas.json e retorna ao frontend.
    """
    alertas_data = load_json_data("alertas.json")
    if not alertas_data:
        return {"erro": True, "mensagem": "Não foram encontrados dados reais de alertas.", "timestamp": datetime.now().isoformat()}
    return alertas_data

@router.get("/dashboards")
async def get_dashboards():
    """
    Endpoint para obter dados reais de dashboards.
    Carrega dados do arquivo dashboards.json e retorna ao frontend.
    """
    dashboards_data = load_json_data("dashboards.json")
    if not dashboards_data:
        return {"erro": True, "mensagem": "Não foram encontrados dados reais de dashboards.", "timestamp": datetime.now().isoformat()}
    return dashboards_data

@router.get("/incidentes")
async def get_incidentes():
    """
    Endpoint para obter dados reais de incidentes.
    Carrega dados do arquivo incidentes.json e retorna ao frontend.
    """
    incidentes_data = load_json_data("incidentes.json")
    if not incidentes_data:
        return {"erro": True, "mensagem": "Não foram encontrados dados reais de incidentes.", "timestamp": datetime.now().isoformat()}
    return incidentes_data
