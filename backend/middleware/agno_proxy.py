"""
Middleware para redirecionar requisições /agno para /api/agno
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI
import logging

logger = logging.getLogger("agno_middleware")

class AgnoProxyMiddleware(BaseHTTPMiddleware):
    """
    Middleware para redirecionar requisições /agno para /api/agno
    """
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Se o caminho começar com /agno/, redireciona para /api/agno/
        if path.startswith("/agno/"):
            # Construir nova URL com prefixo /api
            new_path = "/api" + path
            logger.info(f"[AGNO_MIDDLEWARE] Redirecionando {path} para {new_path}")
            
            # Modificar o escopo da requisição para o novo caminho
            request.scope["path"] = new_path
            # Atualizar a URL na requisição
            raw_path = request.scope["path"].encode("utf-8")
            request.scope["raw_path"] = raw_path
        
        # Continuar com o próximo middleware ou rota
        return await call_next(request)

def add_agno_middleware(app: FastAPI):
    """
    Adiciona o middleware de redirecionamento Agno à aplicação FastAPI
    """
    app.add_middleware(AgnoProxyMiddleware)
    logger.info("[AGNO_MIDDLEWARE] Middleware de redirecionamento Agno adicionado")
    return app
