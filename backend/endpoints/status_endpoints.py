from fastapi import APIRouter, HTTPException
import os
import json
import logging
from datetime import datetime

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router
router = APIRouter()

def get_data_source_indicator():
    """Busca o indicador de fonte de dados em vários locais possíveis"""
    paths = [
        "cache/data_source_indicator.json",
        "backend/cache/data_source_indicator.json",
        "../cache/data_source_indicator.json",
        "data_source_indicator.json"
    ]
    
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao ler {path}: {e}")
    return None


# Endpoint principal de status para o frontend (VisaoGeral.vue)
def carregar_cache_status():
    # Tenta carregar o status do cache salvo
    caminhos = [
        "dados/status.json",
        "backend/dados/status.json",
        "../dados/status.json"
    ]
    for caminho in caminhos:
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
    return None

@router.get("")
async def get_status():
    """
    Endpoint principal de status para o frontend (VisaoGeral.vue)
    Retorna statusGeral, descricao, alertas, dominios, etc.
    """
    status = carregar_cache_status()
    if not status:
        return {
            "status": "Desconhecido",
            "descricao": "Dados não disponíveis",
            "alertas": 0,
            "alertasDescricao": "Não foi possível obter informações sobre alertas",
            "errosCriticos": 0,
            "errosDescricao": "Não foi possível obter informações sobre erros",
            "diagnostico": "Possível problema de conexão com o serviço backend.",
            "recomendacoes": [
                "Verifique se o serviço backend está em execução",
                "Verifique a conectividade de rede",
                "Consulte os logs do sistema para mais detalhes"
            ],
            "dominios": {}
        }
    # Mapeia o status do cache para o formato esperado pelo frontend
    return {
        "status": status.get("servidor", "Desconhecido"),
        "descricao": status.get("descricao", ""),
        "alertas": status.get("metricas", {}).get("alertas_ativos", 0),
        "alertasDescricao": status.get("descricao_alertas", ""),
        "errosCriticos": status.get("metricas", {}).get("erros_ativos", 0),
        "errosDescricao": status.get("descricao_erros", ""),
        "diagnostico": status.get("diagnostico", ""),
        "recomendacoes": status.get("recomendacoes", []),
        "dominios": status.get("dominios", {}),
        "disponibilidade": status.get("metricas", {}).get("disponibilidade", 99.9),
        "ultimaAtualizacao": status.get("ultima_atualizacao", datetime.now().isoformat())
    }

@router.get("/health")
async def get_health():
    """
    Retorna o status de saúde do sistema
    """
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat()
    }
