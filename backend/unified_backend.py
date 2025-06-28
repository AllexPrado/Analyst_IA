"""
Backend unificado para o Analyst-IA com correções de bugs e endpoints completos
Este arquivo resolve problemas com o chat IA e dados nulos no frontend
"""

import os
import sys
import json
import logging
import aiofiles
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken não disponível. Usando fallback para contagem de tokens.")

import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Importar utils necessários
from utils.cache import get_cache, atualizar_cache_completo
from utils.entity_processor import filter_entities_with_data, is_entity_valid
from utils.newrelic_collector import coletar_contexto_completo
from utils.openai_connector import gerar_resposta_ia

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/analyst_ia.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

# Configuração da aplicação
app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI unificado para análise de métricas e IA contextual",
    version="2.0.1"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substituir por origens específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatInput(BaseModel):
    pergunta: str = Field(..., description="Pergunta para a IA")
    message: Optional[str] = Field(None, description="Campo alternativo para compatibilidade")

# Utilitários
def safe_first(lista, default=None):
    """Retorna o primeiro elemento de uma lista ou o valor padrão se vazia."""
    return lista[0] if lista and len(lista) > 0 else default

# Inicialização e cache
async def consolidar_entidades():
    """Consolida entidades de todos os domínios em uma única lista."""
    try:
        logger.info("Consolidando entidades no startup...")
        
        # Verificar se já existe cache recente
        cache = await get_cache()
        ja_tem_cache = cache and cache.get("entidades") and len(cache["entidades"]) > 0
        
        if ja_tem_cache:
            # Se já tem cache, apenas reprocessar as entidades existentes
            entidades = cache.get("entidades", [])
            logger.info(f"Reprocessando {len(entidades)} entidades já consolidadas no cache")
        else:
            # Se não tem cache, coletar novas entidades (pode levar mais tempo)
            logger.info("Cache vazio, coletando novas entidades...")
            await atualizar_cache_completo(coletar_contexto_fn=coletar_contexto_completo)
            cache = await get_cache()
            entidades = cache.get("entidades", [])
            logger.info(f"Coletadas {len(entidades)} novas entidades")
        
        # Garantir que temos dados válidos antes de prosseguir
        entidades_validas = filter_entities_with_data(entidades)
        logger.info(f"Startup: {len(entidades_validas)} entidades consolidadas")
        
        return entidades_validas
    except Exception as e:
        logger.error(f"Erro ao consolidar entidades: {str(e)}")
        logger.debug(traceback.format_exc())
        return []

@app.on_event("startup")
async def startup_event():
    """Executa na inicialização do servidor e força atualização do cache."""
    logger.info("Forçando atualização do cache no startup...")
    await atualizar_cache_completo(coletar_contexto_fn=coletar_contexto_completo)
    await consolidar_entidades()
    
# Endpoints
@app.get("/api/health")
async def health_check():
    """Endpoint para verificar se o serviço está operacional"""
    cache = await get_cache()
    cache_status = {
        "exists": bool(cache),
        "entities": len(cache.get("entidades", [])) if cache else 0,
        "last_update": cache.get("timestamp", "nunca") if cache else "nunca"
    }
    
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "cache": cache_status,
        "version": "2.0.1"
    }

@app.get("/api/status")
async def get_status():
    """Retorna status atual do serviço e cache"""
    cache = await get_cache()
    return {
        "status": "online",
        "fallback_mode": False,
        "cache_status": {
            "last_updated": cache.get("timestamp", "nunca"),
            "entities_count": len(cache.get("entidades", [])),
            "valid_entities": len(filter_entities_with_data(cache.get("entidades", []))),
        }
    }

