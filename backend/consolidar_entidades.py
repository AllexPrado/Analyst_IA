import logging
import asyncio
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Importar funções necessárias
from utils.cache import get_cache, forcar_atualizacao_cache, _cache, salvar_cache_no_disco
from utils.newrelic_collector import coletar_contexto_completo

async def converter_e_consolidar_entidades():
    """
    Converte e consolida entidades do formato de domínios para uma lista única.
    Busca o cache atual, extrai entidades de cada domínio e cria uma nova chave 'entidades'
    contendo todas as entidades consolidadas.
    """
    try:
        logger.info("Consolidando entidades no cache...")
        cache = await get_cache()
        
        # Verificar se temos dados por domínios
        dominios = ["apm", "browser", "infra", "db", "mobile", "iot", "serverless", "synth", "ext"]
        todas_entidades = []
        
        # Para cada domínio, extrair entidades
        for dominio in dominios:
            if dominio in cache:
                entidades_dominio = cache.get(dominio, [])
                logger.info(f"Encontradas {len(entidades_dominio)} entidades no domínio {dominio.upper()}")
                todas_entidades.extend(entidades_dominio)
        
        logger.info(f"Total de entidades consolidadas: {len(todas_entidades)}")
        
        if not todas_entidades:
            logger.warning("Nenhuma entidade encontrada em nenhum domínio!")
            logger.warning("Chaves disponíveis no cache: " + ", ".join(list(cache.keys())))
            
            # Forçar atualização para garantir dados novos
            logger.info("Forçando atualização do cache para obter novos dados...")
            sucesso = await forcar_atualizacao_cache(coletar_contexto_completo)
            if sucesso:
                logger.info("Cache atualizado com sucesso! Tentando novamente...")
                # Obtenha o cache novamente após a atualização
                cache = await get_cache()
                # Repetir processo com cache atualizado
                todas_entidades = []
                for dominio in dominios:
                    if dominio in cache:
                        entidades_dominio = cache.get(dominio, [])
                        logger.info(f"Após atualização: {len(entidades_dominio)} entidades no domínio {dominio.upper()}")
                        todas_entidades.extend(entidades_dominio)
                
                logger.info(f"Após atualização: Total de entidades consolidadas: {len(todas_entidades)}")
            else:
                logger.error("Falha ao atualizar o cache!")
        
        # Adicionar ao cache a nova lista de entidades consolidada
        _cache["dados"]["entidades"] = todas_entidades
        _cache["dados"]["timestamp"] = datetime.now().isoformat()
        
        # Salvar no disco
        await salvar_cache_no_disco()
        
        logger.info("Entidades consolidadas e adicionadas ao cache com sucesso!")
        return len(todas_entidades) > 0
        
    except Exception as e:
        logger.error(f"Erro ao consolidar entidades: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    asyncio.run(converter_e_consolidar_entidades())
