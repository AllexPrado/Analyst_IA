

# Endpoint para consultar dados avançados reais de uma entidade por GUID

# (deve ficar após a definição de app e dos imports)

from fastapi import Query
from utils.newrelic_advanced_collector import get_entity_advanced_data

# ...demais endpoints e código...

# Adicione o endpoint no final do arquivo, antes do if __name__ == "__main__":

@app.get("/api/entidade/{guid}/dados_avancados")
async def dados_avancados_entidade(guid: str, period: str = Query("7d", description="Período NRQL: 30min, 3h, 24h, 7d, 30d")):
    """
    Retorna os dados avançados reais do New Relic para uma entidade pelo GUID.
    """
    import aiohttp
    try:
        from utils.newrelic_advanced_collector import get_all_entities
        async with aiohttp.ClientSession() as session:
            entidades = await get_all_entities(session)
            entidade = next((e for e in entidades if e.get("guid") == guid), None)
            if not entidade:
                raise HTTPException(status_code=404, detail=f"Entidade com guid {guid} não encontrada no New Relic")
            dados = await get_entity_advanced_data(entidade, period, session=session)
            return {"guid": guid, "entidade": entidade, "dados_avancados": dados, "periodo": period, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Erro ao coletar dados avançados para guid {guid}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao coletar dados avançados: {e}")
import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uvicorn
import random
import json
from pathlib import Path
import aiohttp
import aiofiles

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicativo FastAPI
app = FastAPI(
    title="API para Dados de Incidentes",
    description="Endpoints para gerenciamento de incidentes e alertas"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caminho para armazenamento dos dados
CACHE_DIR = Path("historico")
INCIDENTES_FILE = CACHE_DIR / "incidentes.json"
ENTIDADES_FILE = CACHE_DIR / "entidades_correlacionadas.json"

# Dados em memória
dados_incidentes = {
    "incidentes": [],
    "alertas": [],
    "timestamp": datetime.now().isoformat(),
    "resumo": {
        "total_incidentes": 0,
        "total_alertas": 0,
        "incidentes_ativos": 0,
        "incidentes_resolvidos": 0,
        "severidade_critica": 0,
        "severidade_warning": 0,
        "severidade_info": 0
    },
    "entidades_associadas": {}  # Nova estrutura para correlação
}

# Carregar dados do New Relic (se disponíveis)
NEW_RELIC_API_KEY = os.getenv("NEW_RELIC_API_KEY")
NEW_RELIC_ACCOUNT_ID = os.getenv("NEW_RELIC_ACCOUNT_ID")

async def carregar_entidades_newrelic():
    """
    Carrega todas as entidades do New Relic para correlacionamento com incidentes
    """
    if not NEW_RELIC_API_KEY or not NEW_RELIC_ACCOUNT_ID:
        logger.warning("Credenciais do New Relic não configuradas. Usando apenas dados locais.")
        return []
        
    try:
        # Importa a função do módulo de coleta (assegurando que está no path)
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from coletor_new_relic import coletar_entidades
        
        # Coleta as entidades
        entidades = await coletar_entidades(NEW_RELIC_API_KEY, NEW_RELIC_ACCOUNT_ID)
        
        logger.info(f"Coletadas {len(entidades)} entidades do New Relic")
        return entidades
    except Exception as e:
        logger.error(f"Erro ao coletar entidades do New Relic: {e}")
        return []

@app.on_event("startup")
async def startup_event():
    # Criar diretório de cache, se não existir
    CACHE_DIR.mkdir(exist_ok=True)
    
    # Carregar dados existentes
    await carregar_dados_existentes()
    
    # Correlacionar incidentes com entidades do New Relic
    await correlacionar_incidentes_entidades()

async def carregar_dados_existentes():
    """Carrega dados de incidentes e entidades de arquivos locais, se disponíveis"""
    try:
        if INCIDENTES_FILE.exists():
            async with aiofiles.open(INCIDENTES_FILE, mode='r') as f:
                conteudo = await f.read()
                dados_incidentes["incidentes"] = json.loads(conteudo).get("incidentes", [])
                logger.info(f"Carregados {len(dados_incidentes['incidentes'])} incidentes do arquivo")
        if ENTIDADES_FILE.exists():
            async with aiofiles.open(ENTIDADES_FILE, mode='r') as f:
                conteudo = await f.read()
                entidades_raw = json.loads(conteudo).get("entidades", [])
                # Normaliza: se for lista de listas, "achata" para lista de dicts
                entidades = []
                for item in entidades_raw:
                    if isinstance(item, list):
                        entidades.extend(item)
                    elif isinstance(item, dict):
                        entidades.append(item)
                logger.info(f"Carregadas {len(entidades)} entidades do arquivo")
                # Adiciona entidades ao histórico
                for entidade in entidades:
                    nome = entidade.get("name", "").lower()
                    if nome and nome not in dados_incidentes["entidades_associadas"]:
                        dados_incidentes["entidades_associadas"][nome] = entidade
    except Exception as e:
        logger.error(f"Erro ao carregar dados existentes: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    # Salvar dados em arquivos
    await salvar_dados()
    
async def salvar_dados():
    """Salva os dados de incidentes e entidades em arquivos locais"""
    try:
        async with aiofiles.open(INCIDENTES_FILE, mode='w') as f:
            await f.write(json.dumps({"incidentes": dados_incidentes["incidentes"]}, indent=4))
            logger.info(f"Dados de incidentes salvos em {INCIDENTES_FILE}")
        # Corrige: salva entidades como lista de dicts, não lista de listas
        entidades_para_salvar = []
        for v in dados_incidentes["entidades_associadas"].values():
            if isinstance(v, list):
                entidades_para_salvar.extend(v)
            elif isinstance(v, dict):
                entidades_para_salvar.append(v)
        async with aiofiles.open(ENTIDADES_FILE, mode='w') as f:
            await f.write(json.dumps({"entidades": entidades_para_salvar}, indent=4))
            logger.info(f"Dados de entidades salvos em {ENTIDADES_FILE}")
    except Exception as e:
        logger.error(f"Erro ao salvar dados: {e}")

from utils.newrelic_advanced_collector import get_all_entities, get_entity_advanced_data

@app.get("/incidentes")
async def listar_incidentes():
    """Lista todos os incidentes com dados avançados reais de cada entidade relacionada"""
    await carregar_dados_do_disco()  # Garantir dados atualizados
    atualizar_resumo()  # Atualiza estatísticas de resumo
    try:
        async with aiohttp.ClientSession() as session:
            entidades = await get_all_entities(session)
            entidades_map = {e.get("guid"): e for e in entidades}
            incidentes_avancados = []
            for incidente in dados_incidentes["incidentes"]:
                entidades_rel = []
                for ent_assoc in dados_incidentes.get("entidades_associadas", {}).get(incidente["id"], []):
                    guid = ent_assoc.get("guid")
                    entidade = entidades_map.get(guid)
                    if entidade:
                        dados_avancados = await get_entity_advanced_data(entidade, "7d", session=session)
                        entidades_rel.append({"guid": guid, "entidade": entidade, "dados_avancados": dados_avancados})
                incidente_c = dict(incidente)
                incidente_c["entidades_dados_avancados"] = entidades_rel
                incidentes_avancados.append(incidente_c)
            return {
                "incidentes": incidentes_avancados,
                "alertas": dados_incidentes["alertas"],
                "timestamp": datetime.now().isoformat(),
                "resumo": dados_incidentes["resumo"]
            }
    except Exception as e:
        logger.error(f"Erro ao coletar dados avançados para incidentes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao coletar dados avançados para incidentes: {e}")

@app.get("/entidades")
async def listar_entidades():
    """Lista todas as entidades do New Relic com dados avançados"""
    try:
        async with aiohttp.ClientSession() as session:
            entidades = await get_all_entities(session)
            entidades_avancadas = []
            for entidade in entidades:
                dados_avancados = await get_entity_advanced_data(entidade, "7d", session=session)
                entidades_avancadas.append({"guid": entidade.get("guid"), "entidade": entidade, "dados_avancados": dados_avancados})
            return {
                "entidades": entidades_avancadas,
                "timestamp": datetime.now().isoformat(),
                "total": len(entidades_avancadas)
            }
    except Exception as e:
        logger.error(f"Erro ao coletar entidades avançadas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao coletar entidades avançadas: {e}")

@app.get("/resumo")
async def resumo_incidentes():
    """Retorna um resumo dos incidentes"""
    atualizar_resumo()  # Garantir dados atualizados
    
    return {
        "resumo": dados_incidentes["resumo"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/analise/{incidente_id}")
async def obter_analise_incidente(incidente_id: str):
    """Fornece uma análise profunda de um incidente específico com dados avançados reais"""
    try:
        async with aiohttp.ClientSession() as session:
            entidades = await get_all_entities(session)
            entidades_map = {e.get("guid"): e for e in entidades}
            entidades_associadas = dados_incidentes.get("entidades_associadas", {}).get(incidente_id, [])
            metricas_entidades = []
            for entidade in entidades_associadas:
                guid = entidade.get("guid")
                entidade_real = entidades_map.get(guid)
                if entidade_real:
                    dados_avancados = await get_entity_advanced_data(entidade_real, "7d", session=session)
                    metricas_entidades.append({"guid": guid, "entidade": entidade_real, "dados_avancados": dados_avancados})
            return {
                "incidente_id": incidente_id,
                "analise": metricas_entidades,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Erro ao coletar análise avançada do incidente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao coletar análise avançada do incidente: {e}")

@app.get("/status-cache")
async def status_cache():
    """Retorna informações sobre o status do cache de incidentes e entidades"""
    # Carregar entidades para estatísticas
    entidades = await carregar_entidades_newrelic()
    
    return {
        "status": "Completo" if entidades and dados_incidentes["incidentes"] else "Incompleto",
        "timestamp": datetime.now().isoformat(),
        "total_entidades_consolidadas": len(entidades),
        "total_alertas": len(dados_incidentes["alertas"]),
        "total_incidentes": len(dados_incidentes["incidentes"]),
        "entidades_por_dominio": contar_entidades_por_dominio(entidades),
        "chaves_disponiveis": list(dados_incidentes.keys()),
        "ultima_atualizacao_cache": dados_incidentes.get("timestamp", "Nunca")
    }
    
async def contar_entidades_por_dominio(entidades):
    """Conta o número de entidades por domínio"""
    contador = {}
    for entidade in entidades:
        dominio = entidade.get("domain", "desconhecido")
        if dominio not in contador:
            contador[dominio] = 0
        contador[dominio] += 1
    return contador

@app.get("/correlacionar")
async def correlacionar_incidentes():
    """Força a correlação de incidentes com entidades do New Relic"""
    await correlacionar_incidentes_entidades()
    return {"mensagem": "Correlação de incidentes concluída"}

async def correlacionar_incidentes_entidades():
    """Correlaciona incidentes com entidades do New Relic para análise profunda e simula métricas detalhadas."""
    # Carregando entidades para correlação
    entidades = await carregar_entidades_newrelic()
    
    if not entidades:
        logger.warning("Nenhuma entidade disponível para correlação")
        return
        
    # Mapeia entidades por nome para fácil referência
    mapa_entidades = {}
    for entidade in entidades:
        nome = entidade.get("name", "").lower()
        if nome:
            mapa_entidades[nome] = entidade
      # Correlaciona incidentes com entidades usando uma abordagem mais flexível
    dados_incidentes["entidades_associadas"] = {}
    
    for incidente in dados_incidentes["incidentes"]:
        servico = incidente.get("impacted_service", "").lower()
        
        # Tentativa 1: Match direto
        if servico in mapa_entidades:
            entidade = mapa_entidades[servico]
        else:
            # Tentativa 2: Busca parcial
            found = False
            for nome_entidade, entidade in mapa_entidades.items():
                if servico in nome_entidade or nome_entidade in servico:
                    found = True
                    break
            
            # Tentativa 3: Usar a primeira entidade disponível como fallback
            if not found and mapa_entidades:
                entidade = list(mapa_entidades.values())[0]
                logger.warning(f"Usando entidade fallback para {servico}")
            else:
                continue
        
        entidade_id = entidade.get("guid")
        if entidade_id:
            if incidente["id"] not in dados_incidentes["entidades_associadas"]:
                dados_incidentes["entidades_associadas"][incidente["id"]] = []
                
            # Simula métricas detalhadas para a entidade
            entidade_com_metricas = dict(entidade)
            entidade_com_metricas["metricas"] = simular_metricas_entidade(entidade)
            dados_incidentes["entidades_associadas"][incidente["id"]].append(entidade_com_metricas)
    
    logger.info(f"Correlação concluída: {len(dados_incidentes.get('entidades_associadas', {}))} incidentes associados a entidades")

@app.get("/analise_causa_raiz/{incidente_id}")
async def analise_causa_raiz(incidente_id: str):
    """Analisa a causa raiz de um incidente específico usando dados avançados reais do New Relic"""
    try:
        async with aiohttp.ClientSession() as session:
            entidades = await get_all_entities(session)
            entidades_map = {e.get("guid"): e for e in entidades}
            entidades_associadas = dados_incidentes.get("entidades_associadas", {}).get(incidente_id, [])
            metricas_entidades = []
            for entidade in entidades_associadas:
                guid = entidade.get("guid")
                entidade_real = entidades_map.get(guid)
                if entidade_real:
                    dados_avancados = await get_entity_advanced_data(entidade_real, "7d", session=session)
                    metricas_entidades.append({"guid": guid, "entidade": entidade_real, "dados_avancados": dados_avancados})
            return {
                "incidente_id": incidente_id,
                "causa_raiz": metricas_entidades,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Erro ao coletar causa raiz avançada do incidente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao coletar causa raiz avançada do incidente: {e}")

async def analisar_causa_raiz(incidente_id):
    """
    Analisa a causa raiz de um incidente específico usando dados reais do New Relic.
    Gera explicações detalhadas, recomendações técnicas e executivas, e resposta humanizada.
    """
    if incidente_id not in dados_incidentes.get("entidades_associadas", {}):
        return {"erro": "Incidente não possui entidades associadas para análise"}

    entidades_associadas = dados_incidentes["entidades_associadas"][incidente_id]
    incidente = next((inc for inc in dados_incidentes["incidentes"] if inc["id"] == incidente_id), None)
    if not incidente:
        return {"erro": "Incidente não encontrado"}

    metricas_entidades = []
    for entidade in entidades_associadas:
        metricas = entidade.get("metricas", {})
        # Aqui você pode expandir para buscar logs, transações, web vitals, etc.
        metricas_entidades.append({
            "nome": entidade.get("name"),
            "guid": entidade.get("guid"),
            "domain": entidade.get("domain"),
            "metricas": metricas
        })

    explicacoes = []
    recomendacoes_dev = []
    recomendacoes_gestor = []
    impacto = []
    for ent in metricas_entidades:
        nome = ent["nome"]
        metricas = ent["metricas"]
        if not metricas:
            explicacoes.append(f"A entidade '{nome}' não possui dados recentes de monitoramento. Pode haver falha de integração ou coleta.")
            recomendacoes_dev.append(f"Verifique a integração do agente New Relic na entidade '{nome}'. Certifique-se de que o serviço está reportando métricas.")
            recomendacoes_gestor.append(f"Acompanhe com a equipe técnica a ausência de dados em '{nome}'. Isso pode indicar falha de monitoramento.")
            impacto.append(f"Sem dados, não é possível estimar o impacto real para '{nome}'.")
        else:
            erros = metricas.get("recent_error")
            apdex = metricas.get("apdex")
            web_vitals = metricas.get("web_vitals")
            transacoes = metricas.get("transactions")
            # Análise de erros
            if erros and isinstance(erros, list) and any(e.get("count", 0) > 0 for e in erros):
                total_erros = sum(e.get("count", 0) for e in erros)
                explicacoes.append(f"A entidade '{nome}' apresentou {total_erros} erros recentes nas últimas horas.")
                recomendacoes_dev.append(f"Investigue os logs de erro em '{nome}'. Corrija exceções e monitore o volume de erros.")
                recomendacoes_gestor.append(f"O serviço '{nome}' apresentou instabilidade. Recomenda-se priorizar a análise pela equipe técnica.")
                impacto.append(f"Possível impacto em usuários devido a falhas recorrentes em '{nome}'.")
            # Análise de apdex
            if apdex and isinstance(apdex, list) and any(a.get("score", 1) < 0.85 for a in apdex):
                scores = [a.get("score", 1) for a in apdex if a.get("score") is not None]
                explicacoes.append(f"A entidade '{nome}' apresentou queda no índice de satisfação do usuário (Apdex médio: {sum(scores)/len(scores):.2f}).")
                recomendacoes_dev.append(f"Analise os endpoints de maior latência em '{nome}' e otimize o desempenho.")
                recomendacoes_gestor.append(f"Usuários podem estar insatisfeitos com a performance do serviço '{nome}'. Avalie a necessidade de melhorias.")
                impacto.append(f"Degradação de experiência para usuários do serviço '{nome}'.")
            # Análise de web vitals (exemplo)
            if web_vitals and isinstance(web_vitals, list):
                for vital in web_vitals:
                    if vital.get("lcp", 0) > 4:
                        explicacoes.append(f"LCP elevado em '{nome}' (LCP={vital.get('lcp'):.2f}s). Páginas lentas para o usuário final.")
                        recomendacoes_dev.append(f"Otimize imagens e scripts em '{nome}' para reduzir o LCP.")
                        impacto.append(f"Usuários podem perceber lentidão ao acessar '{nome}'.")
            # Análise de transações (exemplo)
            if transacoes and isinstance(transacoes, list):
                lentas = [t for t in transacoes if t.get("duration", 0) > 2]
                if lentas:
                    explicacoes.append(f"{len(lentas)} transações lentas detectadas em '{nome}'.")
                    recomendacoes_dev.append(f"Revise endpoints com duração >2s em '{nome}'.")
                    impacto.append(f"Possível aumento de tempo de resposta percebido por usuários de '{nome}'.")

    if not explicacoes:
        explicacoes.append("Nenhuma anomalia crítica detectada nas métricas disponíveis. Continue monitorando.")
        impacto.append("Sem impacto relevante detectado.")

    analise = {
        "incidente_id": incidente_id,
        "servico_afetado": incidente.get("impacted_service"),
        "severidade": incidente.get("severity"),
        "entidades_relacionadas": entidades_associadas,
        "explicacao_detalhada": "\n".join(explicacoes),
        "impacto_resumido": "\n".join(impacto),
        "recomendacoes_desenvolvedor": recomendacoes_dev,
        "recomendacoes_gestor": recomendacoes_gestor,
        "resumo_executivo": f"Incidente em '{incidente.get('impacted_service')}'. {explicacoes[0]}"
    }
    return analise

async def carregar_dados_do_disco():
    """Carrega dados de incidentes do disco se existirem"""
    try:
        if INCIDENTES_FILE.exists():
            with open(INCIDENTES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Atualiza dados globais
                dados_incidentes.update(data)
                logger.info(f"Dados carregados do disco: {len(dados_incidentes['incidentes'])} incidentes, {len(dados_incidentes['alertas'])} alertas")
        else:
            logger.warning(f"Arquivo de incidentes não encontrado: {INCIDENTES_FILE}")
    except Exception as e:
        logger.error(f"Erro ao carregar dados do disco: {str(e)}")

async def salvar_dados_no_disco():
    """Salva dados de incidentes no disco"""
    try:
        if not CACHE_DIR.exists():
            CACHE_DIR.mkdir(parents=True)
            
        with open(INCIDENTES_FILE, 'w', encoding='utf-8') as f:
            json.dump(dados_incidentes, f, indent=2, ensure_ascii=False)
            logger.info(f"Dados salvos no disco: {len(dados_incidentes['incidentes'])} incidentes, {len(dados_incidentes['alertas'])} alertas")
    except Exception as e:
        logger.error(f"Erro ao salvar dados no disco: {str(e)}")

def atualizar_resumo():
    """Atualiza o resumo de incidentes e alertas"""
    dados_incidentes["resumo"] = {
        "total_incidentes": len(dados_incidentes["incidentes"]),
        "total_alertas": len(dados_incidentes["alertas"]),
        "incidentes_ativos": sum(1 for i in dados_incidentes["incidentes"] if i.get("state") == "em_andamento"),
        "incidentes_resolvidos": sum(1 for i in dados_incidentes["incidentes"] if i.get("state") == "resolvido"),
        "severidade_critica": sum(1 for i in dados_incidentes["incidentes"] if i.get("severity") == "critical"),
        "severidade_warning": sum(1 for i in dados_incidentes["incidentes"] if i.get("severity") == "warning"),
        "severidade_info": sum(1 for i in dados_incidentes["incidentes"] if i.get("severity") == "info")
    }
    
def contar_entidades_por_dominio(entidades):
    """Conta entidades por domínio"""
    contagem = {}
    for entidade in entidades:
        dominio = entidade.get("domain", "desconhecido")
        if dominio not in contagem:
            contagem[dominio] = 0
        contagem[dominio] += 1
    return contagem

@app.on_event("startup")
async def inicializar():
    """Inicializa o aplicativo carregando dados e configurando tarefas de fundo"""
    logger.info("Inicializando API de Incidentes...")
    await carregar_dados_do_disco()
    await correlacionar_incidentes_entidades()
    atualizar_resumo()
    logger.info("Inicialização concluída")

@app.post("/adicionar-dados-exemplo")
async def adicionar_dados_exemplo():
    """
    Adiciona dados de exemplo para testes, utilizando nomes de entidades reais do New Relic
    """
    # Obtém entidades reais para usar nos exemplos
    entidades_reais = await carregar_entidades_newrelic()
    nomes_servicos = ["API de Pagamentos", "Portal do Cliente", "Backend de Processamento"]
    
    if entidades_reais:
        # Usa nomes de entidades reais se disponíveis
        nomes_servicos = [e.get("name") for e in entidades_reais[:5] if e.get("name")]
        if not nomes_servicos:  # Fallback
            nomes_servicos = ["API de Pagamentos", "Portal do Cliente", "Backend de Processamento"]
    
    # Data atual para cálculo de timestamps
    agora = datetime.now()
    
    # Cria dados de exemplo de incidentes
    incidentes_exemplo = [
        {
            "id": f"inc-{i+1}",
            "title": f"Incidente: Alerta de {tipo} em {servico}",
            "description": f"Detectado problema em Serviço de Autenticação no servidor {servidor}",
            "severity": severidade,
            "opened_at": (agora - timedelta(days=random.randint(0, 6), hours=random.randint(0, 12))).isoformat(),
            "state": "em_andamento",
            "impacted_service": servico
        } 
        for i, (tipo, servico, servidor, severidade) in enumerate([
            ("cpu_usage", nomes_servicos[0], "srv-prod-02", "warning"),
            ("apdex_violation", nomes_servicos[1], "srv-prod-01", "info"),
            ("error_percentage", nomes_servicos[2], "srv-prod-01", "info"),
        ])
    ]
    
    # Cria dados de exemplo de alertas
    alertas_exemplo = [
        {
            "id": f"alert-{i+1}-{int(agora.timestamp())}",
            "name": f"Alerta de {tipo} em {servico}",
            "description": f"Detectado problema em {problema} no servidor {servidor}",
            "severity": severidade,
            "timestamp": (agora - timedelta(days=dias, hours=horas)).isoformat(),
            "current_state": estado
        }
        for i, (tipo, servico, problema, servidor, severidade, dias, horas, estado) in enumerate([
            ("cpu_usage", nomes_servicos[0], "Serviço de Autenticação", "srv-prod-02", "warning", 2, 7, "active"),
            ("apdex_violation", nomes_servicos[1], "Serviço de Autenticação", "srv-prod-01", "info", 2, 3, "active"),
            ("error_percentage", nomes_servicos[2], "Serviço de Autenticação", "srv-prod-01", "info", 0, 10, "active"),
            ("apdex_violation", nomes_servicos[2], "Backend de Processamento", "srv-prod-02", "warning", 2, 17, "closed"),
            ("transaction_duration", nomes_servicos[1], "Portal do Cliente", "srv-app-01", "info", 4, 12, "active"),
            ("transaction_duration", nomes_servicos[2], "Serviço de Autenticação", "srv-prod-01", "info", 0, 6, "active"),
            ("cpu_usage", nomes_servicos[0], "Portal do Cliente", "srv-prod-01", "critical", 6, 9, "closed"),
        ])
    ]
    
    # Adiciona os exemplos aos dados em memória
    dados_incidentes["incidentes"] = incidentes_exemplo
    dados_incidentes["alertas"] = alertas_exemplo
    dados_incidentes["timestamp"] = agora.isoformat()
    
    # Atualiza resumo
    atualizar_resumo()
    
    # Salva no disco
    await salvar_dados_no_disco()
    
    # Correlaciona com entidades
    await correlacionar_incidentes_entidades()
    
    return {
        "status": "success",
        "message": "Dados de exemplo adicionados com sucesso",
        "alertas_adicionados": len(alertas_exemplo),
        "incidentes_adicionados": len(incidentes_exemplo)
    }

def simular_metricas_entidade(entidade):
    """
    Simula métricas detalhadas para uma entidade, incluindo erros, apdex, web vitals e transações.
    Use para testes e para enriquecer a análise de causa raiz.
    """
    import random
    # Simula erros
    erros = [{"timestamp": datetime.now().isoformat(), "count": random.randint(0, 5)} for _ in range(3)]
    # Simula apdex
    apdex = [{"timestamp": datetime.now().isoformat(), "score": round(random.uniform(0.7, 1.0), 2)} for _ in range(3)]
    # Simula web vitals
    web_vitals = [{"lcp": round(random.uniform(2, 6), 2)} for _ in range(2)]
    # Simula transações
    transactions = [{"endpoint": f"/api/{i}", "duration": round(random.uniform(0.5, 3.5), 2)} for i in range(3)]
    return {
        "recent_error": erros,
        "apdex": apdex,
        "web_vitals": web_vitals,
        "transactions": transactions
    }

if __name__ == "__main__":
    port = 8000
    print(f"Iniciando API de Incidentes na porta {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
