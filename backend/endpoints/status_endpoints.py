from fastapi import APIRouter, HTTPException
import os
import json
import logging
from datetime import datetime

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router
router = APIRouter()

# Função para verificar o status dos dados
@router.get("/data_source")
async def get_data_source():
    """
    Retorna informações sobre a origem dos dados (reais ou simulados)
    """
    try:
        # Verificar se existe o indicador de dados reais
        indicator_path = "backend/cache/data_source_indicator.json"
        if os.path.exists(indicator_path):
            with open(indicator_path, 'r', encoding='utf-8') as f:
                indicator = json.load(f)
                return indicator
        
        # Verificar se existe o arquivo de relatório de integração
        report_path = "relatorio_integracao_dados_reais.json"
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
                return {
                    "using_real_data": report.get("modo") == "real",
                    "timestamp": report.get("timestamp", datetime.now().isoformat()),
                    "source": "New Relic API" if report.get("modo") == "real" else "Simulado"
                }
        
        # Se não houver indicador nem relatório, verificar variáveis de ambiente
        account_id = os.environ.get("NEW_RELIC_ACCOUNT_ID")
        api_key = os.environ.get("NEW_RELIC_API_KEY")
        
        if account_id and api_key:
            return {
                "using_real_data": True,
                "timestamp": datetime.now().isoformat(),
                "source": "New Relic API (credenciais disponíveis)"
            }
        
        # Se nada disso estiver disponível, assume dados simulados
        return {
            "using_real_data": False,
            "timestamp": datetime.now().isoformat(),
            "source": "Dados simulados"
        }
    except Exception as e:
        logger.error(f"Erro ao verificar origem dos dados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao verificar origem dos dados: {str(e)}")

@router.get("/health")
async def get_health():
    """
    Retorna o status de saúde do sistema
    """
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat()
    }
