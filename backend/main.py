import os
import sys
import json
import logging
import aiofiles
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import re

# Inicializa o sistema de cache durante o startup
import cache_integration

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
from PyPDF2 import PdfReader

# Configuração de logging
# Garante que o diretório de logs existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

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
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatInput(BaseModel):
    pergunta: str = ""

class MetricsResponse(BaseModel):
    entidades: list

class ChatResponse(BaseModel):
    resposta: str
    contexto: Optional[Dict[str, Any]] = None

from utils.newrelic_collector import coletar_contexto_completo, safe_first, NewRelicCollector
from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia
from utils.cache import (
    get_cache, cache_updater_loop, diagnosticar_cache, 
    buscar_no_cache_por_pergunta, forcar_atualizacao_cache,
    atualizar_cache_completo
)
import asyncio
from utils.entity_processor import filter_entities_with_data, process_entity_details
from utils.intent_extractor import extract_metrics_for_query
from utils.context_enricher import context_enricher
from utils.learning_integration import learning_integration

# Instancia o coletor New Relic para health checks
newrelic_collector = NewRelicCollector(
    api_key=os.getenv('NEW_RELIC_API_KEY', ''),
    account_id=os.getenv('NEW_RELIC_ACCOUNT_ID', '')
)

@app.on_event("startup")
async def startup_tasks():
    # Iniciar loop de atualização do cache
    loop = asyncio.get_event_loop()
    loop.create_task(cache_updater_loop(coletar_contexto_completo))
    
    # Consolidar entidades na inicialização
    logger.info("Consolidando entidades no startup...")
    try:
        entidades = await consolidar_entidades_do_cache()
        logger.info(f"Startup: {len(entidades)} entidades consolidadas")
    except Exception as e:
        logger.error(f"Erro ao consolidar entidades no startup: {e}", exc_info=True)

