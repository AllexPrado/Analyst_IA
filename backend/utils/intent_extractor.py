"""
Módulo para extrair intenções e métricas específicas baseadas nas perguntas do usuário.
Permite customizar o processamento de entidades com base no tipo de consulta.
"""

import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def extract_metrics_for_query(pergunta: str, entidades: List[Dict[str, Any]]) -> Dict:
    """
    Extrai métricas específicas com base na pergunta do usuário.
    Permite priorizar e filtrar as entidades com base na pergunta.
    
    Args:
        pergunta: Pergunta do usuário
        entidades: Lista de entidades filtradas
        
    Returns:
        Dict com métricas extraídas e filtros aplicados
    """
    pergunta_lower = pergunta.lower()
    
    # Inicializa os resultados
    result = {
        "tipo_consulta": "geral",
        "entidades_relevantes": [],
        "filtros_aplicados": [],
        "periodo_analise": "30min",  # padrão
        "metricas_prioritarias": [],
        "keywords": []
    }
    
    # Detectar menções a períodos de tempo
    periodos = {
        "7d": ["7 dias", "semana", "semanal", "últimos 7 dias", "ultima semana"],
        "24h": ["24 horas", "dia", "diário", "último dia", "ultimas 24 horas"],
        "30min": ["30 minutos", "meia hora", "últimos 30 minutos"],
        "3h": ["3 horas", "últimas horas", "últimas 3 horas"],
        "60min": ["hora", "última hora", "60 minutos"]
    }
    
    for periodo, keywords in periodos.items():
        if any(keyword in pergunta_lower for keyword in keywords):
            result["periodo_analise"] = periodo
            result["filtros_aplicados"].append(f"Período: {periodo}")
            break
    
    # Detectar consultas sobre APIs lentas
    api_patterns = [
        r"apis?\s+(?:mais\s+)?lenta",
        r"lentid[ãa]o.*apis?",
        r"apis?.*lenta",
        r"performance.*apis?",
        r"apis?.*performance"
    ]
    
    sql_patterns = [
        r"sql",
        r"quer(?:y|ies)",
        r"banco\s+de\s+dados",
        r"database",
    ]
    
    error_patterns = [
        r"erro",
        r"falha",
        r"exceção",
        r"exception",
        r"stacktrace",
        r"trace"
    ]
    
    # Verificar se a pergunta é sobre APIs lentas
    if any(re.search(pattern, pergunta_lower) for pattern in api_patterns):
        result["tipo_consulta"] = "apis_lentas"
        result["filtros_aplicados"].append("Consulta sobre APIs lentas")
        result["metricas_prioritarias"] = ["response_time_max", "apdex", "throughput"]
        result["keywords"] = ["api", "endpoint", "lenta", "performance", "latência"]
        
        # Extrair número de APIs solicitadas
        numero_match = re.search(r"(\d+)\s+apis", pergunta_lower)
        if numero_match:
            result["numero_apis"] = int(numero_match.group(1))
            result["filtros_aplicados"].append(f"Limite: top {numero_match.group(1)} APIs")
    
    # Verificar se a pergunta é sobre SQL
    if any(re.search(pattern, pergunta_lower) for pattern in sql_patterns):
        result["tipo_consulta"] = "sql_performance"
        result["filtros_aplicados"].append("Consulta sobre SQL/Banco de dados")
        result["metricas_prioritarias"] = ["database_query", "sql_performance", "database_call_time"]
        result["keywords"].extend(["sql", "query", "database", "banco"])
    
    # Verificar se a pergunta é sobre erros/stacktraces
    if any(re.search(pattern, pergunta_lower) for pattern in error_patterns):
        if result["tipo_consulta"] == "geral":
            result["tipo_consulta"] = "errors"
        else:
            result["tipo_consulta"] += "_with_errors"
            
        result["filtros_aplicados"].append("Consulta sobre erros/exceções")
        result["metricas_prioritarias"].extend(["recent_error", "error_rate", "error_trace"])
        result["keywords"].extend(["erro", "exceção", "stacktrace", "trace"])
    
    # Verificar menção a "causa raiz"
    if "causa raiz" in pergunta_lower or "root cause" in pergunta_lower:
        result["filtros_aplicados"].append("Análise de causa raiz")
        result["tipo_consulta"] += "_root_cause"
        result["keywords"].extend(["causa raiz", "root cause", "diagnóstico"])
    
    # Aplicar filtros às entidades
    filtered_entities = []
    
    # Se for consulta específica, filtra apenas entidades relevantes
    if result["tipo_consulta"] != "geral":
        for entity in entidades:
            entity_score = 0
            
            # Verifica se a entidade tem as métricas prioritárias
            if entity.get("metricas") and entity.get("metricas", {}).get(result["periodo_analise"]):
                metrics = entity.get("metricas", {}).get(result["periodo_analise"])
                
                # Pontua a entidade com base nas métricas prioritárias
                for metric_key in result["metricas_prioritarias"]:
                    if any(metric_key in k for k in metrics.keys()):
                        entity_score += 3
                
                # Verifica se a entidade tem palavras-chave relevantes
                entity_name = entity.get("name", "").lower()
                for keyword in result["keywords"]:
                    if keyword in entity_name:
                        entity_score += 2
                
                # Se for do tipo APM tem mais chances de ter dados relevantes para APIs
                if entity.get("domain") == "APM":
                    entity_score += 5
            
            # Se encontrou métricas relevantes, adiciona à lista filtrada
            if entity_score > 0:
                # Adiciona o score para usar na ordenação
                entity["_relevance_score"] = entity_score
                filtered_entities.append(entity)
    
    # Ordena por relevância (se houver score)
    if filtered_entities:
        filtered_entities.sort(key=lambda e: e.get("_relevance_score", 0), reverse=True)
        result["entidades_relevantes"] = filtered_entities
        
    logger.info(f"Extrator de intenções: {result['tipo_consulta']} com {len(filtered_entities)} entidades relevantes")
    
    return result

