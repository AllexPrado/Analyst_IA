from fastapi import APIRouter, HTTPException
from datetime import datetime
from models.incidentes import ChatRequestModel, ChatResponseModel
from utils.newrelic_advanced_collector import get_all_entities, get_entity_advanced_data
import aiohttp

router = APIRouter()

@router.post(
    "/chat",
    response_model=ChatResponseModel,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Endpoint de chat para integração com frontend",
    description="Endpoint de chat para integração com frontend. Recebe uma mensagem e retorna uma resposta baseada em dados reais do backend. Nunca retorna dados simulados.",
)
async def chat_api(request: ChatRequestModel):
    try:
        mensagem = request.mensagem
        if not mensagem:
            raise HTTPException(status_code=400, detail="Campo 'mensagem' é obrigatório.")
        async with aiohttp.ClientSession() as session:
            entidades = await get_all_entities(session)
            entidades_com_erros = []
            for entidade in entidades:
                dados_avancados = await get_entity_advanced_data(entidade, "24h", session=session)
                erros = dados_avancados.get("errors")
                if erros and isinstance(erros, list) and any(e.get("count", 0) > 0 for e in erros):
                    total_erros = sum(e.get("count", 0) for e in erros)
                    entidades_com_erros.append((entidade.get("name", "(sem nome)"), total_erros))
            if entidades_com_erros:
                entidades_com_erros.sort(key=lambda x: x[1], reverse=True)
                top_entidade, top_erros = entidades_com_erros[0]
                resposta = f"A entidade '{top_entidade}' apresentou o maior número de erros ({top_erros}) nas últimas 24h."
            else:
                resposta = "Nenhuma entidade apresentou erros nas últimas 24h."
        return ChatResponseModel(
            resposta=resposta,
            mensagem_recebida=mensagem,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no endpoint de chat: {e}")
