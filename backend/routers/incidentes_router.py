from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime
from models.incidentes import *
from services.incidentes_service import dados_incidentes, atualizar_resumo, carregar_dados_do_disco, contar_entidades_por_dominio
from utils.newrelic_advanced_collector import get_all_entities, get_entity_advanced_data
import aiohttp
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Endpoint utilitário para testes automatizados
@router.post("/adicionar-dados-exemplo", tags=["Util"], summary="Adiciona dados de exemplo para testes", include_in_schema=True)
async def adicionar_dados_exemplo():
    """
    Adiciona dados de exemplo para testes automatizados.
    """
    from datetime import timedelta
    import random
    agora = datetime.now()
    nomes_servicos = ["API de Pagamentos", "Portal do Cliente", "Backend de Processamento"]
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
    dados_incidentes["incidentes"] = incidentes_exemplo
    dados_incidentes["alertas"] = alertas_exemplo
    dados_incidentes["timestamp"] = agora.isoformat()
    atualizar_resumo()
    return {
        "status": "success",
        "message": "Dados de exemplo adicionados com sucesso",
        "alertas_adicionados": len(alertas_exemplo),
        "incidentes_adicionados": len(incidentes_exemplo),
        "explicacao": "Endpoint utilitário para inserir dados de exemplo e facilitar testes automatizados do frontend.",
        "sugestao": "Utilize este endpoint apenas em ambientes de desenvolvimento ou homologação.",
        "proximos_passos": "Após adicionar os dados, utilize os endpoints principais para validar as integrações e fluxos do frontend."
    }

@router.get(
    "/incidentes",
    response_model=IncidentesResponseModel,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Lista todos os incidentes com dados avançados reais",
    description="Lista todos os incidentes com dados avançados reais de cada entidade relacionada. Sempre retorna dados reais, nunca simulados.",
    status_code=status.HTTP_200_OK
)
async def listar_incidentes():
    await carregar_dados_do_disco()
    atualizar_resumo()
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
                        entidades_rel.append(EntidadeModel(guid=guid, entidade=entidade, dados_avancados=dados_avancados))
                incidente_c = IncidenteModel(**{**incidente, "entidades_dados_avancados": entidades_rel})
                incidentes_avancados.append(incidente_c)
            return IncidentesResponseModel(
                incidentes=incidentes_avancados,
                alertas=dados_incidentes["alertas"],
                timestamp=datetime.now().isoformat(),
                resumo=dados_incidentes["resumo"],
                explicacao="Esta lista apresenta todos os incidentes detectados, enriquecidos com dados avançados coletados do New Relic para cada entidade relacionada.",
                sugestao="Analise os incidentes com maior severidade e verifique as entidades mais impactadas para priorizar ações.",
                proximos_passos="Clique em um incidente para visualizar detalhes, causas e recomendações específicas. Utilize filtros para refinar sua análise."
            )
    except Exception as e:
        logger.error(f"Erro ao coletar dados avançados para incidentes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao coletar dados avançados para incidentes: {e}")
