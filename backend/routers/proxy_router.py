"""
Proxy router to ensure endpoints are accessible through multiple paths.
This router fixes issues with endpoints that might be registered under
different prefixes by creating proxy endpoints.
"""
from fastapi import APIRouter, Request, Depends, HTTPException
import logging
from typing import Dict, Any, Callable, Optional
import httpx
import asyncio

logger = logging.getLogger(__name__)

# Create the router
proxy_router = APIRouter()

async def proxy_request(
    request: Request,
    target_path: str,
    timeout: float = 30.0,
    add_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Proxy a request to another endpoint in the same application.
    
    Args:
        request: The incoming request
        target_path: The target path to proxy to (e.g., "/api/agno/corrigir")
        timeout: Request timeout in seconds
        add_prefix: Optional prefix to add to the target_path
    
    Returns:
        The response from the proxied endpoint
    """
    # Get request body
    body = await request.json() if request.method != "GET" else {}
    
    # Construct the full URL
    base_url = str(request.base_url).rstrip("/")
    if add_prefix:
        if not add_prefix.startswith("/"):
            add_prefix = "/" + add_prefix
        target_path = f"{add_prefix}{target_path}"
    
    target_url = f"{base_url}{target_path}"
    
    logger.info(f"Proxying request from {request.url.path} to {target_url}")
    
    # Forward the request
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if request.method == "GET":
                response = await client.get(target_url)
            else:
                response = await client.post(target_url, json=body)
            
            if response.status_code >= 400:
                logger.warning(f"Proxy request to {target_url} failed with status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Proxy request failed: {response.text}"
                )
            
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Proxy request to {target_url} failed with error: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Proxy request failed: {str(e)}"
            )

# Create proxy endpoints for the agno router
# This ensures that both /agno/... and /api/agno/... will work

@proxy_router.post("/agno/corrigir")
async def proxy_corrigir(request: Request):
    """Proxy to /api/agno/corrigir"""
    logger.info("Recebida requisição em /agno/corrigir - redirecionando para /api/agno/corrigir")
    return await proxy_request(request, "/api/agno/corrigir")

@proxy_router.post("/agno/playbook")
async def proxy_playbook(request: Request):
    """Proxy to /api/agno/playbook"""
    logger.info("Recebida requisição em /agno/playbook - redirecionando para /api/agno/playbook")
    return await proxy_request(request, "/api/agno/playbook")

@proxy_router.post("/agno/feedback")
async def proxy_feedback(request: Request):
    """Proxy to /api/agno/feedback"""
    logger.info("Recebida requisição em /agno/feedback - redirecionando para /api/agno/feedback")
    return await proxy_request(request, "/api/agno/feedback")

@proxy_router.post("/agno/coletar_newrelic")
async def proxy_coletar_newrelic(request: Request):
    """Proxy to /api/agno/coletar_newrelic"""
    logger.info("Recebida requisição em /agno/coletar_newrelic - redirecionando para /api/agno/coletar_newrelic")
    return await proxy_request(request, "/api/agno/coletar_newrelic")

# Also add the reverse direction for completeness
@proxy_router.post("/api/agno/corrigir")
async def proxy_api_corrigir(request: Request):
    """Proxy to /agno/corrigir"""
    return await proxy_request(request, "/agno/corrigir")

@proxy_router.post("/api/agno/playbook")
async def proxy_api_playbook(request: Request):
    """Proxy to /agno/playbook"""
    return await proxy_request(request, "/agno/playbook")

@proxy_router.post("/api/agno/feedback")
async def proxy_api_feedback(request: Request):
    """Proxy to /agno/feedback"""
    return await proxy_request(request, "/agno/feedback")

@proxy_router.post("/api/agno/coletar_newrelic")
async def proxy_api_coletar_newrelic(request: Request):
    """Proxy to /agno/coletar_newrelic"""
    return await proxy_request(request, "/agno/coletar_newrelic")
