import asyncio
import logging
from datetime import datetime, timedelta
import aiofiles
import json
import traceback
from pathlib import Path
import os

logger = logging.getLogger(__name__)

# Cache em memória com estrutura melhorada
_cache = {
    "metadados": {
        "ultima_atualizacao": None,
        "atualizacao_forcada": False,
        "tipo_ultima_atualizacao": "nenhuma"
    },
    "dados": {},
    "consultas_historicas": {}
}

# Atualizar uma vez ao dia (86400 segundos = 24 horas)
CACHE_UPDATE_INTERVAL = 86400  # 24 horas
CACHE_HISTORICO_DIR = Path("historico")
CACHE_FILE = CACHE_HISTORICO_DIR / "cache_completo.json"
CACHE_CONSULTA_DIR = CACHE_HISTORICO_DIR / "consultas"

async def carregar_cache_do_disco():
    """Carrega o cache do disco se existir."""
    try:        # Certifique-se de que o diretório existe
        os.makedirs(CACHE_HISTORICO_DIR, exist_ok=True)
        os.makedirs(CACHE_CONSULTA_DIR, exist_ok=True)
        
        if CACHE_FILE.exists():
            logger.info(f"Carregando cache do arquivo: {CACHE_FILE}")
            # Usando open normal em vez de aiofiles para evitar problemas com o await
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                dados_carregados = json.loads(conteudo)
                
                # Atualiza o cache em memória com os dados do disco
                _cache["dados"] = dados_carregados
                _cache["metadados"]["ultima_atualizacao"] = dados_carregados.get("timestamp")
                logger.info(f"Cache carregado com sucesso. Timestamp: {_cache['metadados']['ultima_atualizacao']}")
                return True
        else:
            logger.warning(f"Arquivo de cache não encontrado: {CACHE_FILE}")
            return False
    except Exception as e:
        logger.error(f"Erro ao carregar cache do disco: {e}")
        logger.error(traceback.format_exc())
        return False

async def salvar_cache_no_disco():
    """Salva o cache atual no disco."""
    try:
        # Certifique-se de que o diretório existe
        os.makedirs(CACHE_HISTORICO_DIR, exist_ok=True)
        # Adiciona timestamp antes de salvar
        if "timestamp" not in _cache["dados"]:
            _cache["dados"]["timestamp"] = datetime.now().isoformat()
            
        # Usando open normal em vez de aiofiles para evitar problemas
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            f.write(json.dumps(_cache["dados"], ensure_ascii=False, indent=2))
        
        logger.info(f"Cache salvo em disco com sucesso: {CACHE_FILE}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar cache em disco: {e}")
        logger.error(traceback.format_exc())
        return False

async def salvar_consulta_historica(consulta, resultado):
    """Salva uma consulta específica no histórico."""
    try:
        # Gera um nome de arquivo baseado na consulta (versão simplificada)
        consulta_hash = hash(consulta) % 10000000
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = CACHE_CONSULTA_DIR / f"consulta_{consulta_hash}_{timestamp}.json"
        # Salva a consulta e resultado
        dados = {
            "consulta": consulta,
            "timestamp": datetime.now().isoformat(),
            "resultado": resultado
        }
        
        os.makedirs(CACHE_CONSULTA_DIR, exist_ok=True)
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(json.dumps(dados, ensure_ascii=False, indent=2))
        
        # Atualiza cache em memória
        _cache["consultas_historicas"][consulta] = {
            "timestamp": datetime.now().isoformat(),
            "arquivo": str(arquivo)
        }
        
        logger.info(f"Consulta salva em: {arquivo}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar consulta: {e}")
        return False