def enrich_prompt_for_query_type(pergunta: str, context_info: Dict) -> str:
    """
    Enriquece o prompt com base no tipo de consulta detectado
    
    Args:
        pergunta: Pergunta do usuário
        context_info: Informações extraídas pelo extrator
    
    Returns:
        Instruções adicionais para o prompt
    """
    tipo_consulta = context_info.get("tipo_consulta", "geral")
    filtros = context_info.get("filtros_aplicados", [])
    
    # Gera instruções adicionais para o prompt
    instructions = []
    
    if "apis_lentas" in tipo_consulta:
        instructions.append(
            "FOCO DE ANÁLISE: APIs com tempos de resposta elevados.\n"
            "- Identifique os endpoints mais lentos com base nos tempos de resposta\n"
            "- Ordene por latência média/máxima\n"
            "- Inclua métricas detalhadas de performance para cada API\n"
            "- Se disponível, indique volume de tráfego para cada endpoint"
        )
        
        if "root_cause" in tipo_consulta:
            instructions.append(
                "ANÁLISE DE CAUSA RAIZ:\n"
                "- Avalie correlações entre consultas SQL lentas e APIs afetadas\n"
                "- Identifique padrões em stacktraces e mensagens de erro\n"
                "- Busque bottlenecks como consultas N+1, queries sem índice, ou chamadas em cascata\n"
                "- Formule hipóteses específicas sobre as causas da lentidão observada"
            )
    
    elif "sql_performance" in tipo_consulta:
        instructions.append(
            "FOCO DE ANÁLISE: Consultas SQL e performance de banco de dados.\n"
            "- Identifique queries específicas com problemas de performance\n"
            "- Mostre estatísticas de tempo de execução de queries\n"
            "- Analise correlações entre queries lentas e APIs afetadas\n"
            "- Extraia exemplos de queries problemáticas quando disponíveis"
        )
    
    elif "errors" in tipo_consulta:
        instructions.append(
            "FOCO DE ANÁLISE: Erros e exceções nas aplicações.\n"
            "- Liste os erros mais frequentes com contagem de ocorrências\n"
            "- Extraia stacktraces relevantes quando disponíveis\n"
            "- Identifique padrões nas mensagens de erro\n"
            "- Sugira correlações entre erros e degradação de performance"
        )
    
    # Adicionar número de exemplos específicos se solicitado
    if "numero_apis" in context_info:
        instructions.append(f"FORMATO DA RESPOSTA: Liste exatamente as {context_info['numero_apis']} APIs mais lentas")
    
    # Adicionar período específico se não for o padrão
    if context_info.get("periodo_analise") != "30min":
        instructions.append(f"PERÍODO DE ANÁLISE: Considere dados do último período de {context_info['periodo_analise']}")
    
    return "\n\n".join(instructions)
