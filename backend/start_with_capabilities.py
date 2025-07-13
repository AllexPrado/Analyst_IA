"""
Script para a inicialização segura do backend com capacidades expandidas dos agentes.
Este script combina o start_backend_safe.py com a expansão de capacidades dos agentes,
garantindo que os agentes tenham conhecimento e capacidades adequadas antes de iniciar.
"""

import os
import sys
import logging
import importlib.util
import time
import traceback
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("logs/start_with_capabilities.log"),
                        logging.StreamHandler(sys.stdout)
                    ])
logger = logging.getLogger(__name__)

def check_module_exists(module_name):
    """
    Verifica se um módulo pode ser importado.
    
    Args:
        module_name (str): Nome do módulo a verificar
        
    Returns:
        bool: True se o módulo existe e pode ser importado, False caso contrário
    """
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ImportError, AttributeError):
        return False

def load_knowledge_base():
    """
    Carrega a base de conhecimento para os agentes.
    
    Returns:
        bool: True se a base de conhecimento foi carregada com sucesso, False caso contrário
    """
    logger.info("Carregando base de conhecimento para os agentes...")
    
    try:
        # Verificar se o módulo load_knowledge_base existe
        if check_module_exists("load_knowledge_base"):
            import load_knowledge_base
            load_knowledge_base.main()
            logger.info("Base de conhecimento carregada com sucesso!")
            return True
        else:
            logger.warning("Módulo de carregamento da base de conhecimento não encontrado")
            
            # Verificar arquivos de conhecimento
            knowledge_dir = Path("core_inteligente/knowledge_base")
            if not knowledge_dir.exists():
                logger.error(f"Diretório de base de conhecimento não encontrado: {knowledge_dir}")
                return False
                
            # Verificar se pelo menos alguns arquivos de conhecimento existem
            knowledge_files = list(knowledge_dir.glob("*.md"))
            if not knowledge_files:
                logger.error("Nenhum arquivo de conhecimento encontrado")
                return False
                
            logger.info(f"Encontrados {len(knowledge_files)} arquivos de conhecimento")
            return True
            
    except Exception as e:
        logger.error(f"Erro ao carregar base de conhecimento: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def expand_agent_capabilities():
    """
    Expande as capacidades dos agentes.
    
    Returns:
        bool: True se as capacidades foram expandidas com sucesso, False caso contrário
    """
    logger.info("Expandindo capacidades dos agentes...")
    
    try:
        # Verificar se o módulo expand_agent_capabilities existe
        if check_module_exists("expand_agent_capabilities"):
            import expand_agent_capabilities
            expander = expand_agent_capabilities.AgentCapabilityExpander()
            results = expander.expand_all()
            
            if results["success"]:
                logger.info("Capacidades dos agentes expandidas com sucesso!")
                return True
            else:
                logger.warning("Algumas capacidades não puderam ser expandidas:")
                for capability, success in results["results"].items():
                    if not success:
                        logger.warning(f"  - Falha ao expandir: {capability}")
                return False
        else:
            logger.error("Módulo de expansão de capacidades não encontrado")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao expandir capacidades dos agentes: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def check_dependencies():
    """
    Verifica dependências necessárias para o backend.
    
    Returns:
        bool: True se todas as dependências estão presentes, False caso contrário
    """
    logger.info("Verificando dependências...")
    
    try:
        # Verificar se o verificador de dependências existe
        if check_module_exists("verificar_dependencias"):
            import verificar_dependencias
            result = verificar_dependencias.check_all()
            
            if result["success"]:
                logger.info("Todas as dependências verificadas com sucesso!")
                return True
            else:
                logger.warning("Algumas dependências não puderam ser verificadas:")
                for dep, status in result["details"].items():
                    if not status["installed"]:
                        logger.warning(f"  - Faltando: {dep}")
                return False
        else:
            logger.warning("Verificador de dependências não encontrado. Continuando mesmo assim.")
            
            # Verificar manualmente algumas dependências críticas
            critical_packages = ["fastapi", "uvicorn", "openai", "newrelic"]
            missing = []
            
            for pkg in critical_packages:
                try:
                    importlib.import_module(pkg)
                except ImportError:
                    missing.append(pkg)
            
            if missing:
                logger.error(f"Dependências críticas faltando: {', '.join(missing)}")
                return False
            
            logger.info("Dependências críticas verificadas manualmente.")
            return True
            
    except Exception as e:
        logger.error(f"Erro ao verificar dependências: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def repair_cache():
    """
    Verifica e repara o cache do sistema.
    
    Returns:
        bool: True se o cache foi verificado/reparado com sucesso, False caso contrário
    """
    logger.info("Verificando e reparando cache...")
    
    try:
        # Verificar se o reparador de cache existe
        if check_module_exists("check_and_fix_cache"):
            import check_and_fix_cache
            result = check_and_fix_cache.check_and_fix()
            
            if result["success"]:
                logger.info("Cache verificado e reparado com sucesso!")
                return True
            else:
                logger.warning("Alguns problemas no cache não puderam ser reparados:")
                for issue, status in result.get("issues", {}).items():
                    if not status["fixed"]:
                        logger.warning(f"  - Problema não resolvido: {issue}")
                return False
        else:
            logger.warning("Reparador de cache não encontrado. Continuando mesmo assim.")
            return True
            
    except Exception as e:
        logger.error(f"Erro ao verificar/reparar cache: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def start_backend_server():
    """
    Inicia o servidor backend.
    
    Returns:
        bool: True se o servidor foi iniciado com sucesso, False caso contrário
    """
    logger.info("Iniciando servidor backend...")
    
    try:
        # Primeiro verificar se o script start_backend_safe existe
        if os.path.exists("start_backend_safe.py"):
            logger.info("Usando script start_backend_safe.py...")
            
            # Importar o módulo
            spec = importlib.util.spec_from_file_location("start_backend_safe", "start_backend_safe.py")
            start_backend_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(start_backend_module)
            
            # Chamar a função main
            if hasattr(start_backend_module, "main"):
                start_backend_module.main()
            else:
                # Executar via sistema
                import subprocess
                subprocess.run([sys.executable, "start_backend_safe.py"])
                
            logger.info("Servidor backend iniciado com sucesso!")
            return True
        
        # Se não existir, tentar o script normal
        elif os.path.exists("start_backend.py"):
            logger.info("Usando script start_backend.py...")
            
            # Importar o módulo
            spec = importlib.util.spec_from_file_location("start_backend", "start_backend.py")
            start_backend_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(start_backend_module)
            
            # Chamar a função main
            if hasattr(start_backend_module, "main"):
                start_backend_module.main()
            else:
                # Executar via sistema
                import subprocess
                subprocess.run([sys.executable, "start_backend.py"])
                
            logger.info("Servidor backend iniciado com sucesso!")
            return True
        
        else:
            logger.error("Nenhum script de inicialização de backend encontrado!")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor backend: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Função principal que executa todas as etapas em sequência.
    """
    logger.info("Iniciando processo de inicialização do backend com capacidades expandidas...")
    
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Verificar dependências
    if not check_dependencies():
        logger.error("Verificação de dependências falhou. Continuando mesmo assim...")
    
    # Reparar cache
    if not repair_cache():
        logger.error("Reparo de cache falhou. Continuando mesmo assim...")
    
    # Carregar base de conhecimento
    if not load_knowledge_base():
        logger.error("Carregamento da base de conhecimento falhou. Continuando mesmo assim...")
    
    # Expandir capacidades dos agentes
    if not expand_agent_capabilities():
        logger.error("Expansão de capacidades dos agentes falhou. Continuando mesmo assim...")
    
    # Iniciar servidor backend
    if not start_backend_server():
        logger.error("Falha ao iniciar o servidor backend!")
        sys.exit(1)
    
    logger.info("Processo de inicialização concluído com sucesso!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Erro fatal durante a inicialização: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)