async def get_cache(forcar_atualizacao=False, consulta=None):
    """
    Retorna o cache atual. Sempre retorna o último cache válido, mesmo se a coleta falhar.
    
    Args:
        forcar_atualizacao: Se True, força a atualização do cache mesmo que seja recente
        consulta: String com consulta específica para verificar no histórico
    """
    global _cache
    agora = datetime.now()
    
    # Inicializa o cache do disco se necessário
    if not _cache["dados"]:
        await carregar_cache_do_disco()
    
    # Verifica se uma consulta específica está no histórico
    if consulta and consulta in _cache["consultas_historicas"]:
        consulta_info = _cache["consultas_historicas"][consulta]
        consulta_timestamp = datetime.fromisoformat(consulta_info["timestamp"])
        # Se a consulta é recente (menos de 24h), não precisa atualizar
        if (agora - consulta_timestamp).total_seconds() < CACHE_UPDATE_INTERVAL:
            logger.info(f"Usando cache para consulta: {consulta[:50]}...")
            try:
                arquivo = consulta_info["arquivo"]
                with open(arquivo, 'r', encoding='utf-8') as f:
                    return json.loads(f.read())["resultado"]
            except Exception:
                logger.warning(f"Erro ao ler consulta do histórico, ignorando.")
    
    # Verificar se o cache está atualizado
    if "timestamp" in _cache["dados"]:
        ultima_atualizacao = datetime.fromisoformat(_cache["dados"]["timestamp"])
        tempo_desde_atualizacao = (agora - ultima_atualizacao).total_seconds()
        
        # Se o cache está atualizado e não estamos forçando, retorna-o
        if tempo_desde_atualizacao < CACHE_UPDATE_INTERVAL and not forcar_atualizacao:
            logger.info(f"Cache atualizado, última atualização: {ultima_atualizacao.isoformat()}")
            return _cache["dados"]
        else:
            # Marca que é necessário atualização
            _cache["metadados"]["atualizacao_forcada"] = forcar_atualizacao
    
    # Se chegou aqui, o cache deve ser usado como está até ser atualizado em background
    logger.info("Obtendo cache atual, atualização em progresso...")
    return _cache["dados"]

async def atualizar_cache_completo(coletar_contexto_fn):
    """
    Atualiza o cache completo com dados do New Relic.
    Implementa fallback seguro: se a coleta falhar ou retornar dados vazios,
    mantém o cache anterior válido.
    
    Também filtra entidades inválidas e garante qualidade de dados antes
    de atualizar o cache definitivo.
    """
    logger.info("Iniciando atualização completa do cache")
    
    # Guarda o cache atual como backup
    cache_anterior = _cache["dados"].copy() if _cache["dados"] else {}
    
    try:
        # Coleta dados do New Relic
        contexto = await coletar_contexto_fn()
        
        if not contexto or not isinstance(contexto, dict):
            logger.error(f"Contexto inválido recebido da função coletar_contexto: {type(contexto)}")
            logger.warning("Mantendo cache anterior devido a contexto inválido")
            return False
            
        # Verifica se a coleta teve sucesso baseado nos metadados
        metadata = contexto.get('metadata', {})
        coleta_bem_sucedida = metadata.get('coleta_bem_sucedida', False)
        rate_limit_failures = metadata.get('rate_limit_failures', 0)
        
        # Adiciona timestamp de atualização
        contexto['timestamp'] = datetime.now().isoformat()
        
        # Validações básicas do contexto coletado
        entidades_originais = contexto.get('entidades', [])
        
        # Filtra entidades inválidas
        if entidades_originais:
            from utils.entity_processor import filter_entities_with_data
            entidades_validas = filter_entities_with_data(entidades_originais)
            
            entidades_removidas = len(entidades_originais) - len(entidades_validas)
            if entidades_removidas > 0:
                logger.info(f"Filtradas {entidades_removidas} entidades sem dados válidos durante atualização")
                
            # Atualiza o contexto com apenas entidades válidas
            contexto['entidades'] = entidades_validas
            
            # Adiciona metadados sobre filtragem
            if not contexto.get('metadata'):
                contexto['metadata'] = {}
            contexto['metadata']['entidades_filtradas'] = entidades_removidas
            contexto['metadata']['entidades_validas'] = len(entidades_validas)
            contexto['metadata']['qualidade_dados'] = 'alta' if len(entidades_validas) > 0 else 'baixa'
        
        # Agora trabalha com entidades filtradas
        entidades = contexto.get('entidades', [])
        
        # FALLBACK SEGURO: Se não coletou nenhuma entidade OU houve muitas falhas de rate limit
        if not entidades or rate_limit_failures > 5:
            logger.warning(f"Coleta falhou ou com muitos rate limits (falhas: {rate_limit_failures})")
            
            # Se temos um cache anterior válido, mantemos ele
            if cache_anterior and cache_anterior.get('entidades'):
                logger.info(f"FALLBACK: Mantendo cache anterior com {len(cache_anterior['entidades'])} entidades")
                
                # Atualiza apenas o timestamp do cache anterior para indicar que foi "verificado"
                cache_anterior['last_check'] = datetime.now().isoformat()
                cache_anterior['fallback_reason'] = f"Rate limit failures: {rate_limit_failures}, Empty entities: {len(entidades)}"
                
                _cache["dados"] = cache_anterior
                _cache["metadados"]["ultima_atualizacao"] = datetime.now().isoformat()
                _cache["metadados"]["tipo_ultima_atualizacao"] = "fallback_seguro"
                
                # Salva o cache anterior (com timestamp atualizado)
                await salvar_cache_no_disco()
                
                logger.info("Fallback seguro aplicado: cache anterior mantido")
                return True
            else:
                logger.error("Nenhum cache anterior válido disponível e coleta atual falhou")
                return False
        
        # Se chegou aqui, a coleta foi bem-sucedida
        logger.info(f"Coleta bem-sucedida com {len(entidades)} entidades")
        
        # Verifica entidades por domínio
        dominios = {}
        for entidade in entidades:
            domain = entidade.get('domain', 'DESCONHECIDO')
            dominios[domain] = dominios.get(domain, 0) + 1
        
        logger.info(f"Entidades coletadas por domínio: {dominios}")
        
        # Verifica entidades sem métricas
        sem_metricas = [e['name'] for e in entidades if not e.get('metricas')]
        if sem_metricas:
            logger.warning(f"{len(sem_metricas)} entidades sem métricas: {sem_metricas[:5]}...")
        
        # Atualiza o cache em memória com os novos dados
        _cache["dados"] = contexto
        _cache["metadados"]["ultima_atualizacao"] = datetime.now().isoformat()
        _cache["metadados"]["tipo_ultima_atualizacao"] = "completa"
        _cache["metadados"]["atualizacao_forcada"] = False
        
        # Salva em disco
        await salvar_cache_no_disco()
        
        logger.info(f"Cache atualizado com sucesso às {datetime.now().isoformat()}")
        return True
        
    except Exception as e:
        logger.error(f"Erro crítico ao atualizar cache: {e}")
        logger.error(traceback.format_exc())
        
        # FALLBACK CRÍTICO: Se houve erro crítico, tenta manter cache anterior
        if cache_anterior and cache_anterior.get('entidades'):
            logger.warning("FALLBACK CRÍTICO: Restaurando cache anterior após erro")
            
            cache_anterior['last_check'] = datetime.now().isoformat()
            cache_anterior['fallback_reason'] = f"Critical error: {str(e)}"
            
            _cache["dados"] = cache_anterior
            _cache["metadados"]["ultima_atualizacao"] = datetime.now().isoformat()
            _cache["metadados"]["tipo_ultima_atualizacao"] = "fallback_critico"
            
            try:
                await salvar_cache_no_disco()
                logger.info("Fallback crítico aplicado: cache anterior restaurado")
                return True
            except Exception as save_error:
                logger.error(f"Erro ao salvar cache durante fallback crítico: {save_error}")
        
        return False

