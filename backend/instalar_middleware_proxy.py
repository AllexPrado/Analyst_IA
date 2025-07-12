"""
Implementação de um middleware para FastAPI que redireciona requisições
de /agno para /api/agno.

Deve ser executado antes do servidor ser iniciado, para garantir que
todos os endpoints estejam acessíveis por ambos os caminhos.
"""

import logging
import os
import sys
from pathlib import Path

# Configurar o logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("proxy_middleware")

def adicionar_middleware_proxy():
    """
    Adiciona um middleware ao arquivo unified_backend.py para
    redirecionar requisições /agno/* para /api/agno/*.
    """
    unified_backend_path = Path("unified_backend.py")
    if not unified_backend_path.exists():
        logger.error(f"Arquivo {unified_backend_path} não encontrado!")
        return False
    
    # Ler o conteúdo atual
    with open(unified_backend_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verificar se o middleware já foi adicionado
    if "class AgnoProxyMiddleware" in content:
        logger.info("Middleware de proxy já está presente no arquivo.")
        return True
    
    # Encontrar o ponto de inserção (após a configuração CORS)
    cors_config = "app.add_middleware(\n    CORSMiddleware,"
    if cors_config not in content:
        logger.error("Não foi possível encontrar o ponto de inserção para o middleware.")
        return False
    
    # Código do middleware a ser adicionado
    middleware_code = """
# Middleware para redirecionar /agno para /api/agno
class AgnoProxyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith("/agno/"):
            # Redireciona /agno/* para /api/agno/*
            original_path = scope["path"]
            new_path = "/api" + original_path
            logger.info(f"Redirecionando solicitação de {original_path} para {new_path}")
            
            # Modificar o caminho na scope
            scope["path"] = new_path
            
            # Adicionar um cabeçalho X-Redirected-From para rastreamento
            if "headers" in scope:
                scope["headers"].append(
                    (b"x-redirected-from", original_path.encode())
                )
        
        await self.app(scope, receive, send)

# Adicionar o middleware de proxy antes de qualquer outro processamento
app.add_middleware(AgnoProxyMiddleware)
"""
    
    # Inserir o middleware após a configuração CORS
    split_point = content.find(cors_config)
    cors_block_end = content.find(")", split_point)
    
    if cors_block_end == -1:
        logger.error("Não foi possível encontrar o final do bloco CORS.")
        return False
    
    new_content = content[:cors_block_end+1] + middleware_code + content[cors_block_end+1:]
    
    # Fazer backup do arquivo original
    backup_path = unified_backend_path.with_suffix(".py.bak")
    if not backup_path.exists():
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Backup criado em {backup_path}")
    
    # Salvar o arquivo modificado
    with open(unified_backend_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    logger.info(f"Middleware de proxy adicionado com sucesso ao {unified_backend_path}")
    return True

if __name__ == "__main__":
    print("=" * 80)
    print("INSTALAÇÃO DO MIDDLEWARE DE PROXY PARA ENDPOINTS /agno")
    print("=" * 80)
    
    if adicionar_middleware_proxy():
        print("\nMiddleware instalado com sucesso!")
        print("Agora reinicie o servidor para aplicar as alterações.")
        print("\nPara reiniciar o servidor, execute:")
        print("python reiniciar_e_testar_agno.py")
    else:
        print("\nFalha ao instalar middleware!")
        print("Verifique os logs para mais informações.")
        sys.exit(1)
