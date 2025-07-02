from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Tentar importar de backend primeiro, se não der erro, importar do pacote atual
try:
    from backend.utils.entity_processor import is_entity_valid, process_entity_details
    from backend.utils.data_loader import load_json_data
except ImportError:
    from utils.entity_processor import is_entity_valid, process_entity_details
    from utils.data_loader import load_json_data

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router
router = APIRouter()

# Endpoint para insights
@router.get("/insights")
async def get_insights():
    """
    Endpoint para obter dados de insights.
    Carrega dados do arquivo insights.json e retorna diretamente, pois 
    insights são diferentes de entidades regulares.
    """
    try:
        # Carregar dados usando a função centralizada
        insights_data = load_json_data("insights.json")
        
        # Verificar se houve erro na carga
        if isinstance(insights_data, dict) and insights_data.get("erro"):
            return insights_data
            
        # Se já tivermos lista ou estrutura válida, retornar diretamente
        if isinstance(insights_data, list) and len(insights_data) > 0:
            logger.info(f"Retornando {len(insights_data)} insights")
            return insights_data
        elif isinstance(insights_data, dict) and 'insights' in insights_data:
            logger.info("Retornando dados de insights em formato estruturado")
            return insights_data
            
        # Se não encontrou insights válidos, retornar mensagem de erro
        logger.warning("Nenhum insight válido encontrado")
        return {
            "erro": True,
            "mensagem": "Não foram encontrados dados de insights válidos. Execute generate_unified_data.py para criar dados de teste.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao processar request de insights: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar insights: {str(e)}")

# Outros endpoints podem ser adicionados aqui