async def atualizar_cache_incremental(coletar_contexto_fn, filtro=None):
    """
    Atualiza apenas partes específicas do cache com base em filtros
    
    Args:
        filtro: Dicionário com critérios para atualização parcial, exemplo:
               {"domain": "APM", "guid": "abc123"}
    """
    logger.info(f"Iniciando atualização incremental do cache com filtro: {filtro}")
    try:
        # Implemente a lógica específica para atualização parcial
        # Por exemplo, coletando apenas entidades específicas
        # Esta é uma implementação simplificada
        
        if not _cache["dados"]:
            # Se o cache ainda não foi inicializado, faça uma atualização completa
            return await atualizar_cache_completo(coletar_contexto_fn)
        
        # Aqui implementaríamos a lógica para buscar só parte dos dados
        # baseado no filtro (não implementado nesta versão)
        
        _cache["metadados"]["ultima_atualizacao_parcial"] = datetime.now().isoformat()
        _cache["metadados"]["tipo_ultima_atualizacao"] = "incremental"
        
        # Salva em disco
        await salvar_cache_no_disco()
        
        logger.info(f"Cache atualizado incrementalmente às {datetime.now().isoformat()}")
        return True
        
    except Exception as e:
        logger.error(f"Erro na atualização incremental: {e}")
        logger.error(traceback.format_exc())
        return False

async def cache_updater_loop(coletar_contexto_fn):
    """
    Loop contínuo para atualização periódica do cache (1x ao dia)
    """
    logger.info("Iniciando loop de atualização de cache (1x ao dia)")
    await carregar_cache_do_disco()
    while True:
        try:
            atualizar = False
            if not _cache["dados"]:
                logger.info("Cache vazio, iniciando primeira atualização")
                atualizar = True
            elif "timestamp" in _cache["dados"]:
                ultima_atualizacao = datetime.fromisoformat(_cache["dados"]["timestamp"])
                agora = datetime.now()
                if (agora - ultima_atualizacao).total_seconds() >= CACHE_UPDATE_INTERVAL:
                    logger.info(f"Cache desatualizado (última atualização: {ultima_atualizacao.isoformat()}), atualizando...")
                    atualizar = True
            elif _cache["metadados"]["atualizacao_forcada"]:
                logger.info("Atualização forçada solicitada")
                atualizar = True
            if atualizar:
                sucesso = await atualizar_cache_completo(coletar_contexto_fn)
                if not sucesso:
                    logger.warning("Falha na atualização do cache. Mantendo dados antigos até próxima tentativa.")
                logger.info(f"Próxima atualização programada para {CACHE_UPDATE_INTERVAL/3600} horas depois")
        except Exception as e:
            logger.error(f"Erro no loop de atualização: {e}")
            logger.error(traceback.format_exc())
        await asyncio.sleep(3600)  # Checa a cada hora, mas só atualiza se passou 24h

