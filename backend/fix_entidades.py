import os
import sys
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uvicorn
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicativo FastAPI
app = FastAPI(
    title="Corrigindo Entidades no Backend",
    description="Script para corrigir o carregamento de entidades do New Relic"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from utils.newrelic_collector import coletar_contexto_completo
from utils.cache import forcar_atualizacao_cache, get_cache, atualizar_cache_completo, _cache, salvar_cache_no_disco

@app.get("/")
async def root():
    return {"message": "API para corrigir entidades está rodando!"}

@app.get("/entidades-teste")
async def get_entidades_teste():
    """Endpoint para testar o carregamento de entidades do New Relic"""
    try:
        # Coletar contexto completo direto do New Relic
        contexto = await coletar_contexto_completo()
        
        # O coletar_contexto_completo retorna entidades por domínio, não uma lista única
        # Vamos consolidar todas as entidades de todos os domínios
        entidades = []
        dominios_para_verificar = ['apm', 'browser', 'infra', 'db', 'mobile', 'iot', 'serverless', 'synth', 'ext']
        
        for dominio in dominios_para_verificar:
            if dominio in contexto and contexto[dominio]:
                for entidade in contexto[dominio]:
                    entidades.append(entidade)
        
        # Contar entidades por domínio
        dominios = {}
        for entidade in entidades:
            domain = entidade.get("domain", "UNKNOWN")
            if domain not in dominios:
                dominios[domain] = 0
            dominios[domain] += 1
        
        # Retornar informações
        return {
            "total_entidades": len(entidades),
            "entidades_por_dominio": dominios,
            "primeiras_entidades": entidades[:10] if entidades else []
        }
    except Exception as e:
        logger.error(f"Erro ao obter entidades: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter entidades: {str(e)}")

@app.post("/atualizar-cache")
async def atualizar_cache():
    """Endpoint para forçar a atualização do cache do New Relic"""
    try:
        # Forçar atualização do cache
        sucesso = await forcar_atualizacao_cache(coletar_contexto_completo)
        
        # Se a atualização foi bem-sucedida, processar e consolidar entidades
        if sucesso:
            # Obter cache atualizado
            cache = await get_cache()
            
            # Consolidar entidades de todos os domínios
            entidades = []
            dominios_para_verificar = ['apm', 'browser', 'infra', 'db', 'mobile', 'iot', 'serverless', 'synth', 'ext']
            
            for dominio in dominios_para_verificar:
                if dominio in cache and isinstance(cache[dominio], list):
                    for entidade in cache[dominio]:
                        # Adicionar à lista consolidada apenas se tiver guid (evitar duplicatas)
                        guid = entidade.get("guid")
                        if guid and not any(e.get("guid") == guid for e in entidades):
                            entidades.append(entidade)
            
            # Contagem por domínio
            dominios_info = {}
            for entidade in entidades:
                domain = entidade.get("domain", "UNKNOWN")
                if domain not in dominios_info:
                    dominios_info[domain] = 0
                dominios_info[domain] += 1
            
            # Adicionar lista consolidada ao cache para facilitar acesso no futuro
            cache["entidades"] = entidades
            
            # Atualizar o cache completo com as entidades consolidadas
            await atualizar_cache_completo(cache)
            
            return {
                "status": "success",
                "message": "Cache atualizado e entidades consolidadas com sucesso",
                "total_entidades": len(entidades),
                "dominios_disponiveis": list(dominios_info.keys()),
                "entidades_por_dominio": dominios_info
            }
        else:
            return {"status": "error", "message": "Falha ao atualizar cache"}
    except Exception as e:
        logger.error(f"Erro ao atualizar cache: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar cache: {str(e)}")

@app.get("/incidentes")
async def get_incidentes():
    """Endpoint para retornar incidentes e alertas do cache"""
    try:
        cache = await get_cache()
        
        # Obter incidentes e alertas do cache
        incidentes = cache.get("incidentes", [])
        alertas = cache.get("alertas", [])
        
        # Formatar para retornar ao frontend
        resultado = {
            "incidentes": incidentes,
            "alertas": alertas,
            "timestamp": datetime.now().isoformat(),
            "resumo": {
                "total_incidentes": len(incidentes),
                "total_alertas": len(alertas),
                "incidentes_ativos": sum(1 for i in incidentes if i.get("state") == "em_andamento"),
                "incidentes_resolvidos": sum(1 for i in incidentes if i.get("state") == "resolvido"),
                "severidade_critica": sum(1 for i in incidentes if i.get("severity") == "critical"),
                "severidade_warning": sum(1 for i in incidentes if i.get("severity") == "warning"),
                "severidade_info": sum(1 for i in incidentes if i.get("severity") == "info")
            }
        }
        
        return resultado
    except Exception as e:
        logger.error(f"Erro ao obter incidentes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter incidentes: {str(e)}")

@app.post("/adicionar-dados-exemplo")
async def adicionar_dados_exemplo():
    """Endpoint para adicionar dados de exemplo ao cache (alertas e incidentes)"""
    try:
        # Obter cache atual
        cache = await get_cache()
        
        # Gerar alertas de exemplo (3-8)
        import random
        from datetime import timedelta
        
        num_alertas = random.randint(3, 8)
        alertas = []
        agora = datetime.now()
        
        # Dados de exemplo
        aplicacoes = ["API de Pagamentos", "Portal do Cliente", "Serviço de Autenticação", "Backend de Processamento"]
        servidores = ["srv-prod-01", "srv-prod-02", "srv-app-01", "db-cluster-01"]
        severidades = ["critical", "warning", "info"]
        tipos = ["transaction_duration", "apdex_violation", "error_percentage", "memory_usage", "cpu_usage"]
        
        # Gerar alertas
        for i in range(num_alertas):
            # Timestamp aleatório nos últimos 7 dias
            horas_atras = random.randint(1, 168)  # 7 dias = 168 horas
            timestamp = agora - timedelta(hours=horas_atras)
            
            alerta = {
                "id": f"alert-{i+1}-{int(timestamp.timestamp())}",
                "name": f"Alerta de {random.choice(tipos)} em {random.choice(aplicacoes)}",
                "description": f"Detectado problema em {random.choice(aplicacoes)} no servidor {random.choice(servidores)}",
                "severity": random.choice(severidades),
                "timestamp": timestamp.isoformat(),
                "current_state": "active" if random.random() < 0.7 else "closed"
            }
            
            alertas.append(alerta)
        
        # Gerar incidentes baseados em alertas (1-3)
        num_incidentes = min(num_alertas, 3)
        incidentes = []
        
        for i in range(num_incidentes):
            alerta = alertas[i]
            timestamp = datetime.fromisoformat(alerta["timestamp"])
            
            # Status aleatório
            status = "em_andamento" if random.random() < 0.7 else "resolvido"
            
            incidente = {
                "id": f"inc-{i+1}",
                "title": f"Incidente: {alerta['name']}",
                "alert_id": alerta["id"],
                "state": status,
                "severity": alerta["severity"],
                "timestamp": timestamp.isoformat(),
                "description": alerta["description"]
            }
            incidentes.append(incidente)

        # Atualizar cache
        cache["alertas"] = alertas
        cache["incidentes"] = incidentes
        await atualizar_cache_completo(cache)

        return {
            "status": "success",
            "message": "Dados de exemplo adicionados ao cache",
            "total_alertas": len(alertas),
            "total_incidentes": len(incidentes)
        }
    except Exception as e:
        logger.error(f"Erro ao adicionar dados de exemplo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar dados de exemplo: {str(e)}")
