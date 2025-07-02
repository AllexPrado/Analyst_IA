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

# Dados simulados para desenvolvimento - serão substituídos por dados reais
# def generate_sample_tendencias_data():
#     """Gera dados de tendências para o frontend"""
#     meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"]
#     return {
#         "apdex": {
#             "labels": meses,
#             "series": [
#                 {
#                     "name": "Apdex",
#                     "data": [0.82, 0.84, 0.81, 0.83, 0.87, 0.89]
#                 }
#             ]
#         },
#         "disponibilidade": {
#             "labels": meses,
#             "series": [
#                 {
#                     "name": "Uptime",
#                     "data": [99.2, 99.3, 99.1, 99.5, 99.7, 99.8]
#                 }
#             ]
#         },
#         "erros": {
#             "labels": meses,
#             "series": [
#                 {
#                     "name": "Taxa de Erros",
#                     "data": [2.5, 2.2, 2.7, 2.0, 1.5, 1.1]
#                 }
#             ]
#         },
#         "throughput": {
#             "labels": meses,
#             "series": [
#                 {
#                     "name": "Requisições/min",
#                     "data": [1200, 1350, 1500, 1700, 1900, 2100]
#                 }
#             ]
#         },
#         "previsao_cpu": {
#             "labels": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", 
#                       "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30"],
#             "series": [
#                 {
#                     "name": "Utilização da CPU",
#                     "data": [60, 61, 63, 65, 66, 68, 69, 71, 72, 74, 75, 76, 78, 79, 80, 
#                             81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 92, 93, 94]
#                 },
#                 {
#                     "name": "Previsão com otimização",
#                     "data": [60, 61, 63, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 
#                             77, 78, 79, 80, 81, 81, 82, 82, 83, 83, 84, 84, 84, 85, 85]
#                 }
#             ]
#         },
#         "anomalias": [
#             {
#                 "data": "2025-06-25",
#                 "hora": "14:32:15",
#                 "recurso": "API Gateway",
#                 "metrica": "Latência",
#                 "desvio": "+245%",
#                 "duracao": "12 min",
#                 "severidade": "Alta",
#                 "status": "Resolvido"
#             },
#             {
#                 "data": "2025-06-26",
#                 "hora": "08:15:22",
#                 "recurso": "Database",
#                 "metrica": "CPU",
#                 "desvio": "+180%",
#                 "duracao": "28 min",
#                 "severidade": "Média",
#                 "status": "Resolvido"
#             },
#             {
#                 "data": "2025-06-27",
#                 "hora": "19:45:03",
#                 "recurso": "Auth Service",
#                 "metrica": "Erros",
#                 "desvio": "+520%",
#                 "duracao": "5 min",
#                 "severidade": "Crítica",
#                 "status": "Resolvido"
#             },
#             {
#                 "data": "2025-06-28",
#                 "hora": "22:12:48",
#                 "recurso": "Cache",
#                 "metrica": "Hit Rate",
#                 "desvio": "-75%",
#                 "duracao": "45 min",
#                 "severidade": "Média",
#                 "status": "Resolvido"
#             }
#         ],
#         "padroes": {
#             "sazonais": {
#                 "confianca": 87,
#                 "dados": [
#                     {"dia": "Dom", "valor": 0.2},
#                     {"dia": "Seg", "valor": 0.8},
#                     {"dia": "Ter", "valor": 0.9},
#                     {"dia": "Qua", "valor": 0.85},
#                     {"dia": "Qui", "valor": 0.95},
#                     {"dia": "Sex", "valor": 0.92},
#                     {"dia": "Sab", "valor": 0.3}
#                 ]
#             }
#         },
#         "previsao_texto": "Análise preditiva indica tendência de aumento de 12% na utilização de CPU nos próximos 30 dias. Recomenda-se avaliar escalabilidade dos recursos."
#     }

@router.get("/tendencias")
async def get_tendencias():
    """
    Endpoint para obter dados de tendências.
    Carrega dados do arquivo tendencias.json e processa para garantir que apenas dados válidos sejam retornados.
    """
    try:
        # Carregar dados usando a função centralizada
        tendencias_data = load_json_data("tendencias.json")
        
        # Verificar se houve erro na carga
        if tendencias_data.get("erro"):
            return tendencias_data
            
        # Para dados de tendências no formato de dicionário específico
        if isinstance(tendencias_data, dict) and any(key in tendencias_data for key in ["apdex", "erros", "tempos_resposta", "throughput"]):
            logger.info("Dados de tendências já estão no formato correto")
            return tendencias_data
            
        # Processar dados com base na estrutura (lista ou dicionário de entidades)
        valid_tendencias = []
        if isinstance(tendencias_data, list):
            valid_tendencias = [process_entity_details(item) for item in tendencias_data if is_entity_valid(item)]
        elif isinstance(tendencias_data, dict):
            valid_tendencias = [process_entity_details(tendencias_data)] if is_entity_valid(tendencias_data) else []
        
        # Remover campos vazios/nulos
        valid_tendencias = [i for i in valid_tendencias if i and i != {}]
        
        # Verificar se temos tendências válidas
        if valid_tendencias:
            logger.info(f"Retornando {len(valid_tendencias)} tendências válidas")
            return valid_tendencias
            
        # Se não encontrou tendências válidas, retornar mensagem de erro
        logger.warning("Nenhuma tendência válida encontrada após processamento")
        return {
            "erro": True,
            "mensagem": "Não foram encontrados dados reais de tendências válidos no cache. Execute generate_unified_data.py para criar dados de teste ou atualize o cache com dados do New Relic.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao processar requisição de tendências: {e}")
        raise HTTPException(status_code=500, detail=str(e))