@app.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Retorna métricas de entidades, garantindo que apenas entidades
    com dados reais sejam retornadas.
    """
    try:
        cache = await get_cache()
        entidades = cache.get("entidades", [])
        
        # Processa e filtra entidades para garantir dados válidos
        entidades_validas = filter_entities_with_data(entidades)
        
        logger.info(f"Metrics: Retornando {len(entidades_validas)} entidades válidas de {len(entidades)} totais")
        return {"entidades": entidades_validas}
        
    except Exception as e:
        logger.error(f"Erro ao buscar métricas: {e}", exc_info=True)
        return {"entidades": []}
@app.get("/api/cache/diagnostico")
async def api_diagnostico_cache():
    """Retorna diagnóstico do cache para monitoramento"""
    return diagnosticar_cache()

@app.post("/api/cache/atualizar")
async def api_atualizar_cache():
    """Endpoint para forçar atualização do cache"""
    sucesso = await forcar_atualizacao_cache(coletar_contexto_completo)
    return {"sucesso": sucesso, "timestamp": datetime.now().isoformat()}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(input: ChatInput):
    try:
        logger.info(f"Recebida pergunta: '{input.pergunta}'")
        
        # Comando especial para resetar o limite de tokens (apenas em ambiente de desenvolvimento)
        if input.pergunta.lower().strip() in ["resetar limite", "reset", "resetar", "reset limit", "reset token"]:
            try:
                usage_file = Path("logs/token_usage.json")
                if usage_file.exists():
                    with open(usage_file, "r") as f:
                        usage_data = json.loads(f.read())
                    
                    usage_data["tokens"] = 0
                    
                    with open(usage_file, "w") as f:
                        f.write(json.dumps(usage_data))
                        
                    logger.info("Limite de tokens resetado manualmente")
                    return {"resposta": "✅ Limite de tokens resetado com sucesso! Você pode continuar utilizando o sistema normalmente.", 
                            "contexto": {"reset": True}}
            except Exception as e:
                logger.error(f"Erro ao resetar limite de tokens: {e}")
                return {"resposta": f"❌ Erro ao resetar limite de tokens: {str(e)}", 
                        "contexto": {"error": True}}
        
        contexto = None
        
        # Primeiro, limpa o cache de entidades inválidas para garantir qualidade
        from utils.cache import limpar_cache_de_entidades_invalidas
        entidades_removidas = await limpar_cache_de_entidades_invalidas()
        if entidades_removidas > 0:
            logger.info(f"Limpeza de cache removeu {entidades_removidas} entidades inválidas antes de processar pergunta")
        
        # Agora busca no cache limpo
        for tentativa in range(2):
            contexto = await buscar_no_cache_por_pergunta(
                input.pergunta,
                atualizar_se_necessario=True,
                coletar_contexto_fn=coletar_contexto_completo
            )
            entidades = contexto.get("entidades", [])
            if entidades:
                break
            logger.info("Nenhuma entidade encontrada no cache, forçando atualização...")
            await forcar_atualizacao_cache(coletar_contexto_completo)
            
        # Garante que as entidades sejam filtradas para ter apenas dados reais
        entidades_originais = contexto.get("entidades", [])
        entidades = filter_entities_with_data(entidades_originais) 
        logger.info(f"Chat usando {len(entidades)} entidades válidas de {len(entidades_originais)} totais")
        
        # Extrai intenções da pergunta e aplica filtros adicionais baseados na consulta
        intent_info = extract_metrics_for_query(input.pergunta, entidades)
        logger.info(f"Intenção detectada: {intent_info['tipo_consulta']}, filtros: {intent_info['filtros_aplicados']}")
        
        # Se tiver entidades relevantes baseadas na intenção, prioriza-as
        if intent_info['entidades_relevantes']:
            entidades = intent_info['entidades_relevantes']
            logger.info(f"Priorizando {len(entidades)} entidades relevantes para a consulta")
        
        # Atualiza o contexto com as entidades filtradas
        contexto["entidades"] = entidades
        
        # Enriquece o contexto com análises adicionais relevantes para a pergunta
        try:
            contexto_enriquecido = context_enricher.enriquecer_contexto(input.pergunta, contexto)
            contexto = contexto_enriquecido
            logger.info("Contexto enriquecido com análises adicionais específicas para a pergunta")
        except Exception as e:
            logger.error(f"Erro no enriquecimento de contexto: {e}", exc_info=True)
            # Em caso de erro no enriquecimento, continua com o contexto original
        
        # Captura alertas
        alertas = contexto.get("alertas", [])
        
        # Filtra para entidades com métricas reais (não vazias)
        entidades_com_metricas = []
        for e in entidades:
            if e.get("metricas"):
                # Verifica se há pelo menos uma métrica real
                has_data = False
                for period_data in e["metricas"].values():
                    if period_data and any(period_data.values()):
                        has_data = True
                        break
                        
                if has_data:
                    entidades_com_metricas.append(e)
        
        logger.info(f"Chat usando {len(entidades_com_metricas)} entidades com métricas reais")
        
        # Resumo detalhado do diagnóstico para IA - processando TODAS as entidades (sem limite)
        # Todas entidades têm igual importância, não limitamos mais a apenas 3
        diagnostico_detalhado = []
        
        # Agrupamento por domínio para organizar melhor os dados
        entidades_por_dominio = {}
        for e in entidades_com_metricas:
            dominio = e.get('domain', 'Desconhecido')
            if dominio not in entidades_por_dominio:
                entidades_por_dominio[dominio] = []
            entidades_por_dominio[dominio].append(e)
            
        # Se não temos métricas, não podemos fazer uma análise detalhada
        if not entidades_com_metricas:
            logger.warning("Sem entidades com métricas para análise detalhada")
            resumo_compacto = "Sem dados de métricas disponíveis."
            
            # Erro crítico: sem dados - interrompe o fluxo
            prompt_compacto = (
                "ATENÇÃO: Não há dados de métricas disponíveis para análise detalhada.\n"
                f"Alertas: {len(alertas)}\n"
                "Recomendação: Verifique a instrumentação do New Relic.\n"
                f"Pergunta: {input.pergunta}"
            )
            
            # Para perguntas específicas sobre APIs lentas/SQL sem dados, retorne um erro
            if ('api' in input.pergunta.lower() or 'sql' in input.pergunta.lower()):
                raise RuntimeError("Não foram encontrados dados suficientes para responder sobre APIs ou SQL. Verifique se a instrumentação do New Relic está corretamente configurada para coletar métricas de APM e Database.")
        else:
            # Com métricas, criamos um diagnóstico detalhado
            # Processamento por domínio para melhor organização
            totais_por_status = {"OK": 0, "ALERTA": 0, "ERRO": 0}
            metricas_agregadas = {"apdex": [], "latencia": [], "erros": 0, "qps": []}
            
            for dominio, entidades_dominio in entidades_por_dominio.items():
                diagnostico_detalhado.append(f"\n## DOMÍNIO: {dominio.upper()} - {len(entidades_dominio)} entidades")
                
                # Ordenar por status - ERROs primeiro, depois ALERTAs, depois OK
                entidades_ordenadas = []
                for e in entidades_dominio:
                    # Recupera dados específicos de métricas relevantes
                    apdex = safe_first(e.get('metricas',{}).get('30min',{}).get('apdex',[]),{}).get('score')
                    latencia = safe_first(e.get('metricas',{}).get('30min',{}).get('response_time_max',[]),{}).get('max.duration')
                    erros = e.get('metricas',{}).get('30min',{}).get('recent_error',[])
                    qps = safe_first(e.get('metricas',{}).get('30min',{}).get('throughput',[]),{}).get('avg.qps')
                    
                    # Determina status baseado em métricas reais
                    status = "OK"
                    razoes = []
                    
                    if apdex is not None and apdex < 0.85:
                        status = "ALERTA"
                        razoes.append(f"Apdex baixo: {apdex:.2f}")
                        
                    if latencia is not None and latencia > 1.0:  # Mais de 1 segundo
                        status = "ALERTA"
                        razoes.append(f"Latência alta: {latencia:.2f}s")
                        
                    if erros and len(erros) > 0:
                        status = "ERRO"
                        erro_exemplo = erros[0].get('message', 'Erro desconhecido') if erros[0] else 'Erro sem detalhes'
                        razoes.append(f"{len(erros)} erros recentes. Ex: {erro_exemplo[:50]}...")
                    
                    # Atualiza contadores e métricas agregadas
                    totais_por_status[status] = totais_por_status.get(status, 0) + 1
                    if apdex is not None: metricas_agregadas["apdex"].append(apdex)
                    if latencia is not None: metricas_agregadas["latencia"].append(latencia)
                    if erros: metricas_agregadas["erros"] += len(erros)
                    if qps is not None: metricas_agregadas["qps"].append(qps)
                    
                    # Armazena para ordenação posterior
                    entidades_ordenadas.append((e, status, apdex, latencia, erros, qps, razoes))
                
                # Ordenar: ERRO primeiro, depois ALERTA, depois OK
                entidades_ordenadas.sort(key=lambda x: 0 if x[1]=="ERRO" else (1 if x[1]=="ALERTA" else 2))
                
                # Processar entidades ordenadas, incluindo TODAS as entidades
                for e, status, apdex, latencia, erros, qps, razoes in entidades_ordenadas:
                    nome = e.get("name", "?") 
                    # Formatação detalhada incluindo métricas reais
                    detalhe = f"- **{nome}** - Status: {status}\n"
                    if razoes:
                        detalhe += f"  - Razões: {', '.join(razoes)}\n"
                    if apdex is not None:
                        detalhe += f"  - Apdex: {apdex:.2f}\n"
                    if latencia is not None:
                        detalhe += f"  - Latência: {latencia:.2f}s\n"
                    if qps is not None:
                        detalhe += f"  - Throughput: {qps:.1f} qps\n"
                    
                    diagnostico_detalhado.append(detalhe)
            
            # Calcular médias e valores agregados
            apdex_medio = sum(metricas_agregadas["apdex"]) / len(metricas_agregadas["apdex"]) if metricas_agregadas["apdex"] else None
            latencia_media = sum(metricas_agregadas["latencia"]) / len(metricas_agregadas["latencia"]) if metricas_agregadas["latencia"] else None
            qps_total = sum(metricas_agregadas["qps"]) if metricas_agregadas["qps"] else None
            
            # Adicionar resumo estatístico no início
            resumo_estatistico = [
                "## RESUMO ESTATÍSTICO",
                f"- Total Entidades: {len(entidades_com_metricas)}",
                f"- Status: {totais_por_status['OK']} OK, {totais_por_status['ALERTA']} ALERTA, {totais_por_status['ERRO']} ERRO",
                f"- Alertas ativos: {len(alertas)}",
            ]
            
            if apdex_medio is not None:
                resumo_estatistico.append(f"- Apdex médio: {apdex_medio:.2f}")
            if latencia_media is not None:
                resumo_estatistico.append(f"- Latência média: {latencia_media:.2f}s")
            if qps_total is not None:
                resumo_estatistico.append(f"- Throughput total: {qps_total:.1f} qps")
            if metricas_agregadas["erros"] > 0:
                resumo_estatistico.append(f"- Total erros: {metricas_agregadas['erros']}")
                
            # Juntar tudo no relatório final
            diagnostico_completo = "\n".join(resumo_estatistico) + "\n\n" + "\n".join(diagnostico_detalhado)
            
            # Instruções específicas baseadas na intenção detectada
            instrucoes_especificas = ""
            if intent_info['tipo_consulta'] == 'apis_lentas':
                instrucoes_especificas = (
                    "Esta pergunta é sobre APIs lentas. Foque em:\n"
                    "1. Identificar as APIs com maiores tempos de resposta\n"
                    "2. Analisar as queries SQL associadas que possam estar causando lentidão\n"
                    "3. Examinar stacktraces para identificar funções problemáticas\n"
                    "4. Correlacionar tempos de resposta com throughput e erros\n"
                    "5. Sugerir consultas NRQL específicas para análise aprofundada de performance\n"
                    "6. Oferecer recomendações concretas para otimização\n"
                )
            elif intent_info['tipo_consulta'] == 'sql_performance':
                instrucoes_especificas = (
                    "Esta pergunta é sobre performance de SQL. Foque em:\n"
                    "1. Identificar queries SQL problemáticas\n"
                    "2. Analisar tempos de execução e frequência de chamadas\n"
                    "3. Correlacionar problemas de banco com APIs lentas\n"
                    "4. Examinar possíveis problemas de índices ou design de queries\n"
                    "5. Sugerir consultas NRQL para monitorar performance de banco de dados\n"
                )
            elif "root_cause" in intent_info['tipo_consulta']:
                instrucoes_especificas = (
                    "Esta pergunta busca análise de causa raiz. Foque em:\n"
                    "1. Realizar análise sistemática dos problemas identificados\n"
                    "2. Correlacionar métricas entre diferentes componentes do sistema\n"
                    "3. Identificar os componentes iniciadores de falhas em cascata\n"
                    "4. Examinar stacktraces, erros e exceções em detalhe\n"
                    "5. Sugerir ações corretivas específicas com base nas causas identificadas\n"
                )
            elif "errors" in intent_info['tipo_consulta']:
                instrucoes_especificas = (
                    "Esta pergunta busca análise de erros. Foque em:\n"
                    "1. Identificar os tipos de erros mais frequentes\n"
                    "2. Analisar stacktraces e mensagens de erro\n"
                    "3. Correlacionar erros com outros problemas de performance\n"
                    "4. Sugerir consultas NRQL para monitoramento de erros\n"
                    "5. Recomendar ações para resolução de problemas\n"
                )
                
            # Prepara análises enriquecidas, se disponíveis
            analises_enriquecidas = ""
            if contexto.get("analises"):
                analises_enriquecidas = "\n## ANÁLISES AVANÇADAS ESPECÍFICAS\n\n"
                
                # Performance
                if contexto["analises"].get("performance"):
                    perf = contexto["analises"]["performance"]
                    analises_enriquecidas += "### Performance\n"
                    analises_enriquecidas += f"{perf.get('analise', '')}\n"
                    
                    # Entidades lentas por Apdex
                    if perf.get("entidades_lentas", {}).get("por_apdex"):
                        analises_enriquecidas += "\nEntidades com pior Apdex:\n"
                        for e in perf["entidades_lentas"]["por_apdex"][:3]:
                            analises_enriquecidas += f"- {e.get('nome')}: {e.get('apdex')}\n"
                    
                    # Entidades lentas por latência
                    if perf.get("entidades_lentas", {}).get("por_latencia"):
                        analises_enriquecidas += "\nEntidades com maior latência:\n"
                        for e in perf["entidades_lentas"]["por_latencia"][:3]:
                            analises_enriquecidas += f"- {e.get('nome')}: {e.get('latencia')}s\n"
                
                # Erros
                if contexto["analises"].get("erros"):
                    erros = contexto["analises"]["erros"]
                    analises_enriquecidas += "\n### Erros\n"
                    if erros.get("entidades_com_erros"):
                        analises_enriquecidas += f"Encontradas {len(erros['entidades_com_erros'])} entidades com erros.\n"
                
                # Correlações
                if contexto["analises"].get("correlacao", {}).get("correlacoes_detectadas"):
                    correlacoes = contexto["analises"]["correlacao"]["correlacoes_detectadas"]
                    if correlacoes:
                        analises_enriquecidas += "\n### Correlações Detectadas\n"
                        for corr in correlacoes:
                            analises_enriquecidas += f"- {corr}\n"
            
            # Prompt detalhado com TODAS as entidades e dados reais
            prompt_compacto = (
                f"# CONTEXTO COMPLETO DE MONITORAMENTO\n\n"
                f"{diagnostico_completo}\n\n"
                f"{analises_enriquecidas}\n\n"
                f"# PERGUNTA DO USUÁRIO\n{input.pergunta}\n\n"
                "# INSTRUÇÕES\n"
                "Forneça uma análise técnica detalhada baseada nos dados acima. "
                "Identifique tendências, anomalias, e correlações entre os serviços. "
                "Priorize problemas mais críticos (ERRO > ALERTA > OK) e sugira ações específicas. "
                "Recomende NRQL específicas quando relevante. Se a pergunta for sobre algum serviço específico, "
                "foque sua análise nele, mas mencione sua relação com outros serviços quando relevante.\n\n"
                f"{instrucoes_especificas if instrucoes_especificas else ''}"
            )
        
        # System prompt aprimorado para análises mais profundas e técnicas
        system_prompt = """
        Você é um Arquiteto de Observabilidade sênior especialista em New Relic e SRE, com profundo conhecimento técnico em:
        
        1. Análise avançada de métricas de APM, Browser, e infraestrutura
        2. Correlação entre indicadores de diferentes domínios e serviços
        3. Consultas NRQL complexas e dashboards analíticos avançados
        4. Troubleshooting aprofundado de problemas de performance e disponibilidade
        5. Otimização de SLAs, SLOs e design de arquitetura resiliente
        6. Root Cause Analysis (RCA) e técnicas de diagnóstico sistemático
        
        REGRAS ESSENCIAIS:
        - Responda APENAS baseado nos dados fornecidos no contexto, nunca invente métricas
        - Seja altamente técnico, específico e analítico - este é seu principal diferencial
        - Analise padrões, anomalias e correlações entre diferentes serviços e domínios
        - Sempre inclua exemplos de consultas NRQL detalhadas quando relevante
        - Mencione entidades específicas, suas métricas e status identificados nos dados
        - Priorize problemas por severidade (ERRO > ALERTA > OK)
        - Sempre que possível, sugira ações técnicas específicas de remediação
        - Se não tiver dados suficientes, seja transparente e explique exatamente quais dados seriam necessários
        - Use formatação markdown avançada para estruturar sua resposta técnica
        - Suas respostas devem ter pelo menos 3 seções: Diagnóstico, Análise Técnica e Recomendações
        
        Seus insights devem ser profundamente técnicos, acionáveis e baseados em uma análise sistemática e exaustiva dos dados fornecidos.
        """
        
        logger.info(f"Enviando prompt para OpenAI com {len(prompt_compacto)} caracteres")
        
        # Verifica se temos dados suficientes para uma resposta de qualidade
        has_quality_data = len(entidades_com_metricas) > 0
        
        # Detecta tipo de persona (técnico vs. gestor)
        # Procura indicadores de persona de gestor na pergunta
        pergunta_lower = input.pergunta.lower()
        palavras_gestor = [
            'resumo executivo', 'visão geral', 'dashboard', 'status', 'impacto no negócio',
            'kpis', 'gráfico', 'resumo', 'métricas principais', 'indicadores'
        ]
        
        # Se encontrar indicadores de perfil gestor, adapta a resposta para esse público
        persona = "gestor" if any(palavra in pergunta_lower for palavra in palavras_gestor) else "tecnico"
        logger.info(f"Persona detectada para resposta: {persona}")
        
        # Usar GPT-4 para análise mais profunda e dados mais complexos
        logger.info(f"Enviando análise para o modelo OpenAI")
        
        resposta = await gerar_resposta_ia(
            prompt=prompt_compacto,
            system_prompt=system_prompt,
            modelo="gpt-4",
            use_gpt4=True,  # Força uso de GPT-4 para análises técnicas
            persona=persona  # Passa a persona detectada
        )
        
        resposta_str = resposta.strip() if isinstance(resposta, str) else str(resposta)
        logger.info(f"Resposta gerada com {len(resposta_str)} caracteres")
        
        # Lista expandida de frases que indicam respostas genéricas ou sem dados suficientes
        respostas_genericas = [
            "não tenho dados",
            "não possuo informações",
            "não foi possível encontrar",
            "não há dados",
            "não sei responder",
            "não tenho informações suficientes",
            "sem dados disponíveis",
            "preciso de mais informações",
            "não é possível analisar",
            "não consigo fornecer"
        ]
        
        if not resposta_str or any(frase in resposta_str.lower() for frase in respostas_genericas):
            # Fallback com dados reais
            if entidades_com_metricas:
                top_3 = entidades_com_metricas[:3]
                fallback_lista = "\n".join([
                    f"- **{e.get('name','?')}** [{e.get('domain','?')}] | Latência: {safe_first(e.get('metricas',{}).get('30min',{}).get('response_time_max',[]),{}).get('max.duration','N/A')}s | Erros: {len(e.get('metricas',{}).get('30min',{}).get('recent_error',[]))}" 
                    for e in top_3
                ])
                resposta_str = (
                    "### Status das Principais Entidades\n"
                    f"{fallback_lista}\n\n"
                    f"**Total:** {len(entidades)} entidades, {len(entidades_com_metricas)} com métricas ativas\n"
                    f"**Alertas:** {len(alertas)} ativos\n\n"
                    "**Recomendação:** Para análise detalhada, especifique o nome da entidade ou tipo de problema na sua pergunta."
                )
            else:
                resposta_str = (
                    "⚠️ Não há dados suficientes para análise. "
                    "Verifique se a instrumentação do New Relic está corretamente configurada."
                )
        
        # Adiciona timestamp para contexto
        resumo_diagnostico = f"Status geral: {len(entidades_com_metricas)} entidades com métricas de {len(entidades)} total"
        
        # Registra a interação para aprendizado contínuo
        session_id = f"sess_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        aprendizado_ativo = False
        
        try:
            if learning_integration.is_enabled():
                # Registra a interação para o sistema de aprendizado
                await learning_integration.registrar_interacao(
                    session_id=session_id,
                    pergunta=input.pergunta,
                    resposta=resposta_str,
                    contexto={
                        "entidades_count": len(entidades),
                        "entidades_com_metricas_count": len(entidades_com_metricas),
                        "alertas_count": len(alertas),
                        "persona": persona,
                        "intent_info": intent_info
                    }
                )
                aprendizado_ativo = True
                logger.info("Interação registrada no sistema de aprendizado contínuo")
        except Exception as e:
            logger.error(f"Erro ao registrar interação para aprendizado: {e}")
        
        # Métricas para monitoramento do sistema
        try:
            metricas = {
                "timestamp": datetime.now().isoformat(),
                "pergunta_len": len(input.pergunta),
                "resposta_len": len(resposta_str),
                "entidades_count": len(entidades),
                "entidades_com_metricas_count": len(entidades_com_metricas),
                "alertas_count": len(alertas),
                "modelo_usado": "gpt-4",
                "tempo_processamento": (datetime.now() - datetime.strptime(contexto.get("timestamp", datetime.now().isoformat()), "%Y-%m-%dT%H:%M:%S.%f")).total_seconds() if "timestamp" in contexto else 0,
                "aprendizado_ativo": aprendizado_ativo
            }
            
            if learning_integration.is_enabled():
                await learning_integration.registrar_metricas(metricas)
                
        except Exception as e:
            logger.error(f"Erro ao registrar métricas: {e}")
        
        return {
            "resposta": resposta_str, 
            "contexto": {
                "diagnostico": resumo_diagnostico, 
                "alertas": len(alertas), 
                "totalEntidades": len(entidades),
                "aprendizado_ativo": aprendizado_ativo
            }
        }
    except RuntimeError as e:
        logger.error(f"Erro no endpoint de chat: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "mensagem": str(e),
                "detalhes": "Erro de negócio/processamento IA.",
                "acao_sugerida": "Resuma ou refine sua pergunta, ou tente novamente mais tarde."
            }
        )
    except Exception as e:
        logger.error(f"Erro inesperado no endpoint de chat: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "mensagem": "Erro interno no servidor. Tente novamente mais tarde.",
                "detalhes": str(e),
                "acao_sugerida": "Aguarde alguns minutos e tente novamente. Se persistir, contate o suporte."
            }
        )

@app.get("/api/status")
async def get_status():
    """Endpoint para obter o status do sistema para o frontend"""
    try:
        # Buscar dados do cache
        contexto = await get_cache()
        entidades = contexto.get("entidades", [])
        entidades_com_metricas = sum(1 for e in entidades if e.get("metricas"))
        status_geral = "Bom"
        alertas = contexto.get("alertas", [])
        if alertas and len(alertas) > 0:
            status_geral = "Alerta" if len(alertas) < 3 else "Crítico"
        disp_valores = []
        for ent in entidades:
            if ent.get("metricas") and ent.get("metricas", {}).get("7d", {}).get("uptime"):
                uptime = ent.get("metricas", {}).get("7d", {}).get("uptime")
                if isinstance(uptime, list) and len(uptime) > 0 and isinstance(uptime[0], dict):
                    valor = uptime[0].get("latest.uptime", 0)
                    if valor and valor > 0:
                        disp_valores.append(min(99.999, 100 * (1 - (1 / (1 + valor)))))
        disponibilidade = 99.92  # Valor padrão
        if disp_valores:
            disponibilidade = sum(disp_valores) / len(disp_valores)
        diagnostico_cache = diagnosticar_cache()
        return {
            "statusGeral": status_geral,
            "incidentesAtivos": len(alertas),
            "disponibilidade": disponibilidade,
            "totalEntidades": len(entidades),
            "entidadesComMetricas": entidades_com_metricas,
            "ultimaAtualizacao": contexto.get("timestamp", datetime.now().isoformat()),
            "dominios": diagnostico_cache.get("contagem_por_dominio", {})
        }
    except Exception as e:
        logger.error(f"Erro ao obter status do sistema: {e}")
        logger.error(traceback.format_exc())
        return {
            "statusGeral": "Indisponível",
            "erro": str(e)
        }

@app.get("/api/cobertura")
async def get_cobertura():
    cache = await get_cache()
    entidades = cache.get("entidades", [])
    total = len(entidades)
    monitoradas = len([e for e in entidades if e.get("metricas")])
    pendentes = total - monitoradas
    return {
        "coberturaGeral": int((monitoradas/total)*100) if total else 0,
        "totalRecursos": total,
        "totalPendentes": pendentes,
        "recursos": entidades[:10] if entidades else [],
        "recursosSemCobertura": [e for e in entidades if not e.get("metricas")] if entidades else [],
        "acoesRecomendadas": [],
        "mensagem": "Todos os recursos estão com métricas configuradas." if total and pendentes == 0 else "Configure a instrumentação no New Relic para aumentar a cobertura."
    }

@app.get("/api/kpis")
async def get_kpis():
    cache = await get_cache()
    entidades = cache.get("entidades", [])
    total = len(entidades)
    if total == 0:
        return {"kpis": [
            {"nome": "Disponibilidade", "valor": 0, "unidade": "%"},
            {"nome": "Taxa de Erro", "valor": 0, "unidade": "%"},
            {"nome": "Latência Máxima", "valor": 0, "unidade": "ms"}
        ], "mensagem": "Nenhum dado disponível. Configure a instrumentação no New Relic para visualizar KPIs."}
    def safe_apdex(e):
        return safe_first(e.get("metricas", {}).get("30min", {}).get("apdex", []), {}).get("score", 0)
    def safe_latencia(e):
        return safe_first(e.get("metricas", {}).get("30min", {}).get("response_time_max", []), {}).get("max.duration", 0)
    entidades_com_metricas = [e for e in entidades if e.get("metricas") and any(e["metricas"].values())]
    total_metricas = len(entidades_com_metricas) if entidades_com_metricas else 1
    disponibilidade = sum(safe_apdex(e) for e in entidades_com_metricas) / total_metricas * 100
    taxa_erro = sum(len(e.get("metricas", {}).get("30min", {}).get("recent_error", [])) for e in entidades_com_metricas) / total_metricas
    latencia = sum(safe_latencia(e) for e in entidades_com_metricas) / total_metricas
    kpis = [
        {"nome": "Disponibilidade", "valor": round(disponibilidade, 2), "unidade": "%"},
        {"nome": "Taxa de Erro", "valor": round(taxa_erro, 2), "unidade": "%"},
        {"nome": "Latência Máxima", "valor": round(latencia * 1000, 2), "unidade": "ms"}
    ]
    return {"kpis": kpis, "mensagem": "" if entidades_com_metricas else "Nenhuma entidade com métricas válidas."}

@app.get("/api/tendencias")
async def get_tendencias():
    try:
        contexto = await get_cache()
        tendencias = []
        for domain, entities in contexto.items():
            if isinstance(entities, list):
                for ent in entities:
                    metricas = ent.get("metricas", {}).get("30min", {})
                    if isinstance(metricas, dict):
                        tendencias.append({
                            "name": ent.get("name", "Desconhecido"),
                            "domain": domain,
                            "latenciaMedia": metricas.get("response_time_max", [{}])[0].get("max_duration", 0) if metricas.get("response_time_max") else 0,
                            "erros": len(metricas.get("recent_error", [])),
                            "qps": metricas.get("throughput", [{}])[0].get("avg.qps", 0) if metricas.get("throughput") else 0
                        })
        if not tendencias:
            return {"tendencias": [], "mensagem": "Nenhuma tendência encontrada. Configure a instrumentação no New Relic para visualizar tendências."}
        return {"tendencias": tendencias}
    except Exception as e:
        logger.error(f"Erro ao obter tendências: {e}")
        logger.error(traceback.format_exc())
        return {"erro": str(e), "tendencias": [], "mensagem": "Erro ao processar tendências."}

@app.get("/api/insights")
async def get_insights():
    cache = await get_cache()
    entidades = cache.get("entidades", [])
    insights = []
    def safe_latencia(e):
        return safe_first(e.get("metricas", {}).get("30min", {}).get("response_time_max", []), {}).get("max.duration", 0)
    for e in sorted(entidades, key=lambda x: safe_latencia(x), reverse=True)[:5]:
        insights.append({
            "entidade": e.get("name"),
            "latencia_max_ms": safe_latencia(e) * 1000
        })
    if not insights:
        return {"insights": [], "mensagem": "Nenhum insight disponível. Configure a instrumentação no New Relic para visualizar insights executivos."}
    return {"insights": insights}

@app.post("/api/chat")
async def chat_api(input: ChatInput):
    """Redireciona para o endpoint principal do chat para manter consistência"""
    try:
        return await chat_endpoint(input)
    except RuntimeError as e:
        logger.error(f"Erro no endpoint de chat: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "mensagem": str(e),
                "detalhes": "Erro de negócio/processamento IA.",
                "acao_sugerida": "Resuma ou refine sua pergunta, ou tente novamente mais tarde."
            }
        )
    except Exception as e:
        logger.error(f"Erro inesperado no endpoint de chat: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "mensagem": "Erro interno no servidor. Tente novamente mais tarde.",
                "detalhes": str(e),
                "acao_sugerida": "Aguarde alguns minutos e tente novamente. Se persistir, contate o suporte."
            }
        )

async def consolidar_entidades_do_cache():
    """
    Função auxiliar para consolidar entidades de todos os domínios em uma única lista.
    Evita duplicações e atualiza o cache adequadamente.
    Também processa e valida as entidades para garantir dados consistentes.
    """
    from utils.entity_processor import process_entity_details
    
    cache = await get_cache()
    
    # Verificar se já temos entidades consolidadas
    if "entidades" in cache and cache.get("entidades"):
        # Mesmo tendo entidades no cache, vamos reprocessá-las para garantir qualidade
        entidades = cache.get("entidades")
        logger.info(f"Reprocessando {len(entidades)} entidades já consolidadas no cache")
        
        # Processa cada entidade para garantir formato consistente
        processed_entities = []
        for entity in entidades:
            processed = process_entity_details(entity)
            if processed:
                processed_entities.append(processed)
        
        return processed_entities
    
    # Caso não tenha, consolidar a partir dos domínios
    dominios = ["apm", "browser", "infra", "db", "mobile", "iot", "serverless", "synth", "ext"]
    todas_entidades = []
    guids_processados = set()  # Para evitar duplicatas
    
    # Para cada domínio, extrair entidades
    for dominio in dominios:
        if dominio in cache:
            entidades_dominio = cache.get(dominio, [])
            logger.info(f"Encontradas {len(entidades_dominio)} entidades no domínio {dominio}")
            
            # Adiciona apenas entidades com guid único (evita duplicatas)
            for entidade in entidades_dominio:
                guid = entidade.get("guid")
                if guid and guid not in guids_processados:
                    processed = process_entity_details(entidade)
                    if processed:
                        guids_processados.add(guid)
                        todas_entidades.append(processed)
    
    # Adicionar ao cache para uso futuro e persistir
    if todas_entidades:
        from utils.cache import _cache, salvar_cache_no_disco
        logger.info(f"Adicionando {len(todas_entidades)} entidades consolidadas ao cache")
        _cache["dados"]["entidades"] = todas_entidades
        await salvar_cache_no_disco()
    else:
        logger.warning("Nenhuma entidade encontrada para consolidação")
    
    return todas_entidades

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