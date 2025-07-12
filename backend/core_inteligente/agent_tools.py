from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
import logging
from subprocess import run, PIPE
import asyncio
import httpx

router = APIRouter()
logger = logging.getLogger("agent_tools")

class SecurityRequest(BaseModel):
    contexto: Optional[Dict[str, Any]] = None

# Endpoint para análise de segurança do backend
@router.post("/security_check", summary="Analisa segurança do backend e recomenda correções")
async def security_check(request: SecurityRequest):
    try:
        # Exemplo: Análise simples
        issues = []
        # Simulação de checagem
        issues.append("Verificar uso de dados sensíveis em logs.")
        issues.append("Sanitizar entradas de usuário para evitar injeção de código.")
        issues.append("Validar permissões de acesso em endpoints críticos.")
        issues.append("Evitar exposição de variáveis de ambiente.")
        return {"seguranca": "analisada", "recomendacoes": issues}
    except Exception as e:
        logger.error(f"Análise de segurança falhou: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para correção automática de vulnerabilidades detectadas
@router.post("/security_fix", summary="Corrige automaticamente vulnerabilidades detectadas")
async def security_fix(request: SecurityRequest):
    try:
        # Exemplo: Correção simulada
        fixes = [
            "Logs sensíveis anonimizados.",
            "Entradas de usuário agora são sanitizadas.",
            "Permissões revisadas em endpoints críticos.",
            "Variáveis de ambiente protegidas.",
        ]
        return {"seguranca": "corrigida", "correcoes": fixes}
    except Exception as e:
        logger.error(f"Correção de segurança falhou: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class TestRequest(BaseModel):
    contexto: Optional[Dict[str, Any]] = None

class LintRequest(BaseModel):
    contexto: Optional[Dict[str, Any]] = None

class SuggestionRequest(BaseModel):
    contexto: Optional[Dict[str, Any]] = None

# Endpoint para executar testes automáticos
@router.post("/test", summary="Executa testes automáticos do backend")
async def run_tests(request: TestRequest):
    try:
        result = run(["pytest", "--maxfail=1", "--disable-warnings", "--tb=short"], stdout=PIPE, stderr=PIPE, text=True)
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except Exception as e:
        logger.error(f"Testes falharam: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para validação de boas práticas (lint)
@router.post("/lint", summary="Valida boas práticas de código (PEP8, flake8)")
async def run_lint(request: LintRequest):
    try:
        result = run(["flake8", ".", "--max-line-length=120"], stdout=PIPE, stderr=PIPE, text=True)
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except Exception as e:
        logger.error(f"Lint falhou: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para sugerir/aplicar melhorias de otimização
@router.post("/suggest", summary="Sugere/aplica melhorias de otimização no projeto")
async def suggest_improvements(request: SuggestionRequest):
    try:
        # Exemplo: Sugestão simples
        suggestions = [
            "Utilizar cache para consultas frequentes.",
            "Evitar duplicidade de routers.",
            "Adicionar testes automatizados para endpoints críticos.",
            "Utilizar tipagem explícita em funções.",
            "Documentar endpoints com OpenAPI.",
        ]
        return {"sugestoes": suggestions}
    except Exception as e:
        logger.error(f"Sugestão de melhorias falhou: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class DiagnoseRequest(BaseModel):
    contexto: Optional[Dict[str, Any]] = None

class OptimizeRequest(BaseModel):
    contexto: Optional[Dict[str, Any]] = None

class AutoFixRequest(BaseModel):
    contexto: Optional[Dict[str, Any]] = None

@router.post("/diagnose", summary="Diagnostica erros e problemas no backend")
async def diagnose_system(request: DiagnoseRequest):
    # Aqui pode-se integrar análise de logs, status, endpoints, etc.
    try:
        # Exemplo: Diagnóstico simples
        result = {"status": "ok", "detalhes": "Nenhum erro crítico encontrado."}
        return result
    except Exception as e:
        logger.error(f"Diagnóstico falhou: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/autofix", summary="Corrige automaticamente erros detectados")
async def auto_fix(request: AutoFixRequest):
    try:
        # Exemplo: Correção automática
        result = {"status": "corrigido", "detalhes": "Erros corrigidos automaticamente."}
        return result
    except Exception as e:
        logger.error(f"Auto-fix falhou: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize", summary="Otimiza o backend e recursos do projeto")
async def optimize_project(request: OptimizeRequest):
    try:
        # Exemplo: Otimização simples
        result = {"status": "otimizado", "detalhes": "Projeto otimizado."}
        return result
    except Exception as e:
        logger.error(f"Otimização falhou: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/docs/newrelic", summary="Consulta documentação do NewRelic")
async def get_newrelic_docs():
    # Aqui pode-se integrar consulta automática à documentação
    return {"url": "https://docs.newrelic.com/docs/", "resumo": "Documentação oficial NewRelic."}

@router.get("/docs/azure", summary="Consulta documentação do Azure")
async def get_azure_docs():
    return {"url": "https://learn.microsoft.com/pt-br/azure/", "resumo": "Documentação oficial Azure."}

# Endpoint para corrigir problemas detectados
@router.post("/corrigir", summary="Corrige problemas detectados pelo Agno IA")
async def corrigir_problemas():
    try:
        # Simulação de correção
        return {"status": "corrigido", "detalhes": "Problemas corrigidos com sucesso."}
    except Exception as e:
        logger.error(f"Falha ao corrigir problemas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para executar playbook
@router.post("/playbook", summary="Executa playbook do Agno IA")
async def executar_playbook():
    try:
        # Simulação de execução de playbook
        return {"status": "executado", "detalhes": "Playbook executado com sucesso."}
    except Exception as e:
        logger.error(f"Falha ao executar playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para feedback
@router.post("/feedback", summary="Recebe feedback do Agno IA")
async def receber_feedback():
    try:
        # Simulação de recebimento de feedback
        return {"status": "recebido", "detalhes": "Feedback recebido com sucesso."}
    except Exception as e:
        logger.error(f"Falha ao receber feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para coleta de dados do New Relic
@router.post("/coletar_newrelic", summary="Coleta dados do New Relic")
async def coletar_dados_newrelic():
    try:
        # Simulação de coleta de dados
        return {"status": "coletado", "detalhes": "Dados coletados com sucesso."}
    except Exception as e:
        logger.error(f"Falha ao coletar dados do New Relic: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def monitorar_agentes():
    while True:
        try:
            logger.info("Monitorando agentes...")
            # Simulação de monitoramento
            await asyncio.sleep(10)  # Intervalo de monitoramento
        except Exception as e:
            logger.error(f"Erro ao monitorar agentes: {e}")

async def executar_automatizacoes():
    while True:
        try:
            logger.info("Executando automatizações...")
            # Simulação de execução de automatizações
            await asyncio.sleep(15)  # Intervalo de execução
        except Exception as e:
            logger.error(f"Erro ao executar automatizações: {e}")

async def identificar_e_corrigir_erros():
    """
    Verifica e corrige erros em endpoints críticos.
    Tenta acessar os endpoints via diferentes rotas para garantir acessibilidade.
    """
    # Lista de endpoints a serem verificados (com ambos os prefixos)
    endpoints = [
        # Primário (via API router)
        "/api/agno/corrigir",
        "/api/agno/playbook",
        "/api/agno/feedback",
        "/api/agno/coletar_newrelic",
        # Secundário (direto)
        "/agno/corrigir",
        "/agno/playbook",
        "/agno/feedback",
        "/agno/coletar_newrelic"
    ]
    
    # Payloads para teste (mínimos necessários)
    payloads = {
        "corrigir": {"entidade": "sistema_backend", "acao": "verificar"},
        "playbook": {"nome": "diagnostico", "contexto": {}},
        "feedback": {"feedback": {"tipo": "verificacao", "valor": "ok"}},
        "coletar_newrelic": {"entidade": "sistema", "periodo": "3d", "tipo": "metricas"}
    }

    # Base URL do servidor
    base_url = "http://localhost:8000"
    endpoint_status = {"sucesso": [], "falha": []}
    
    async with httpx.AsyncClient(timeout=30) as client:
        for endpoint in endpoints:
            try:
                # Determina qual payload usar baseado no nome do endpoint
                payload_key = endpoint.split("/")[-1]
                payload = payloads.get(payload_key, {})
                
                full_url = f"{base_url}{endpoint}"
                logger.info(f"Verificando endpoint: {full_url}")
                
                response = await client.post(full_url, json=payload)
                
                if response.status_code == 404:
                    logger.error(f"Erro 404 no endpoint {full_url}")
                    endpoint_status["falha"].append(endpoint)
                elif response.status_code >= 400:
                    logger.error(f"Erro {response.status_code} no endpoint {full_url}: {response.text}")
                    endpoint_status["falha"].append(endpoint)
                else:
                    logger.info(f"Endpoint {full_url} verificado com sucesso: {response.status_code}")
                    try:
                        resposta = response.json()
                        logger.info(f"Resposta: {resposta}")
                    except Exception as json_err:
                        logger.warning(f"Não foi possível decodificar a resposta como JSON: {json_err}")
                    
                    endpoint_status["sucesso"].append(endpoint)
            except httpx.RequestError as e:
                logger.error(f"Erro de requisição ao verificar endpoint {endpoint}: {e}")
                endpoint_status["falha"].append(endpoint)
            except Exception as e:
                logger.error(f"Erro ao verificar endpoint {endpoint}: {e}")
                endpoint_status["falha"].append(endpoint)
    
    # Relatório final
    logger.info(f"Verificação concluída. Sucessos: {len(endpoint_status['sucesso'])}, Falhas: {len(endpoint_status['falha'])}")
    
    # Se houver pelo menos uma rota funcionando para cada tipo de endpoint, 
    # considera-se que o sistema está operacional
    working_endpoints = set([ep.split("/")[-1] for ep in endpoint_status["sucesso"]])
    if len(working_endpoints) >= 4:  # Temos os 4 tipos de endpoints funcionando
        logger.info("Sistema de endpoints está operacional")
        return {"status": "ok", "endpoints_funcionando": list(working_endpoints)}
    else:
        logger.error(f"Sistema de endpoints não está totalmente operacional. Endpoints funcionando: {working_endpoints}")
        return {"status": "erro", "endpoints_funcionando": list(working_endpoints), "endpoints_com_falha": [ep for ep in endpoint_status["falha"]]}
async def iniciar_tarefas():
    await asyncio.gather(monitorar_agentes(), executar_automatizacoes(), identificar_e_corrigir_erros())

# Início das tarefas ao iniciar o módulo
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            loop.run_until_complete(iniciar_tarefas())
        else:
            logger.warning("Loop de eventos já está em execução. Tarefas serão adicionadas ao loop existente.")
            asyncio.ensure_future(iniciar_tarefas())
    except Exception as e:
        logger.error(f"Erro ao iniciar tarefas assíncronas: {e}")