def diagnosticar_cache():
    """Diagnostica o estado do cache."""
    logger.info("Diagnosticando cache.")
    
    # Prepara estatísticas
    estatisticas = {
        "total_chaves_dados": len(_cache["dados"]) if _cache["dados"] else 0,
        "chaves_dados": list(_cache["dados"].keys()) if _cache["dados"] else [],
        "metadados": _cache["metadados"],
        "total_consultas_historicas": len(_cache["consultas_historicas"]),
        "tamanho_disco_mb": 0,
        "ultima_atualizacao": _cache["metadados"]["ultima_atualizacao"],
        "status": "não inicializado"
    }
    
    # Verifica tamanho do arquivo de cache
    if CACHE_FILE.exists():
        estatisticas["tamanho_disco_mb"] = round(CACHE_FILE.stat().st_size / (1024 * 1024), 2)
        estatisticas["status"] = "carregado"
    
    # Verifica idade do cache
    if _cache["metadados"]["ultima_atualizacao"]:
        ultima_atualizacao = datetime.fromisoformat(_cache["metadados"]["ultima_atualizacao"])
        idade_segundos = (datetime.now() - ultima_atualizacao).total_seconds()
        estatisticas["idade_horas"] = round(idade_segundos / 3600, 2)
        estatisticas["atualizado"] = idade_segundos < CACHE_UPDATE_INTERVAL
    
    # Estatísticas por domínio se disponíveis
    if _cache["dados"] and "apm" in _cache["dados"]:
        estatisticas["contagem_por_dominio"] = {
            dominio: len(entidades) 
            for dominio, entidades in _cache["dados"].items()
            if isinstance(entidades, list)
        }
    
    return estatisticas

async def forcar_atualizacao_cache(coletar_contexto_fn):
    """Força uma atualização imediata do cache."""
    logger.info("Solicitada atualização forçada do cache")
    _cache["metadados"]["atualizacao_forcada"] = True
    return await atualizar_cache_completo(coletar_contexto_fn)

async def buscar_no_cache_por_pergunta(pergunta, atualizar_se_necessario=True, coletar_contexto_fn=None):
    """
    Busca informações do cache SEM atualizar em tempo real.
    Sempre retorna o cache mais recente disponível, sem aguardar coleta.
    """
    # Salva esta consulta no histórico para futuras referências
    resultado = await get_cache(forcar_atualizacao=False)
    await salvar_consulta_historica(pergunta, resultado)
    return resultado

# Função para compatibilidade com testes antigos
async def atualizar_cache(coletar_contexto_fn):
    """Função legada para compatibilidade com testes antigos."""
    return await atualizar_cache_completo(coletar_contexto_fn)

async def limpar_cache_de_entidades_invalidas():
    """
    Limpa o cache, removendo entidades sem dados válidos.
    Usa o processador de entidades para filtrar o que será mantido.
    """
    try:
        from utils.entity_processor import filter_entities_with_data, is_entity_valid
        
        if "entidades" not in _cache["dados"] or not _cache["dados"]["entidades"]:
            logger.warning("Nenhuma entidade no cache para limpar")
            return 0
            
        total_antes = len(_cache["dados"]["entidades"])
        logger.info(f"Iniciando limpeza de cache: {total_antes} entidades antes da limpeza")
        
        # Filtra entidades válidas usando o processador
        entidades_validas = filter_entities_with_data(_cache["dados"]["entidades"])
        
        # Atualiza o cache com apenas entidades válidas
        _cache["dados"]["entidades"] = entidades_validas
        total_depois = len(_cache["dados"]["entidades"])
        
        # Adiciona metadados sobre a limpeza
        _cache["metadados"]["ultima_limpeza"] = datetime.now().isoformat()
        _cache["metadados"]["entidades_removidas"] = total_antes - total_depois
        
        logger.info(f"Limpeza concluída: {total_depois} entidades mantidas, {total_antes - total_depois} removidas")
        
        # Salva o cache limpo
        await salvar_cache_no_disco()
        
        return total_antes - total_depois
        
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        logger.error(traceback.format_exc())
        return 0