@app.post("/api/chat")
async def chat_endpoint(input: ChatInput):
    """Endpoint do chat"""
    pergunta = input.pergunta
    # Compatibilidade com clientes que enviam 'message' em vez de 'pergunta'
    if not pergunta and hasattr(input, 'message') and input.message:
        pergunta = input.message
        logger.info(f"Campo 'message' usado em vez de 'pergunta': '{pergunta}'")
    logger.info(f"Recebida pergunta: '{pergunta}'")
    
    try:
        # Limpa o cache de entidades inválidas
        cache = await get_cache()
        entidades_originais = cache.get("entidades", [])
        
        # Filtra entidades para garantir que temos dados reais
        entidades = filter_entities_with_data(entidades_originais)
        logger.info(f"Chat usando {len(entidades)} entidades válidas de {len(entidades_originais)} totais")
        
        # Prepara o contexto para a IA - foco nas métricas reais
        entidades_com_metricas = [e for e in entidades if e.get("metricas") and any(e["metricas"].values())]
        logger.info(f"Chat usando {len(entidades_com_metricas)} entidades com métricas reais")
        
        # Prepara um sistema prompt técnico e específico
        system_prompt = """
        Você é um SRE sênior especialista em New Relic com profundo conhecimento técnico em:
        
        1. Análise de métricas de APM, Browser, e infraestrutura
        2. Consultas NRQL e dashboards analíticos
        3. Troubleshooting de problemas de performance
        4. Otimização de SLAs e SLOs
        
        REGRAS:
        - Responda APENAS baseado nos dados fornecidos
        - Nunca invente dados ou métricas que não foram fornecidos
        - Seja técnico, específico e direto
        - IMPORTANTE: Para cumprimentos simples como "oi", "olá", "bom dia", responda de forma EXTREMAMENTE CONCISA (máximo 2 frases)
        - Evite respostas longas ou genéricas a não ser que a pergunta realmente exija uma análise profunda
        """
        
        # Construir um prompt conciso com as informações mais relevantes
        if pergunta.lower() in ["oi", "olá", "oi!", "olá!", "bom dia", "boa tarde", "boa noite", "mensagem_inicial"]:
            prompt_compacto = """
            Você recebeu um cumprimento simples. Responda apenas com uma saudação breve de 1-2 frases.
            NÃO inclua apresentações longas, descrição de capacidades ou ofertas de ajuda detalhadas.
            APENAS uma resposta curta como "Olá! Como posso ajudar com seu monitoramento hoje?" ou similar.
            LIMITE SUA RESPOSTA A NO MÁXIMO 20 PALAVRAS.
            """
        else:
            # Resumir as principais entidades para o prompt
            top_entidades = entidades_com_metricas[:3] if entidades_com_metricas else []
            resumo_entidades = ""
            
            for e in top_entidades:
                nome = e.get("name", "Entidade sem nome")
                tipo = e.get("type", "Desconhecido")
                dominio = e.get("domain", "Desconhecido")
                
                # Extrair algumas métricas principais se disponíveis
                apdex = safe_first(e.get('metricas',{}).get('30min',{}).get('apdex',[]),{}).get('score')
                latencia = safe_first(e.get('metricas',{}).get('30min',{}).get('response_time_max',[]),{}).get('max.duration')
                
                resumo_entidades += f"- {nome} ({tipo}, {dominio}): "
                if apdex is not None:
                    resumo_entidades += f"Apdex {apdex:.2f}, "
                if latencia is not None:
                    resumo_entidades += f"Latência máx {latencia}ms, "
                resumo_entidades += "\\n"
            
            # Construir o prompt com a pergunta e contexto resumido
            prompt_compacto = f"""
            Pergunta: {pergunta}
            
            Contexto resumido:
            - Temos dados de {len(entidades_com_metricas)} entidades com métricas.
            - Distribuição por domínio: {len([e for e in entidades_com_metricas if e.get('domain') == 'APM'])} APM, {len([e for e in entidades_com_metricas if e.get('domain') == 'BROWSER'])} Browser, {len([e for e in entidades_com_metricas if e.get('domain') == 'INFRA'])} Infra.
            
            Principais entidades:
            {resumo_entidades}
            """
        
        logger.info(f"Enviando prompt para OpenAI com {len(prompt_compacto)} caracteres")
        
        # Verifica se temos dados suficientes para uma resposta de qualidade
        has_quality_data = len(entidades_com_metricas) > 0
        
        # Usar GPT-3.5 para economizar tokens, só usar GPT-4 em perguntas complexas
        use_gpt4 = len(prompt_compacto) > 1000 or "análise" in pergunta.lower() or "complexo" in pergunta.lower()
        
        resposta = await gerar_resposta_ia(
            prompt=prompt_compacto,
            system_prompt=system_prompt,
            modelo="gpt-3.5-turbo" if not use_gpt4 else "gpt-4"
            # temperatura removida - esse parâmetro não existe na função
        )
        
        resposta_str = resposta.strip() if isinstance(resposta, str) else str(resposta)
        logger.info(f"Resposta gerada com {len(resposta_str)} caracteres")
        
        # Se a resposta da IA for muito genérica, usa fallback com dados reais
        respostas_genericas = [
            "não tenho dados",
            "não possuo informações",
            "não foi possível encontrar",
            "não há dados",
            "não tenho acesso",
            "não tenho como"
        ]
        
        is_generic = any(frase in resposta_str.lower() for frase in respostas_genericas)
        
        if is_generic and has_quality_data:
            logger.warning("Resposta genérica detectada! Usando fallback com dados reais.")
            fallback = "Com base nos dados disponíveis de nossas entidades monitoradas, "
            fallback += f"temos {len(entidades_com_metricas)} aplicações com métricas ativas. "
            
            # Adicionar algumas estatísticas concretas
            total_apdex = 0
            count_apdex = 0
            for e in entidades_com_metricas:
                apdex = safe_first(e.get('metricas',{}).get('30min',{}).get('apdex',[]),{}).get('score')
                if apdex is not None:
                    total_apdex += apdex
                    count_apdex += 1
            
            if count_apdex > 0:
                avg_apdex = total_apdex / count_apdex
                fallback += f"O Apdex médio das aplicações é {avg_apdex:.2f}. "
            
            # Adicionar sugestão de consulta NRQL
            fallback += "\\n\\nPara investigar mais detalhes, considere esta consulta NRQL:\\n"
            fallback += "```sql\\nSELECT average(apdex), max(duration) FROM Transaction FACET appName LIMIT 10\\n```"
            
            resposta_str = fallback
        
        return {"resposta": resposta_str}
    except Exception as e:
        logger.error(f"Erro inesperado no endpoint de chat: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar sua pergunta: {str(e)}"
        )

