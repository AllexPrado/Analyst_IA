# Handler de lifespan para inicialização e finalização do app FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    logger.info("Inicializando API de Incidentes...")
    await carregar_dados_do_disco()
    await correlacionar_incidentes_entidades()
    atualizar_resumo()
    logger.info("Inicialização concluída")
    yield
    logger.info("Finalizando API de Incidentes...")
    await salvar_dados_no_disco()
# Função para correlacionar incidentes com entidades do New Relic
async def correlacionar_incidentes_entidades():
    entidades = await carregar_entidades_newrelic()
    if not entidades:
        logger.warning("Nenhuma entidade disponível para correlação")
        return
    mapa_entidades = {}
    for entidade in entidades:
        nome = entidade.get("name", "").lower()
        if nome:
            mapa_entidades[nome] = entidade
    dados_incidentes["entidades_associadas"] = {}
    for incidente in dados_incidentes["incidentes"]:
        servico = incidente.get("impacted_service", "").lower()
        entidade = None
        if servico in mapa_entidades:
            entidade = mapa_entidades[servico]
        else:
            for nome_entidade, ent in mapa_entidades.items():
                if servico in nome_entidade or nome_entidade in servico:
                    entidade = ent
                    break
            if not entidade and mapa_entidades:
                entidade = list(mapa_entidades.values())[0]
                logger.warning(f"Usando entidade fallback para {servico}")
        if not entidade:
            continue
        entidade_id = entidade.get("guid")
        if entidade_id:
            if incidente["id"] not in dados_incidentes["entidades_associadas"]:
                dados_incidentes["entidades_associadas"][incidente["id"]] = []
            dados_incidentes["entidades_associadas"][incidente["id"]].append(entidade)
    logger.info(f"Correlação concluída: {len(dados_incidentes.get('entidades_associadas', {}))} incidentes associados a entidades")
import os
import sys
from dotenv import load_dotenv
import aiohttp

# Função para carregar entidades do New Relic
async def carregar_entidades_newrelic():
    NEW_RELIC_API_KEY = os.getenv("NEW_RELIC_API_KEY")
    NEW_RELIC_ACCOUNT_ID = os.getenv("NEW_RELIC_ACCOUNT_ID")
    if not NEW_RELIC_API_KEY or not NEW_RELIC_ACCOUNT_ID:
        logger.warning("Credenciais do New Relic não configuradas. Usando apenas dados locais.")
        return []
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from coletor_new_relic import coletar_entidades
        entidades = await coletar_entidades(NEW_RELIC_API_KEY, NEW_RELIC_ACCOUNT_ID)
        logger.info(f"Coletadas {len(entidades)} entidades do New Relic")
        return entidades
    except Exception as e:
        logger.error(f"Erro ao coletar entidades do New Relic: {e}")
        return []

# Função para contar entidades por domínio
def contar_entidades_por_dominio(entidades):
    contagem = {}
    for entidade in entidades:
        dominio = entidade.get("domain", "desconhecido")
        if dominio not in contagem:
            contagem[dominio] = 0
        contagem[dominio] += 1
    return contagem
from typing import Dict, Any, List
from datetime import datetime
import logging
from pathlib import Path as PathlibPath
import json
import aiofiles

logger = logging.getLogger(__name__)

CACHE_DIR = PathlibPath("historico")
INCIDENTES_FILE = CACHE_DIR / "incidentes.json"
ENTIDADES_FILE = CACHE_DIR / "entidades_correlacionadas.json"

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
    "entidades_associadas": {}
}

async def carregar_dados_do_disco():
    try:
        if INCIDENTES_FILE.exists():
            with open(INCIDENTES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dados_incidentes.update(data)
                logger.info(f"Dados carregados do disco: {len(dados_incidentes['incidentes'])} incidentes, {len(dados_incidentes['alertas'])} alertas")
        else:
            logger.warning(f"Arquivo de incidentes não encontrado: {INCIDENTES_FILE}")
    except Exception as e:
        logger.error(f"Erro ao carregar dados do disco: {str(e)}")

async def salvar_dados_no_disco():
    try:
        if not CACHE_DIR.exists():
            CACHE_DIR.mkdir(parents=True)
        with open(INCIDENTES_FILE, 'w', encoding='utf-8') as f:
            json.dump(dados_incidentes, f, indent=2, ensure_ascii=False)
            logger.info(f"Dados salvos no disco: {len(dados_incidentes['incidentes'])} incidentes, {len(dados_incidentes['alertas'])} alertas")
    except Exception as e:
        logger.error(f"Erro ao salvar dados no disco: {str(e)}")

def atualizar_resumo():
    dados_incidentes["resumo"] = {
        "total_incidentes": len(dados_incidentes["incidentes"]),
        "total_alertas": len(dados_incidentes["alertas"]),
        "incidentes_ativos": sum(1 for i in dados_incidentes["incidentes"] if i.get("state") == "em_andamento"),
        "incidentes_resolvidos": sum(1 for i in dados_incidentes["incidentes"] if i.get("state") == "resolvido"),
        "severidade_critica": sum(1 for i in dados_incidentes["incidentes"] if i.get("severity") == "critical"),
        "severidade_warning": sum(1 for i in dados_incidentes["incidentes"] if i.get("severity") == "warning"),
        "severidade_info": sum(1 for i in dados_incidentes["incidentes"] if i.get("severity") == "info")
    }

def contar_entidades_por_dominio(entidades: List[Dict[str, Any]]):
    contagem = {}
    for entidade in entidades:
        dominio = entidade.get("domain", "desconhecido")
        if dominio not in contagem:
            contagem[dominio] = 0
        contagem[dominio] += 1
    return contagem
