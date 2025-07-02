from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Tentar importar as funções de validação e processamento de entidade, permitindo execução fora de pacote
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

@router.get("/kpis")
async def get_kpis():
    """
    Endpoint para obter dados de KPIs.
    Carrega dados do arquivo kpis.json e valida para retornar ao frontend.
    """
    try:
        # Carregar dados usando a função centralizada
        kpis_data = load_json_data("kpis.json")
        
        # Verificar se houve erro na carga
        if kpis_data.get("erro"):
            return kpis_data
            
        # Para dados de KPIs no formato de dicionário (não são entidades)
        if isinstance(kpis_data, dict) and kpis_data.get("performance"):
            logger.info("Dados de KPIs carregados corretamente no formato de dicionário")
            return kpis_data
            
        # Processar dados apenas se forem entidades
        valid_kpis = []
        if isinstance(kpis_data, list):
            valid_kpis = [process_entity_details(kpi) for kpi in kpis_data if is_entity_valid(kpi)]
            # Remover campos vazios/nulos
            valid_kpis = [k for k in valid_kpis if k and k != {}]
            
            # Verificar se temos KPIs válidos
            if valid_kpis:
                logger.info(f"Retornando {len(valid_kpis)} KPIs válidos")
                return valid_kpis
        
        # Se não encontrou KPIs válidos, retornar mensagem de erro
        logger.warning("Nenhum KPI válido encontrado após processamento")
        return {
            "erro": True,
            "mensagem": "Não foram encontrados dados reais de KPIs válidos no cache. Execute generate_unified_data.py para criar dados de teste ou atualize o cache com dados do New Relic.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao processar requisição de KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
