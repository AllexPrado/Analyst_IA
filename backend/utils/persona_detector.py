import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

PERSONAS = {
    "executivo": {
        "keywords": ["business", "negócio", "impacto", "custo", "roi", "performance", "sla", "disponibilidade", "executivo", "gestão", "resultado"],
        "prompt_template": """
# Análise Executiva de Performance e Impacto no Negócio

{contexto}

## Pontos-chave para Gestão:
- Impacto no negócio
- SLAs e disponibilidade
- Custos e recursos
- Recomendações estratégicas
- Próximos passos
"""
    },
    "tecnico": {
        "keywords": ["código", "erro", "bug", "deploy", "infra", "log", "trace", "query", "api", "latência", "técnico", "debug"],
        "prompt_template": """
# Análise Técnica Detalhada

{contexto}

## Diagnóstico Técnico:
- Causa raiz
- Stacktrace/logs relevantes
- Queries impactadas
- Recomendações técnicas
- Ações para correção
"""
    },
    "default": {
        "keywords": [],
        "prompt_template": """
# Análise Geral

{contexto}

## Observações:
- Pontos relevantes
- Recomendações gerais
"""
    }
}

def detectar_persona(pergunta: str) -> str:
    p = pergunta.lower()
    for persona, data in PERSONAS.items():
        if any(kw in p for kw in data["keywords"]):
            return persona
    return "default"

def montar_prompt_por_persona(persona: str, contexto: str) -> str:
    template = PERSONAS.get(persona, PERSONAS["default"])['prompt_template']
    
    # Extrai e resume informações mais relevantes do contexto para reduzir tamanho do prompt
    contexto_resumido = resumir_contexto_para_persona(persona, contexto)
    
    return template.format(contexto=contexto_resumido)
    
def resumir_contexto_para_persona(persona: str, contexto: str) -> str:
    """
    Extrai e resume as partes mais relevantes do contexto para cada persona.
    Isso ajuda a reduzir o tamanho do prompt e focar no que importa para cada tipo de usuário.
    """
    import json
    
    try:
        # Se o contexto for muito grande, precisamos extrair apenas o essencial
        if len(contexto) > 30000:
            logger.warning(f"Contexto muito grande ({len(contexto)} caracteres), resumindo...")
            
            # Tenta carregar o contexto como JSON
            try:
                ctx_dict = json.loads(contexto)
            except:
                # Se falhar, usa uma abordagem baseada em texto
                return resumir_contexto_texto(contexto, persona)
                
            # Extrai seções relevantes com base na persona
            resumo = {}
            
            # Para todos, inclui metadata e timestamp
            if "timestamp" in ctx_dict:
                resumo["timestamp"] = ctx_dict["timestamp"]
                
            # Para executivos, foca em métricas de negócio e resumos
            if persona == "executivo":
                if "alertas" in ctx_dict:
                    resumo["alertas"] = ctx_dict["alertas"]
                if "kpis" in ctx_dict:
                    resumo["kpis"] = ctx_dict["kpis"]
                if "tendencias" in ctx_dict:
                    resumo["tendencias"] = ctx_dict["tendencias"]
                
                # Inclui apenas um resumo das entidades, não todos os detalhes
                if "entidades" in ctx_dict:
                    entidades_resumo = []
                    for entidade in ctx_dict["entidades"][:10]:  # Limita a 10 entidades
                        ent_resumo = {
                            "name": entidade.get("name"),
                            "domain": entidade.get("domain"),
                            "status": entidade.get("status", "desconhecido"),
                            "resumo": {}
                        }
                        # Adiciona resumo de métricas se disponível
                        if "metricas" in entidade:
                            for periodo, metricas in entidade["metricas"].items():
                                # Pega apenas métricas do período de 7d
                                if periodo == "7d":
                                    ent_resumo["resumo"] = {
                                        k: v for k, v in metricas.items() 
                                        if k in ["apdex", "throughput", "cpu", "memoria"]
                                    }
                        entidades_resumo.append(ent_resumo)
                    resumo["entidades_resumo"] = entidades_resumo
                    
            # Para técnicos, inclui mais detalhes técnicos
            elif persona == "tecnico":
                # Inclui erros e métricas técnicas
                if "entidades" in ctx_dict:
                    entidades_tecnicas = []
                    for entidade in ctx_dict["entidades"]:
                        # Filtra apenas entidades com erros ou alertas
                        if "metricas" in entidade:
                            # Verifica se tem erros ou métricas ruins
                            tem_problemas = False
                            for periodo, metricas in entidade.get("metricas", {}).items():
                                if "recent_error" in metricas or "js_errors" in metricas:
                                    tem_problemas = True
                                    break
                            
                            # Se tem problemas ou é APM ou INFRA, inclui no resumo
                            if tem_problemas or entidade.get("domain") in ["APM", "INFRA"]:
                                entidades_tecnicas.append(entidade)
                    
                    # Se tiver muitas entidades com problemas, limita
                    if len(entidades_tecnicas) > 10:
                        entidades_tecnicas = entidades_tecnicas[:10]
                    
                    resumo["entidades_tecnicas"] = entidades_tecnicas
            
            # Para padrão (default), inclui um equilíbrio
            else:
                if "entidades" in ctx_dict:
                    # Pega até 5 entidades mais importantes
                    entidades_importantes = []
                    for entidade in ctx_dict["entidades"][:5]:
                        entidades_importantes.append({
                            "name": entidade.get("name"),
                            "domain": entidade.get("domain"),
                            "status": entidade.get("status", "desconhecido")
                        })
                    resumo["entidades"] = entidades_importantes
                
                if "alertas" in ctx_dict:
                    resumo["alertas"] = ctx_dict["alertas"]
            
            # Converte de volta para string
            return json.dumps(resumo, ensure_ascii=False, indent=2)
        else:
            # Se o contexto não é tão grande, usa ele inteiro
            return contexto
    except Exception as e:
        logger.error(f"Erro ao resumir contexto: {e}")
        return contexto[:30000]  # Corta para ter certeza que não é muito grande