@app.get("/api/kpis")
async def get_kpis():
    """
    Endpoint aprimorado para KPIs que fornece dados mais completos para o frontend
    """
    cache = await get_cache()
    entidades = cache.get("entidades", [])
    total = len(entidades)
    
    # Se não houver entidades, retorne resposta padrão vazia
    if total == 0:
        return {"kpis": [
            {"nome": "Disponibilidade", "valor": 0, "unidade": "%"},
            {"nome": "Taxa de Erro", "valor": 0, "unidade": "%"},
            {"nome": "Latência Máxima", "valor": 0, "unidade": "ms"}
        ], "mensagem": "Nenhum dado disponível. Configure a instrumentação no New Relic para visualizar KPIs."}
    
    # Funções auxiliares para extração de métricas
    def safe_apdex(e):
        return safe_first(e.get("metricas", {}).get("30min", {}).get("apdex", []), {}).get("score", 0)
    
    def safe_latencia(e):
        return safe_first(e.get("metricas", {}).get("30min", {}).get("response_time_max", []), {}).get("max.duration", 0)
    
    def safe_throughput(e):
        return safe_first(e.get("metricas", {}).get("30min", {}).get("throughput", []), {}).get("avg.qps", 0)
    
    # Filtragem das entidades com métricas válidas
    entidades_com_metricas = [e for e in entidades if e.get("metricas") and any(e["metricas"].values())]
    entidades_apm = [e for e in entidades_com_metricas if e.get("domain") == "APM"]
    
    # Evita divisão por zero
    total_metricas = len(entidades_com_metricas) if entidades_com_metricas else 1
    total_apm = len(entidades_apm) if entidades_apm else 1
    
    # Cálculo dos KPIs
    disponibilidade = sum(safe_apdex(e) for e in entidades_com_metricas) / total_metricas * 100
    taxa_erro = sum(len(e.get("metricas", {}).get("30min", {}).get("recent_error", [])) for e in entidades_com_metricas) / total_metricas
    latencia = sum(safe_latencia(e) for e in entidades_com_metricas) / total_metricas
    throughput = sum(safe_throughput(e) for e in entidades_apm)
    
    # Cálculo de serviços com problemas
    servicos_com_erros = [e for e in entidades_com_metricas if len(e.get("metricas", {}).get("30min", {}).get("recent_error", [])) > 0]
    
    # KPIs principais para dashboard
    kpis = [
        {"nome": "Disponibilidade", "valor": round(disponibilidade, 2), "unidade": "%"},
        {"nome": "Taxa de Erro", "valor": round(taxa_erro, 2), "unidade": "%"},
        {"nome": "Latência Máxima", "valor": round(latencia, 2), "unidade": "ms"}
    ]
    
    # Incluir dados adicionais para o frontend
    response = {
        "kpis": kpis, 
        "total_entidades": total,
        "entidades_com_metricas": len(entidades_com_metricas),
        "throughput": round(throughput, 2),
        "servicos_problematicos": len(servicos_com_erros),
        "mensagem": "",
        "ultimo_refresh": datetime.now().isoformat()
    }
    
    # Adicionar dados de serviços específicos se disponíveis
    if entidades_apm:
        response["servicos_detalhes"] = []
        for e in entidades_apm[:10]:  # Limita a 10 serviços
            apdex = safe_apdex(e)
            erros = len(e.get("metricas", {}).get("30min", {}).get("recent_error", []))
            latencia_max = safe_latencia(e)
            
            status = "Excelente"
            if apdex < 0.9 or erros > 0 or latencia_max > 1000:
                status = "Atenção"
            if apdex < 0.7 or erros > 5 or latencia_max > 3000:
                status = "Crítico"
                
            servico = {
                "nome": e.get("name", "Desconhecido"),
                "disponibilidade": round(apdex * 100, 1),
                "taxa_erro": round(erros / 10, 1) if erros > 0 else 0,
                "latencia": round(latencia_max, 0),
                "status": status
            }
            response["servicos_detalhes"].append(servico)
    
    return response

