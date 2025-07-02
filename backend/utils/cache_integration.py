"""
Módulo para integração automática do sistema de cache avançado com o restante da aplicação.
Este módulo é carregado durante o startup da aplicação para garantir que o cache
seja inicializado corretamente.
"""

import asyncio
import logging
from pathlib import Path
import sys
import json
import os

# Configuração de logging
logger = logging.getLogger(__name__)

# Importar módulos de cache
try:
    from .cache_initializer import inicializar_cache
    from .cache_advanced import collect_cached_data
except ImportError:
    logger.error("Erro ao importar módulos de cache. Verificando caminho...")
    # Adicionar caminhos alternativos para importação
    current_dir = Path(__file__).parent
    sys.path.append(str(current_dir.parent))
    
    try:
        from utils.cache_initializer import inicializar_cache
        from utils.cache_advanced import collect_cached_data
        logger.info("Módulos de cache importados com sucesso após ajuste de caminho")
    except ImportError as e:
        logger.error(f"Falha ao importar módulos de cache mesmo após ajuste de caminho: {e}")
        raise

def update_cache_file(filename, data, cache_dirs=None):
    """
    Atualiza um arquivo de cache com novos dados
    
    Args:
        filename: Nome do arquivo de cache (sem o caminho)
        data: Dados a serem salvos (objeto que pode ser serializado para JSON)
        cache_dirs: Lista de diretórios de cache onde salvar os dados
                   Se None, usa os diretórios padrão ['backend/cache', 'cache']
                   
    Returns:
        bool: True se o cache foi atualizado com sucesso, False caso contrário
    """
    if cache_dirs is None:
        cache_dirs = ["backend/cache", "cache"]
        
    success = False
    
    for cache_dir in cache_dirs:
        try:
            # Garantir que o diretório existe
            os.makedirs(cache_dir, exist_ok=True)
            
            # Caminho completo para o arquivo de cache
            cache_path = os.path.join(cache_dir, filename)
            
            # Salvar os dados em formato JSON
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"✅ Cache atualizado com sucesso: {cache_path}")
            success = True
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar cache {cache_dir}/{filename}: {e}")
    
    return success

# Inicializar o cache em background
async def init_cache_async():
    """Inicializa o cache de forma assíncrona."""
    try:
        logger.info("Iniciando o sistema de cache avançado...")
        success = await inicializar_cache(collect_cached_data)
        if success:
            logger.info("✅ Sistema de cache avançado inicializado com sucesso")
        else:
            logger.error("❌ Falha ao inicializar o sistema de cache avançado")
    except Exception as e:
        logger.error(f"Erro durante inicialização do cache: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Criar task para inicialização do cache
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    # Se não houver um event loop, criar um novo
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Executar inicialização do cache
try:
    logger.info("Agendando inicialização do sistema de cache...")
    loop.create_task(init_cache_async())
    logger.info("Task de inicialização do cache agendada com sucesso")
except Exception as e:
    logger.error(f"Erro ao agendar task de inicialização do cache: {e}")
    import traceback
    logger.error(traceback.format_exc())
