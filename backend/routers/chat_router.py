
from fastapi import APIRouter, HTTPException
from datetime import datetime
from models.incidentes import ChatRequestModel, ChatResponseModel
from core_inteligente.agno_agent import responder_chat

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
    import logging
    logger = logging.getLogger("chat_router")
    try:
        mensagem = request.mensagem
        if not mensagem:
            logger.error("Campo 'mensagem' ausente no request.")
            raise HTTPException(status_code=400, detail="Campo 'mensagem' é obrigatório.")
        resposta_agno = responder_chat(mensagem, session_id=None)
        logger.info(f"Resposta Agno: {resposta_agno}")
        if isinstance(resposta_agno, dict):
            resposta = resposta_agno.get("resposta") or resposta_agno.get("content") or str(resposta_agno)
            sugestao = resposta_agno.get("sugestao", "")
            proximos_passos = resposta_agno.get("proximos_passos", "")
            explicacao = resposta_agno.get("explicacao", "Resposta gerada pelo agente Agno.")
        else:
            resposta = str(resposta_agno)
            sugestao = ""
            proximos_passos = ""
            explicacao = "Resposta gerada pelo agente Agno."
        # Garante que todos os campos obrigatórios estão presentes
        if not resposta:
            logger.error(f"Resposta vazia do agente para mensagem: {mensagem}")
            resposta = "Não foi possível gerar uma resposta para sua mensagem."
        return ChatResponseModel(
            resposta=resposta,
            mensagem_recebida=mensagem,
            timestamp=datetime.now().isoformat(),
            explicacao=explicacao,
            sugestao=sugestao,
            proximos_passos=proximos_passos
        )
    except Exception as e:
        logger.exception(f"Erro no endpoint de chat (Agno): {e}")
        raise HTTPException(status_code=500, detail=f"Erro no endpoint de chat (Agno): {e}")