@app.get("/api/tendencias")
async def get_tendencias():
    """Endpoint para dados de tendências das aplicações"""
    cache = await get_cache()
    entidades = cache.get("entidades", [])
    
    # Filtrar apenas entidades com métricas válidas
    entidades_validas = filter_entities_with_data(entidades)
    
    if not entidades_validas:
        return {"series": [], "periodos": [], "mensagem": "Sem dados suficientes para gerar tendências"}
    
    # Coletar dados por período (30min, 24h, 7d)
    periodos = ["30min", "24h", "7d"]
    metricas_por_periodo = {periodo: [] for periodo in periodos}
    
    for entidade in entidades_validas:
        for periodo in periodos:
            metricas = entidade.get("metricas", {}).get(periodo, {})
            
            # Apdex score (se disponível)
            apdex = safe_first(metricas.get("apdex", []), {}).get("score")
            if apdex is not None:
                metricas_por_periodo[periodo].append(apdex)
    
    # Calculando médias
    medias = {}
    for periodo, valores in metricas_por_periodo.items():
        if valores:
            medias[periodo] = sum(valores) / len(valores)
        else:
            medias[periodo] = 0
    
    # Formatando para o frontend
    series = [{
        "name": "Apdex Médio",
        "data": [round(medias[p], 2) for p in periodos]
    }]
    
    return {
        "series": series,
        "periodos": ["Últimos 30 min", "Últimas 24h", "Últimos 7d"],
        "has_data": any(v > 0 for v in medias.values())
    }

@app.get("/api/cobertura")
async def get_cobertura():
    """Endpoint para dados de cobertura de monitoramento"""
    cache = await get_cache()
    entidades = cache.get("entidades", [])
    
    if not entidades:
        return {
            "labels": [],
            "series": [],
            "totals": {"apps": 0, "servers": 0, "databases": 0, "browsers": 0}
        }
    
    # Contagem por domínio
    dominios = {}
    for e in entidades:
        domain = e.get("domain")
        dominios[domain] = dominios.get(domain, 0) + 1
    
    # Mapeando tipos para categorias mais amplas
    totals = {
        "apps": dominios.get("APM", 0),
        "servers": dominios.get("INFRA", 0),
        "databases": dominios.get("DB", 0) + dominios.get("SYNTH", 0),
        "browsers": dominios.get("BROWSER", 0) + dominios.get("MOBILE", 0)
    }
    
    # Formatando para gráfico
    labels = list(dominios.keys())
    series = list(dominios.values())
    
    return {
        "labels": labels,
        "series": series,
        "totals": totals
    }

