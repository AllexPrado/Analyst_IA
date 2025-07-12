"""
Simple script to create a proxy router without modifying any existing files.
This will ensure endpoints are accessible through both /agno/ and /api/agno/ paths.
"""
from pathlib import Path

def create_proxy_router():
    proxy_router_content = '''"""
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
    return await proxy_request(request, "/api/agno/corrigir")

@proxy_router.post("/agno/playbook")
async def proxy_playbook(request: Request):
    """Proxy to /api/agno/playbook"""
    return await proxy_request(request, "/api/agno/playbook")

@proxy_router.post("/agno/feedback")
async def proxy_feedback(request: Request):
    """Proxy to /api/agno/feedback"""
    return await proxy_request(request, "/api/agno/feedback")

@proxy_router.post("/agno/coletar_newrelic")
async def proxy_coletar_newrelic(request: Request):
    """Proxy to /api/agno/coletar_newrelic"""
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
'''
    
    # Write the proxy router file
    proxy_router_path = Path("d:/projetos/Analyst_IA/backend/routers/proxy_router.py")
    with open(proxy_router_path, "w") as f:
        f.write(proxy_router_content)
    print(f"Created proxy router at {proxy_router_path}")

if __name__ == "__main__":
    create_proxy_router()
    print("To use this proxy router, add the following code to your core_router.py:")
    print("=" * 50)
    print("try:")
    print("    from routers.proxy_router import proxy_router")
    print("    api_router.include_router(proxy_router)")
    print("    logger.info(\"Router de proxy incluído com sucesso para garantir acesso às rotas /agno e /api/agno\")")
    print("except ImportError as e:")
    print("    logger.error(f\"Erro ao importar proxy_router: {e}\")")
    print("=" * 50)
    print("Then restart your FastAPI application.")
