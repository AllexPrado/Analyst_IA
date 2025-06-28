"""
Módulo de integração para o sistema de cache avançado.
Este módulo substitui as funções originais de cache por implementações mais robustas.
"""

import logging
import functools
import sys
from pathlib import Path

# Configuração de logging
logger = logging.getLogger(__name__)

# Importações internas
from . import cache
from .cache import (
    carregar_cache_do_disco, salvar_cache_no_disco,
    atualizar_cache_completo, get_cache, forcar_atualizacao_cache
)

# Importar os novos módulos
from .cache_initializer import inicializar_cache, verificar_integridade_cache
from .cache_collector import coletar_contexto_completo as coletar_contexto_completo_avancado

def replace_function_in_module(module, function_name, new_function):
    """
    Substitui uma função em um módulo por uma nova função.
    
    Args:
        module: O módulo onde a função será substituída
        function_name: Nome da função a ser substituída
        new_function: Nova função para substituir a original
    """
    if hasattr(module, function_name):
        setattr(module, function_name, new_function)
        logger.info(f"Função {function_name} substituída com sucesso")
        return True
    else:
        logger.warning(f"Função {function_name} não encontrada no módulo")
        return False

async def inicializar_sistema_cache():
    """
    Inicializa o sistema de cache, substituindo as funções originais por implementações
    mais robustas e garantindo que o cache esteja pronto para uso.
    
    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário
    """
    logger.info("Inicializando sistema de cache avançado")
    
    # Substituir função de coleta de contexto
    try:
        import utils.newrelic_collector
        replace_function_in_module(
            utils.newrelic_collector, 
            "coletar_contexto_completo", 
            coletar_contexto_completo_avancado
        )
    except Exception as e:
        logger.error(f"Erro ao substituir função de coleta de contexto: {e}")
        return False
    
    # Inicializar o cache
    try:
        resultado = await inicializar_cache(coletar_contexto_completo_avancado)
        if not resultado:
            logger.error("Falha ao inicializar o cache")
            return False
            
        logger.info("Sistema de cache inicializado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar o cache: {e}")
        return False

async def status_cache():
    """
    Retorna status detalhado do sistema de cache.
    
    Returns:
        dict: Status do sistema de cache
    """
    try:
        # Verificar integridade do cache
        integridade = await verificar_integridade_cache()
        
        return {
            "status": "healthy" if integridade["integridade"] else "degraded",
            "cache_valido": integridade["integridade"],
            "ultima_atualizacao": integridade["ultima_atualizacao"],
            "idade_horas": integridade["idade_horas"],
            "total_entidades": integridade["total_entidades"],
            "entidades_por_dominio": integridade["entidades_por_dominio"],
            "erros": integridade["erros"]
        }
    except Exception as e:
        logger.error(f"Erro ao obter status do cache: {e}")
        
        return {
            "status": "error",
            "erro": str(e)
        }

async def atualizar_cache_incremental(filtro=None):
    """
    Atualiza o cache de forma incremental, apenas para entidades específicas.
    Esta implementação é mais completa que a original.
    
    Args:
        filtro: Filtro para selecionar as entidades que serão atualizadas
            - domain: Domínio específico para atualizar (APM, BROWSER, etc.)
            - guid: GUID específico da entidade para atualizar
            - name: Nome da entidade para atualizar (busca por substring)
            
    Returns:
        bool: True se a atualização foi bem-sucedida, False caso contrário
    """
    logger.info(f"Iniciando atualização incremental do cache com filtro: {filtro}")
    
    try:
        # Se não houver filtro, faz uma atualização completa
        if not filtro:
            logger.info("Sem filtro, realizando atualização completa")
            return await atualizar_cache_completo(coletar_contexto_completo_avancado)
        
        # Obter o cache atual
        cache_atual = await get_cache(forcar_atualizacao=False)
        
        # Se o cache estiver vazio, faz uma atualização completa
        if not cache_atual or not cache_atual.get("entidades"):
            logger.info("Cache vazio, realizando atualização completa")
            return await atualizar_cache_completo(coletar_contexto_completo_avancado)
        
        # Selecionar entidades que correspondem ao filtro
        entidades_atuais = cache_atual.get("entidades", [])
        entidades_para_atualizar = []
        
        # Aplica filtros
        domain_filtro = filtro.get("domain", "").upper() if filtro.get("domain") else None
        guid_filtro = filtro.get("guid")
        name_filtro = filtro.get("name", "").lower() if filtro.get("name") else None
        
        for entidade in entidades_atuais:
            # Verifica se corresponde ao filtro
            match = True
            
            if domain_filtro and entidade.get("domain", "").upper() != domain_filtro:
                match = False
                
            if guid_filtro and entidade.get("guid") != guid_filtro:
                match = False
                
            if name_filtro and name_filtro not in entidade.get("name", "").lower():
                match = False
                
            if match:
                entidades_para_atualizar.append(entidade)
        
        # Se não houver entidades para atualizar, retorna False
        if not entidades_para_atualizar:
            logger.warning(f"Nenhuma entidade corresponde ao filtro: {filtro}")
            return False
        
        logger.info(f"Selecionadas {len(entidades_para_atualizar)} entidades para atualização")
        
        # Criar um novo cache com base no atual
        novo_cache = cache_atual.copy()
        
        # Aqui implementaríamos a lógica para atualizar apenas estas entidades
        # (não implementado completamente nesta versão)
        
        # Por enquanto, forçamos uma atualização completa
        logger.info("Funcionalidade de atualização incremental em desenvolvimento")
        logger.info("Realizando atualização completa como fallback")
        
        return await atualizar_cache_completo(coletar_contexto_completo_avancado)
        
    except Exception as e:
        logger.error(f"Erro na atualização incremental: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# Exporta funções
__all__ = [
    'inicializar_sistema_cache',
    'status_cache',
    'atualizar_cache_incremental',
    'coletar_contexto_completo_avancado'
]