@app.get("/api/insights")
async def get_insights():
    """Endpoint para insights estratégicos"""
    cache = await get_cache()
    entidades = cache.get("entidades", [])
    
    entidades_validas = filter_entities_with_data(entidades)
    
    if not entidades_validas:
        return {"insights": []}
    
    # Filtrando por APM para análise de performance
    apps = [e for e in entidades_validas if e.get("domain") == "APM"]
    
    insights = []
    
    # Insight 1: Aplicações com pior Apdex
    if apps:
        # Ordenando por Apdex (menor primeiro)
        apps_by_apdex = sorted(
            apps,
            key=lambda e: safe_first(e.get("metricas", {}).get("30min", {}).get("apdex", []), {}).get("score", 1),
            reverse=False
        )
        
        if apps_by_apdex and len(apps_by_apdex) > 0:
            worst_app = apps_by_apdex[0]
            apdex = safe_first(worst_app.get("metricas", {}).get("30min", {}).get("apdex", []), {}).get("score")
            
            if apdex is not None and apdex < 0.9:
                insights.append({
                    "titulo": "Aplicação com baixa satisfação",
                    "descricao": f"A aplicação {worst_app.get('name')} tem Apdex de {apdex:.2f}, abaixo do recomendado (0.9+)",
                    "severidade": "alta" if apdex < 0.7 else "média",
                    "tipo": "performance"
                })
    
    # Insight 2: Infraestrutura com problemas
    infra = [e for e in entidades_validas if e.get("domain") == "INFRA"]
    hosts_with_issues = [
        h for h in infra
        if h.get("metricas", {}).get("30min", {}).get("cpu_utilization", []) and 
        safe_first(h.get("metricas", {}).get("30min", {}).get("cpu_utilization", []), {}).get("average") > 80
    ]
    
    if hosts_with_issues:
        insights.append({
            "titulo": "Servidores com alta utilização",
            "descricao": f"{len(hosts_with_issues)} servidores com CPU acima de 80% nas últimas 30 minutos",
            "severidade": "média",
            "tipo": "infraestrutura"
        })
    
    # Insight 3: Erros recentes
    apps_with_errors = [
        a for a in apps
        if a.get("metricas", {}).get("30min", {}).get("recent_error", [])
    ]
    
    if apps_with_errors:
        insights.append({
            "titulo": "Aplicações com erros recentes",
            "descricao": f"{len(apps_with_errors)} aplicações reportaram erros nos últimos 30 minutos",
            "severidade": "alta",
            "tipo": "erros"
        })
    
    return {"insights": insights}

@app.get("/api/entidades", response_model=List[Dict])
async def get_entidades():
    """
    Endpoint para listar todas as entidades com seus detalhes,
    garantindo que apenas entidades com dados válidos sejam retornadas.
    """
    try:
        cache = await get_cache()
        entidades = cache.get("entidades", [])
        
        # Processa e filtra entidades para garantir dados válidos
        entidades_validas = filter_entities_with_data(entidades)
        
        logger.info(f"Retornando {len(entidades_validas)} entidades válidas de {len(entidades)} totais")
        return entidades_validas
    
    except Exception as e:
        logger.error(f"Erro ao buscar entidades: {e}", exc_info=True)
        return []

@app.post("/api/limits/reset")
async def reset_token_limits():
    """Endpoint para resetar limites de uso de tokens (apenas para ambiente de teste)"""
    try:
        from pathlib import Path
        import json
        from datetime import datetime
        
        usage_file = Path("logs/token_usage.json")
        if usage_file.exists():
            with open(usage_file, "w") as f:
                usage_data = {"date": datetime.now().strftime("%Y-%m-%d"), "tokens": 0}
                json.dump(usage_data, f)
            return {"sucesso": True, "mensagem": "Limite de tokens resetado com sucesso"}
        else:
            return {"sucesso": False, "mensagem": "Arquivo de controle de tokens não encontrado"}
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao resetar limite: {str(e)}"}

# Configuração para execução direta (dev)
if __name__ == "__main__":
    uvicorn.run("unified_backend:app", host="127.0.0.1", port=8000, reload=True)