def resumir_contexto_texto(contexto: str, persona: str) -> str:
    """Abordagem baseada em texto para resumo quando JSON não é possível"""
    
    # Se for contexto em markdown, extrai seções relevantes
    linhas = contexto.split('\n')
    resultado = []
    secao_atual = ""
    incluir_secao = False
    
    # Para executivos, mantém seções de resumo e KPIs
    executivo_keywords = ["RESUMO", "KPI", "SLA", "DISPONIBILIDADE", "NEGÓCIO"]
    tecnico_keywords = ["ERROS", "LATÊNCIA", "PERFORMANCE", "MÉTRICAS", "TÉCNICO"]
    
    for linha in linhas:
        # Detecta cabeçalhos markdown (#, ##, etc)
        if linha.strip().startswith('#'):
            # Termina seção anterior se existir
            if secao_atual and incluir_secao:
                resultado.append(secao_atual)
            
            # Nova seção
            secao_atual = linha + "\n"
            incluir_secao = False
            
            # Verifica se a seção é relevante para a persona
            if persona == "executivo" and any(kw in linha.upper() for kw in executivo_keywords):
                incluir_secao = True
            elif persona == "tecnico" and any(kw in linha.upper() for kw in tecnico_keywords):
                incluir_secao = True
            else:
                # Para default, inclui cabeçalhos de primeiro nível
                if linha.strip().startswith('# '):
                    incluir_secao = True
        elif incluir_secao:
            secao_atual += linha + "\n"
    
    # Adiciona última seção se necessário
    if secao_atual and incluir_secao:
        resultado.append(secao_atual)
    
    # Se mesmo assim for muito grande, limita ao final do texto (que geralmente tem a pergunta)
    resumo = '\n'.join(resultado)
    if len(resumo) > 30000:
        return resumo[-30000:]
    return resumo
