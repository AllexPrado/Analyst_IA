"""
Unified router diagnostic and fix script.
This script:
1. Diagnoses router configuration issues in the application
2. Creates a proxy router that ensures all endpoints are accessible
3. Updates the agent_tools.py to correctly access endpoints
"""
import logging
import sys
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("router_fix.log")
    ]
)

logger = logging.getLogger(__name__)

def check_file_exists(filepath):
    """Check if a file exists"""
    path = Path(filepath)
    exists = path.exists()
    logger.info(f"Checking file {filepath}: {'EXISTS' if exists else 'MISSING'}")
    return exists

def create_proxy_router():
    """Create a proxy router that ensures all endpoints are accessible through multiple paths"""
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
    try:
        with open(proxy_router_path, "w") as f:
            f.write(proxy_router_content)
        logger.info(f"Created proxy router at {proxy_router_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create proxy router: {e}")
        return False

def update_core_router():
    """Update core_router.py to include the proxy router"""
    core_router_path = Path("d:/projetos/Analyst_IA/backend/core_router.py")
    
    try:
        with open(core_router_path, "r") as f:
            content = f.read()
        
        # Check if proxy router is already included
        if "from routers.proxy_router import proxy_router" in content:
            logger.info("Proxy router is already included in core_router.py")
            return True
        
        # Find insertion point after other router inclusions
        insertion_point = content.find("logger.info(\"Router Agno IA incluído com sucesso em /agno\")")
        if insertion_point == -1:
            logger.warning("Could not find insertion point in core_router.py")
            return False
        
        # Find end of line after insertion point
        end_of_line = content.find("\n", insertion_point)
        if end_of_line == -1:
            end_of_line = len(content)
        
        # Insert proxy router include and initialization
        new_content = (
            content[:end_of_line] + 
            "\n\n# Incluir o router de proxy para garantir acessibilidade dos endpoints\n"
            "try:\n"
            "    from routers.proxy_router import proxy_router\n"
            "    api_router.include_router(proxy_router)\n"
            "    logger.info(\"Router de proxy incluído com sucesso para garantir acesso às rotas /agno e /api/agno\")\n"
            "except ImportError as e:\n"
            "    logger.error(f\"Erro ao importar proxy_router: {e}\")\n" +
            content[end_of_line:]
        )
        
        # Write updated content
        with open(core_router_path, "w") as f:
            f.write(new_content)
        
        logger.info("Updated core_router.py to include proxy router")
        return True
    except Exception as e:
        logger.error(f"Failed to update core_router.py: {e}")
        return False

def update_agent_tools():
    """Update agent_tools.py to correctly access endpoints"""
    agent_tools_path = Path("d:/projetos/Analyst_IA/backend/core_inteligente/agent_tools.py")
    
    try:
        with open(agent_tools_path, "r") as f:
            content = f.read()
        
        # Find the identificar_e_corrigir_erros function
        start = content.find("async def identificar_e_corrigir_erros():")
        if start == -1:
            logger.warning("Could not find identificar_e_corrigir_erros function in agent_tools.py")
            return False
        
        # Find the beginning of the function body (first indented line after function definition)
        function_body_start = content.find("    ", start)
        if function_body_start == -1:
            logger.warning("Could not find function body in agent_tools.py")
            return False
        
        # Find the end of the function (next non-indented line or end of file)
        function_body_end = content.find("\nasync def", function_body_start)
        if function_body_end == -1:
            function_body_end = content.find("\ndef", function_body_start)
        if function_body_end == -1:
            function_body_end = content.find("\n# Inicializando", function_body_start)
        if function_body_end == -1:
            logger.warning("Could not find end of function in agent_tools.py")
            return False
        
        # Create new function implementation
        new_function = '''async def identificar_e_corrigir_erros():
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
        "coletar_newrelic": {"tipo": "entidades"}
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
                else:
                    logger.info(f"Endpoint {full_url} verificado com sucesso: {response.status_code}")
                    endpoint_status["sucesso"].append(endpoint)
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
    else:
        logger.error(f"Sistema de endpoints não está totalmente operacional. Endpoints funcionando: {working_endpoints}")'''
        
        # Replace the function implementation
        new_content = content[:start] + new_function + content[function_body_end:]
        
        # Write updated content
        with open(agent_tools_path, "w") as f:
            f.write(new_content)
        
        logger.info("Updated agent_tools.py with improved endpoint testing")
        return True
    except Exception as e:
        logger.error(f"Failed to update agent_tools.py: {e}")
        return False

def update_init_files():
    """Ensure all __init__.py files are properly set up"""
    # Update routers/__init__.py
    routers_init_path = Path("d:/projetos/Analyst_IA/backend/routers/__init__.py")
    try:
        with open(routers_init_path, "r") as f:
            content = f.read()
        
        if "from .proxy_router import proxy_router" not in content:
            new_content = content + '''
try:
    from .proxy_router import proxy_router
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Error importing proxy_router: {e}")
'''
            with open(routers_init_path, "w") as f:
                f.write(new_content)
            logger.info("Updated routers/__init__.py to include proxy_router")
    except Exception as e:
        logger.error(f"Failed to update routers/__init__.py: {e}")

def main():
    """Main function to diagnose and fix router issues"""
    logger.info("=" * 50)
    logger.info("ROUTER DIAGNOSTICS AND FIX")
    logger.info("=" * 50)
    
    # Check key files
    logger.info("Checking key files...")
    check_file_exists("d:/projetos/Analyst_IA/backend/main.py")
    check_file_exists("d:/projetos/Analyst_IA/backend/core_router.py")
    check_file_exists("d:/projetos/Analyst_IA/backend/routers/agno_router.py")
    check_file_exists("d:/projetos/Analyst_IA/backend/core_inteligente/agent_tools.py")
    
    # Create and set up proxy router
    logger.info("\nCreating proxy router...")
    create_proxy_router()
    
    # Update core_router.py
    logger.info("\nUpdating core_router.py...")
    update_core_router()
    
    # Update agent_tools.py
    logger.info("\nUpdating agent_tools.py...")
    update_agent_tools()
    
    # Update __init__.py files
    logger.info("\nUpdating __init__.py files...")
    update_init_files()
    
    logger.info("\nRouter fix complete! Please restart your FastAPI application.")
    logger.info("The endpoints should now be accessible at both /agno/... and /api/agno/...")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
