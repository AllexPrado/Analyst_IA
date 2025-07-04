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

def atualizar_coverage_cache():
    """
    Calcula e preenche o campo 'coverage' em metadata do cache,
    baseado nas entidades reais coletadas.
    """
    try:
        cache_dados = _cache.get("dados", {})
        coverage = {}

        # Domínios críticos a serem cobertos
        dominios_criticos = [
            "APM", "BROWSER", "MOBILE", "SYNTH", "INFRA", "DASHBOARDS", "LOGS", "ALERTAS", "INCIDENTES", "WORKLOADS", "KPIS", "TENDENCIAS"
        ]

        # Mapeamento de nomes alternativos para domínios
        aliases = {
            "dashboards": "DASHBOARDS",
            "logs": "LOGS",
            "alertas": "ALERTAS",
            "incidentes": "INCIDENTES",
            "workloads": "WORKLOADS",
            "kpis": "KPIS",
            "tendencias": "TENDENCIAS"
        }

        # Normaliza domínios presentes no cache
        for domain, entities in cache_dados.items():
            dom = aliases.get(domain.lower(), domain.upper())
            if not isinstance(entities, list):
                continue
            total_entities = len(entities)
            complete_entities = 0
            # Critérios de "completo" por domínio
            for ent in entities:
                if dom in ["APM", "BROWSER", "MOBILE", "SYNTH", "INFRA"]:
                    if ent.get("reporting") and any(ent.get(k) for k in ["metricas", "metrics", "apdex", "response_time", "error_rate", "throughput"]):
                        complete_entities += 1
                elif dom == "LOGS":
                    if ent.get("log_count", 0) > 0 or ent.get("logs"):
                        complete_entities += 1
                elif dom == "DASHBOARDS":
                    if ent.get("widgets") or ent.get("visualizations"):
                        complete_entities += 1
                elif dom == "ALERTAS":
                    if ent.get("status") in ["open", "triggered", "acknowledged", "closed"]:
                        complete_entities += 1
                elif dom == "INCIDENTES":
                    if ent.get("status") in ["open", "closed", "acknowledged"]:
                        complete_entities += 1
                elif dom == "WORKLOADS":
                    if ent.get("entities") and len(ent.get("entities", [])) > 0:
                        complete_entities += 1
                elif dom == "KPIS":
                    if any(ent.get(k) for k in ["apdex", "response_time", "throughput", "error_rate"]):
                        complete_entities += 1
                elif dom == "TENDENCIAS":
                    if ent.get("trend") or ent.get("tendencia"):
                        complete_entities += 1
                else:
                    # fallback: reporting True e alguma métrica
                    if ent.get("reporting") and any(ent.get(k) for k in ["metricas", "metrics", "apdex", "response_time", "error_rate"]):
                        complete_entities += 1
            coverage[dom] = {
                "total_entities": total_entities,
                "complete_entities": complete_entities
            }

        # Garante que todos os domínios críticos estejam presentes no coverage
        for dom in dominios_criticos:
            if dom not in coverage:
                coverage[dom] = {"total_entities": 0, "complete_entities": 0}

        # Preenche no metadata
        if "metadata" not in cache_dados:
            cache_dados["metadata"] = {}
        cache_dados["metadata"]["coverage"] = coverage
        _cache["dados"] = cache_dados
        logger.info(f"Coverage atualizado no cache: {coverage}")
        return coverage
    except Exception as e:
        logger.error(f"Erro ao atualizar coverage no cache: {e}")
        logger.error(traceback.format_exc())
        return None

# Configurações de cache multinível
CACHE_UPDATE_INTERVAL = 3600  # Cache principal: 1 hora
CACHE_SHORT_INTERVAL = 30  # Cache curta duração: 30 segundos (para consultas frequentes)
CACHE_LONG_INTERVAL = 86400  # Cache longa duração: 24 horas (para dados históricos)

# Diretórios e arquivos de cache
CACHE_HISTORICO_DIR = Path("historico")
CACHE_CONSULTA_DIR = Path("consultas")  # Diretório para consultas históricas
CACHE_FILE = CACHE_HISTORICO_DIR / "cache_completo.json"
CACHE_SHORT_FILE = CACHE_HISTORICO_DIR / "cache_rapido.json"
CACHE_LONG_FILE = CACHE_HISTORICO_DIR / "cache_longo.json"

# Adicionado para integração com o coletor avançado
USAR_COLETOR_AVANCADO = os.getenv("USAR_COLETOR_AVANCADO", "true").lower() == "true"

async def carregar_cache_do_disco():
    """Carrega o cache do disco se existir."""
    try:        # Certifique-se de que o diretório existe
        os.makedirs(CACHE_HISTORICO_DIR, exist_ok=True)
        
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
        arquivo = CACHE_HISTORICO_DIR / f"consulta_{consulta_hash}_{timestamp}.json"
        # Salva a consulta e resultado
        dados = {
            "consulta": consulta,
            "timestamp": datetime.now().isoformat(),
            "resultado": resultado
        }
        
        os.makedirs(CACHE_HISTORICO_DIR, exist_ok=True)
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

async def get_cache(forcar_atualizacao=False, consulta=None, tipo_cache="padrao"):
    """
    Retorna o cache atual com monitoramento de desempenho e estatísticas.
    Suporta diferentes níveis de cache conforme necessidade.
    
    Args:
        forcar_atualizacao: Se True, força a atualização do cache mesmo que seja recente
        consulta: String com consulta específica para verificar no histórico
        tipo_cache: Tipo de cache a usar: "padrao" (1h), "rapido" (30s), "longo" (24h)
    """
    global _cache
    agora = datetime.now()
    inicio = datetime.now()
    cache_hit = False
    
    # Define o intervalo baseado no tipo de cache solicitado
    intervalo = CACHE_UPDATE_INTERVAL  # Padrão: 1 hora
    if tipo_cache == "rapido":
        intervalo = CACHE_SHORT_INTERVAL  # 30 segundos
    elif tipo_cache == "longo":
        intervalo = CACHE_LONG_INTERVAL  # 24 horas
    
    # Inicializa contadores de estatísticas se não existirem
    if "cache_hits" not in _cache["metadados"]:
        _cache["metadados"]["cache_hits"] = 0
    if "cache_misses" not in _cache["metadados"]:
        _cache["metadados"]["cache_misses"] = 0
    if "tempo_medio_acesso_ms" not in _cache["metadados"]:
        _cache["metadados"]["tempo_medio_acesso_ms"] = 0
    if "acessos_total" not in _cache["metadados"]:
        _cache["metadados"]["acessos_total"] = 0
    
    # Inicializa o cache do disco se necessário
    if not _cache["dados"]:
        logger.info("Cache vazio, carregando do disco...")
        await carregar_cache_do_disco()
    
    # Verifica se uma consulta específica está no histórico
    if consulta and consulta in _cache["consultas_historicas"]:
        consulta_info = _cache["consultas_historicas"][consulta]
        consulta_timestamp = datetime.fromisoformat(consulta_info["timestamp"])
        # Se a consulta é recente (dentro do intervalo), usa o cache
        if (agora - consulta_timestamp).total_seconds() < intervalo:
            logger.info(f"Cache HIT: Usando cache para consulta: {consulta[:50]}...")
            try:
                arquivo = consulta_info["arquivo"]
                with open(arquivo, 'r', encoding='utf-8') as f:
                    # Registra hit no cache
                    _cache["metadados"]["cache_hits"] += 1
                    cache_hit = True
                    return json.loads(f.read())["resultado"]
            except Exception as e:
                logger.warning(f"Erro ao ler consulta do histórico: {e}")
    
    # Verificar se o cache está atualizado
    if "timestamp" in _cache["dados"]:
        ultima_atualizacao = datetime.fromisoformat(_cache["dados"]["timestamp"])
        tempo_desde_atualizacao = (agora - ultima_atualizacao).total_seconds()
        
        # Se o cache está atualizado e não estamos forçando, retorna-o
        if tempo_desde_atualizacao < intervalo and not forcar_atualizacao:
            logger.info(f"Cache HIT: Cache atualizado, última atualização: {ultima_atualizacao.isoformat()}")
            # Registra hit no cache
            _cache["metadados"]["cache_hits"] += 1
            cache_hit = True
        else:
            # Marca que é necessário atualização
            _cache["metadados"]["atualizacao_forcada"] = forcar_atualizacao
            # Registra miss no cache (dados desatualizados)
            _cache["metadados"]["cache_misses"] += 1
            logger.info(f"Cache MISS: Dados desatualizados ({tempo_desde_atualizacao:.0f}s > {intervalo}s)")
    else:
        # Registra miss no cache (dados incompletos)
        _cache["metadados"]["cache_misses"] += 1
        logger.info("Cache MISS: Dados incompletos")
    
    # Calcula o tempo de acesso ao cache
    tempo_acesso = (datetime.now() - inicio).total_seconds() * 1000  # milissegundos
    
    # Atualiza estatísticas de tempo de acesso
    acessos_anteriores = _cache["metadados"]["acessos_total"]
    tempo_medio_anterior = _cache["metadados"]["tempo_medio_acesso_ms"]
    
    if acessos_anteriores > 0:
        # Média móvel ponderada
        novo_tempo_medio = (tempo_medio_anterior * acessos_anteriores + tempo_acesso) / (acessos_anteriores + 1)
    else:
        novo_tempo_medio = tempo_acesso
    
    _cache["metadados"]["tempo_medio_acesso_ms"] = round(novo_tempo_medio, 2)
    _cache["metadados"]["acessos_total"] += 1
    
    # Se foi um miss, mas temos dados anteriores, usamos o que temos
    # enquanto a atualização acontece em background
    if not cache_hit:
        logger.info("Usando cache atual enquanto atualização ocorre em background...")
    
    return _cache["dados"]

async def atualizar_cache_completo(coletar_contexto_fn):
    """
    Atualiza o cache completo usando a função de coleta fornecida.
    Suporta tanto o coletor original quanto o avançado.
    
    Args:
        coletar_contexto_fn: Função que coleta o contexto completo do New Relic
        
    Returns:
        bool: True se a atualização foi bem-sucedida, False caso contrário
    """
    logger.info("Iniciando atualização completa do cache")
    try:
        # Tenta usar o coletor avançado se disponível
        try:
            from .newrelic_advanced_collector import collect_full_data
            # Verifica se a função passada é o coletor avançado
            import inspect
            fn_name = coletar_contexto_fn.__name__ if hasattr(coletar_contexto_fn, '__name__') else str(coletar_contexto_fn)
            
            if "advanced" in fn_name or fn_name == "collect_full_data":
                logger.info("Usando coletor avançado para atualização completa")
                resultado = await collect_full_data()
            else:
                logger.info("Usando coletor padrão para atualização completa")
                resultado = await coletar_contexto_fn()
        except ImportError:
            logger.info("Coletor avançado não disponível, usando coletor padrão")
            resultado = await coletar_contexto_fn()
        
        if resultado and "entidades" in resultado:
            # Filtra entidades para garantir qualidade dos dados
            from .entity_processor import filter_entities_with_data
            entidades_filtradas = filter_entities_with_data(resultado["entidades"])
            
            # Atualiza o cache
            resultado["entidades"] = entidades_filtradas
            resultado["timestamp"] = datetime.now().isoformat()
            _cache["dados"] = resultado
            _cache["metadados"]["ultima_atualizacao"] = datetime.now().isoformat()
            _cache["metadados"]["tipo_ultima_atualizacao"] = "completa"
            _cache["metadados"]["atualizacao_forcada"] = False
            
            # Salva o cache atualizado
            await salvar_cache_no_disco()
            
            logger.info(f"Cache atualizado com sucesso: {len(entidades_filtradas)} entidades válidas")
            return True
        else:
            logger.error("Falha ao atualizar cache: dados inválidos retornados pelo coletor")
            return False
    except Exception as e:
        logger.error(f"Erro ao atualizar cache completo: {e}")
        logger.error(traceback.format_exc())
        return False

async def atualizar_cache_completo_avancado():
    """
    Atualiza o cache utilizando o coletor avançado que coleta 100% dos dados do New Relic:
    - Métricas básicas (Apdex, Response Time, Error Rate, Throughput)
    - Logs detalhados
    - Traces e distribuições
    - Backtraces de erros
    - Queries SQL e performance
    - Informações de execução de código
    - Relacionamentos entre entidades
    
    Retorna:
        bool: True se a atualização foi bem-sucedida, False caso contrário
    """
    try:
        from utils.newrelic_advanced_collector import collect_full_data
        from utils.entity_processor import filter_entities_with_data
        
        logger.info("Iniciando atualização do cache com o coletor avançado...")
        
        # Coleta completa usando o coletor avançado
        resultado = await collect_full_data()
        
        if not resultado or "erro" in resultado:
            logger.error(f"Erro na coleta de dados avançados: {resultado.get('erro', 'Desconhecido')}")
            return False
        
        # Recupera e filtra as entidades
        entidades_raw = resultado.get("entidades", [])
        
        logger.info(f"Coletadas {len(entidades_raw)} entidades brutas. Filtrando...")
        
        # Filtra entidades com dados reais
        entidades_filtradas = filter_entities_with_data(entidades_raw)
        
        logger.info(f"Filtradas {len(entidades_filtradas)} entidades válidas de {len(entidades_raw)} totais")
        
        # Substitui as entidades filtradas no resultado
        resultado["entidades"] = entidades_filtradas
        resultado["timestamp_atualizacao"] = datetime.now().isoformat()
        
        # Verifica se o diretório existe
        CACHE_HISTORICO_DIR.mkdir(parents=True, exist_ok=True)
        
        # Salva em disco
        async with aiofiles.open(CACHE_FILE, "w", encoding="utf-8") as f:
            await f.write(json.dumps(resultado, ensure_ascii=False, indent=2))
        
        # Atualiza o cache em memória
        global _cache
        _cache["dados"] = resultado
        _cache["metadados"]["ultima_atualizacao"] = resultado["timestamp_atualizacao"]
        _cache["metadados"]["tipo_ultima_atualizacao"] = "avançada"

        # Atualiza o campo coverage no cache
        try:
            atualizar_coverage_cache()
        except Exception as e:
            logger.error(f"Erro ao atualizar coverage após coleta avançada: {e}")

        logger.info(f"Cache atualizado com dados avançados e salvo em: {CACHE_FILE}")
        logger.info(f"Entidades por domínio: {resultado.get('contagem_por_dominio', {})}")

        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar cache com dados avançados: {str(e)}", exc_info=True)
        return False

async def atualizar_cache_incremental(coletar_contexto_fn, filtro=None):
    """
    Atualiza apenas partes específicas do cache com base em filtros.
    Implementação robusta que permite atualizações parciais mais eficientes.
    
    Args:
        filtro: Dicionário com critérios para atualização parcial, exemplos:
               {"domain": "APM"} - Atualiza apenas entidades APM
               {"guid": "abc123"} - Atualiza apenas uma entidade específica
               {"tipo": "ERRO"} - Atualiza apenas entidades com erro
               {"periodo": "30min"} - Atualiza apenas métricas dos últimos 30 minutos
    """
    logger.info(f"Iniciando atualização incremental do cache com filtro: {filtro}")
    try:
        # Se o cache ainda não foi inicializado ou filtro não fornecido
        if not _cache["dados"] or not filtro:
            logger.info("Cache vazio ou sem filtro, realizando atualização completa")
            return await atualizar_cache_completo(coletar_contexto_fn)
        
        # Guarda o cache atual como backup
        cache_atual = _cache["dados"].copy()
        
        # Determina o tipo de atualização baseado no filtro
        if "domain" in filtro:
            # Atualização de um domínio específico
            dominio = filtro["domain"]
            logger.info(f"Atualizando apenas o domínio: {dominio}")
            
            # Coleta apenas dados do domínio específico
            try:
                # Esta função deve ser implementada no coletor para suportar coleta parcial
                from utils.newrelic_collector import coletar_dominio_especifico
                novo_dados = await coletar_dominio_especifico(dominio)
                
                if novo_dados and novo_dados.get("entidades"):
                    # Substitui entidades apenas do domínio específico
                    entidades_atualizadas = []
                    
                    # Mantém entidades de outros domínios
                    for e in _cache["dados"].get("entidades", []):
                        if e.get("domain") != dominio:
                            entidades_atualizadas.append(e)
                    
                    # Adiciona novas entidades do domínio atualizado
                    entidades_atualizadas.extend(novo_dados["entidades"])
                    
                    # Atualiza o cache
                    _cache["dados"]["entidades"] = entidades_atualizadas
                    _cache["metadados"]["ultima_atualizacao_parcial"] = datetime.now().isoformat()
                    _cache["metadados"]["tipo_ultima_atualizacao"] = f"incremental_dominio_{dominio}"
                    
                    # Salva em disco
                    await salvar_cache_no_disco()
                    logger.info(f"Cache atualizado incrementalmente para domínio {dominio}")
                    return True
                else:
                    logger.warning(f"Não foi possível coletar dados para o domínio {dominio}")
            except ImportError:
                logger.warning("Função coletar_dominio_especifico não implementada, usando fallback")
                # Fallback para atualização completa
                return await atualizar_cache_completo(coletar_contexto_fn)
        
        elif "guid" in filtro:
            # Atualização de uma entidade específica
            guid = filtro["guid"]
            logger.info(f"Atualizando apenas a entidade com GUID: {guid}")
            
            try:
                # Esta função deve ser implementada no coletor
                from utils.newrelic_collector import coletar_entidade_especifica
                nova_entidade = await coletar_entidade_especifica(guid)
                
                if nova_entidade:
                    # Substitui ou adiciona a entidade no cache
                    entidades_atualizadas = []
                    entidade_encontrada = False
                    
                    # Procura e substitui a entidade específica
                    for e in _cache["dados"].get("entidades", []):
                        if e.get("guid") == guid:
                            entidades_atualizadas.append(nova_entidade)
                            entidade_encontrada = True
                        else:
                            entidades_atualizadas.append(e)
                    
                    # Se não encontrou, adiciona como nova entidade
                    if not entidade_encontrada:
                        entidades_atualizadas.append(nova_entidade)
                    
                    # Atualiza o cache
                    _cache["dados"]["entidades"] = entidades_atualizadas
                    _cache["metadados"]["ultima_atualizacao_parcial"] = datetime.now().isoformat()
                    _cache["metadados"]["tipo_ultima_atualizacao"] = f"incremental_entidade_{guid}"
                    
                    # Salva em disco
                    await salvar_cache_no_disco()
                    logger.info(f"Cache atualizado incrementalmente para entidade {guid}")
                    return True
                else:
                    logger.warning(f"Não foi possível coletar dados para a entidade {guid}")
            except ImportError:
                logger.warning("Função coletar_entidade_especifica não implementada, usando fallback")
                # Fallback para atualização completa
                return await atualizar_cache_completo(coletar_contexto_fn)
        
        # Se o tipo de filtro não é suportado, faz atualização completa
        logger.info(f"Filtro não suportado completamente: {filtro}, realizando atualização completa")
        return await atualizar_cache_completo(coletar_contexto_fn)
        
    except Exception as e:
        logger.error(f"Erro na atualização incremental: {e}")
        logger.error(traceback.format_exc())
        # Em caso de falha, restaura o cache anterior
        _cache["dados"] = cache_atual
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
                # Usar o coletor avançado se configurado
                if USAR_COLETOR_AVANCADO:
                    logger.info("Usando coletor avançado para atualização do cache (100% dos dados do New Relic)")
                    sucesso = await atualizar_cache_completo_avancado()
                else:
                    logger.info("Usando coletor padrão para atualização do cache")
                    sucesso = await atualizar_cache_completo(coletar_contexto_fn)
                    
                if not sucesso:
                    logger.warning("Falha na atualização do cache. Mantendo dados antigos até próxima tentativa.")
                logger.info(f"Próxima atualização programada para {CACHE_UPDATE_INTERVAL/3600} horas depois")
        except Exception as e:
            logger.error(f"Erro no loop de atualização: {e}")
            logger.error(traceback.format_exc())
        await asyncio.sleep(3600)  # Checa a cada hora, mas só atualiza se passou 24h

def diagnosticar_cache():
    """
    Diagnóstico detalhado do estado do cache com métricas avançadas.
    Inclui estatísticas de acesso, saúde do cache e qualidade dos dados.
    """
    logger.info("Realizando diagnóstico detalhado do cache.")
    
    # Estatísticas básicas
    estatisticas = {
        "total_chaves_dados": len(_cache["dados"]) if _cache["dados"] else 0,
        "chaves_dados": list(_cache["dados"].keys()) if _cache["dados"] else [],
        "metadados": _cache["metadados"],
        "total_consultas_historicas": len(_cache["consultas_historicas"]),
        "tamanho_disco_mb": 0,
        "ultima_atualizacao": _cache["metadados"]["ultima_atualizacao"],
        "status": "não inicializado",
        "performance": {},
        "qualidade_dados": {},
        "arquivos_cache": {}
    }
    
    # Verifica tamanho e existência de todos os arquivos de cache
    arquivos_cache = {
        "principal": CACHE_FILE,
        "consultas": CACHE_CONSULTA_DIR,
        "rapido": CACHE_SHORT_FILE,
        "longo": CACHE_LONG_FILE
    }
    
    tamanho_total = 0
    for nome, arquivo in arquivos_cache.items():
        if isinstance(arquivo, Path) and arquivo.exists():
            if arquivo.is_file():
                tamanho = arquivo.stat().st_size / (1024 * 1024)  # MB
                estatisticas["arquivos_cache"][nome] = {
                    "existe": True,
                    "tamanho_mb": round(tamanho, 2),
                    "modificado": datetime.fromtimestamp(arquivo.stat().st_mtime).isoformat()
                }
                tamanho_total += tamanho
            elif arquivo.is_dir():
                arquivos = list(arquivo.glob("*"))
                tamanho = sum(f.stat().st_size for f in arquivos if f.is_file()) / (1024 * 1024)
                estatisticas["arquivos_cache"][nome] = {
                    "existe": True,
                    "total_arquivos": len(arquivos),
                    "tamanho_mb": round(tamanho, 2),
                    "ultimo_arquivo": max([f.stat().st_mtime for f in arquivos]) if arquivos else None
                }
                tamanho_total += tamanho
        else:
            estatisticas["arquivos_cache"][nome] = {
                "existe": False
            }
    
    estatisticas["tamanho_disco_mb"] = round(tamanho_total, 2)
    
    if CACHE_FILE.exists():
        estatisticas["status"] = "carregado"
    
    # Verifica idade e validade do cache
    if _cache["metadados"]["ultima_atualizacao"]:
        ultima_atualizacao = datetime.fromisoformat(_cache["metadados"]["ultima_atualizacao"])
        idade_segundos = (datetime.now() - ultima_atualizacao).total_seconds()
        estatisticas["idade_horas"] = round(idade_segundos / 3600, 2)
        estatisticas["idade_minutos"] = round(idade_segundos / 60, 2)
        estatisticas["atualizado"] = idade_segundos < CACHE_UPDATE_INTERVAL
        
        # Classifica o status de atualização
        if idade_segundos < CACHE_SHORT_INTERVAL:
            estatisticas["status_atualizacao"] = "tempo_real"
        elif idade_segundos < CACHE_UPDATE_INTERVAL:
            estatisticas["status_atualizacao"] = "recente"
        elif idade_segundos < CACHE_LONG_INTERVAL:
            estatisticas["status_atualizacao"] = "defasado"
        else:
            estatisticas["status_atualizacao"] = "obsoleto"
    
    # Estatísticas de entidades e domínios
    if _cache["dados"] and "entidades" in _cache["dados"]:
        entidades = _cache["dados"]["entidades"]
        total_entidades = len(entidades)
        estatisticas["total_entidades"] = total_entidades
        
        # Contagem por domínio
        dominios = {}
        for e in entidades:
            domain = e.get("domain", "desconhecido")
            dominios[domain] = dominios.get(domain, 0) + 1
        
        estatisticas["contagem_por_dominio"] = dominios
        
        # Estatísticas de qualidade de dados
        entidades_com_metricas = sum(1 for e in entidades if e.get("metricas"))
        entidades_com_erros = sum(1 for e in entidades if e.get("metricas", {}).get("30min", {}).get("recent_error"))
        
        # Calcular taxa de preenchimento de métricas críticas
        metricas_criticas = ["apdex", "response_time_max", "throughput", "error_rate"]
        preenchimento_metricas = {}
        
        for metrica in metricas_criticas:
            tem_metrica = sum(1 for e in entidades 
                             if e.get("metricas", {}).get("30min", {}).get(metrica))
            taxa = (tem_metrica / total_entidades) if total_entidades > 0 else 0
            preenchimento_metricas[metrica] = round(taxa * 100, 1)
        
        estatisticas["qualidade_dados"] = {
            "entidades_com_metricas_percent": round((entidades_com_metricas / total_entidades) * 100 if total_entidades > 0 else 0, 1),
            "entidades_com_erros_percent": round((entidades_com_erros / total_entidades) * 100 if total_entidades > 0 else 0, 1),
            "preenchimento_metricas": preenchimento_metricas,
            "saude_geral": "boa" if entidades_com_metricas > total_entidades * 0.8 else 
                          ("media" if entidades_com_metricas > total_entidades * 0.5 else "baixa")
        }
        
        # Desempenho e uso do cache
        # Esta parte será simulada pois não temos contadores reais
        cache_hits = _cache["metadados"].get("cache_hits", 0)
        cache_misses = _cache["metadados"].get("cache_misses", 0)
        total_acessos = cache_hits + cache_misses
        
        estatisticas["performance"] = {
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "hit_rate": round((cache_hits / total_acessos) * 100 if total_acessos > 0 else 0, 1),
            "tempo_medio_acesso_ms": _cache["metadados"].get("tempo_medio_acesso_ms", 0),
            "economia_estimada_consultas": cache_hits  # Cada hit evita uma consulta à API
        }
    
    return estatisticas

async def forcar_atualizacao_cache(coletar_contexto_fn):
    """Força uma atualização imediata do cache."""
    logger.info("Solicitada atualização forçada do cache")
    _cache["metadados"]["atualizacao_forcada"] = True
    
    # Usar o coletor avançado se configurado
    if USAR_COLETOR_AVANCADO:
        logger.info("Usando coletor avançado para atualização forçada (100% dos dados do New Relic)")
        return await atualizar_cache_completo_avancado()
    else:
        logger.info("Usando coletor padrão para atualização forçada")
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
    if USAR_COLETOR_AVANCADO:
        return await atualizar_cache_completo_avancado()
    else:
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

async def invalidar_cache_seletivo(criterio, coletar_contexto_fn=None):
    """
    Invalida e atualiza seletivamente partes do cache com base em critérios específicos.
    Útil para casos como novos alertas ou deploys que afetam apenas partes do sistema.
    
    Args:
        criterio: Dicionário com critérios para invalidação, exemplos:
                {"entidade": "nome_aplicacao"} - Invalida apenas uma entidade
                {"alerta": "id_alerta"} - Invalida entidades relacionadas a um alerta
                {"dominio": "APM"} - Invalida todas as entidades de um domínio
        coletar_contexto_fn: Função opcional para coletar novos dados após invalidação
    
    Returns:
        bool: True se a invalidação foi bem-sucedida, False caso contrário
    """
    logger.info(f"Iniciando invalidação seletiva do cache: {criterio}")
    try:
        if not _cache["dados"] or not criterio:
            logger.warning("Cache vazio ou critério não fornecido")
            return False
            
        # Invalida cache com base no tipo de critério
        if "entidade" in criterio:
            nome_entidade = criterio["entidade"]
            logger.info(f"Invalidando cache para entidade: {nome_entidade}")
            
            # Procura a entidade pelo nome
            for i, entidade in enumerate(_cache["dados"].get("entidades", [])):
                if entidade.get("name") == nome_entidade:
                    # Marca como desatualizada
                    _cache["dados"]["entidades"][i]["cache_valido"] = False
                    _cache["dados"]["entidades"][i]["ultima_atualizacao"] = None
                    
                    # Se houver função coletora, atualiza apenas esta entidade
                    if coletar_contexto_fn:
                        logger.info(f"Atualizando dados da entidade: {nome_entidade}")
                        filtro = {"guid": entidade.get("guid")} if entidade.get("guid") else {"name": nome_entidade}
                        await atualizar_cache_incremental(coletar_contexto_fn, filtro)
                    
                    await salvar_cache_no_disco()
                    return True
            
            logger.warning(f"Entidade não encontrada no cache: {nome_entidade}")
            return False
            
        elif "dominio" in criterio:
            dominio = criterio["dominio"]
            logger.info(f"Invalidando cache para domínio: {dominio}")
            
            # Marca todas as entidades do domínio como desatualizadas
            entidades_afetadas = 0
            for i, entidade in enumerate(_cache["dados"].get("entidades", [])):
                if entidade.get("domain") == dominio:
                    _cache["dados"]["entidades"][i]["cache_valido"] = False
                    _cache["dados"]["entidades"][i]["ultima_atualizacao"] = None
                    entidades_afetadas += 1
            
            # Se houver função coletora, atualiza o domínio
            if coletar_contexto_fn and entidades_afetadas > 0:
                logger.info(f"Atualizando dados do domínio: {dominio}")
                await atualizar_cache_incremental(coletar_contexto_fn, {"domain": dominio})
            
            await salvar_cache_no_disco()
            return entidades_afetadas > 0
            
        elif "alerta" in criterio:
            id_alerta = criterio["alerta"]
            logger.info(f"Invalidando cache para entidades relacionadas ao alerta: {id_alerta}")
            
            # Localiza o alerta específico
            alerta_encontrado = None
            for alerta in _cache["dados"].get("alertas", []):
                if alerta.get("id") == id_alerta:
                    alerta_encontrado = alerta
                    break
                    
            if not alerta_encontrado:
                logger.warning(f"Alerta não encontrado no cache: {id_alerta}")
                return False
                
            # Invalida entidades relacionadas ao alerta
            entidade_alerta = alerta_encontrado.get("entidade")
            if entidade_alerta:
                # Chama recursivamente para invalidar a entidade
                return await invalidar_cache_seletivo({"entidade": entidade_alerta}, coletar_contexto_fn)
            
        logger.warning(f"Critério de invalidação não suportado: {criterio}")
        return False
        
    except Exception as e:
        logger.error(f"Erro ao invalidar cache seletivamente: {e}")
        logger.error(traceback.format_exc())
        return False

async def _initialize_cache(force=False):
    """
    Inicializa o cache garantindo que esteja carregado em memória.
    
    Args:
        force: Se True, força o carregamento do cache mesmo que já esteja carregado
    
    Returns:
        bool: True se bem sucedido, False caso contrário
    """
    global _cache
    
    try:
        # Se o cache já estiver inicializado e não forçarmos, não fazemos nada
        if _cache["dados"] and not force:
            logger.debug("Cache já inicializado")
            return True
        
        # Carrega o cache do disco
        success = await carregar_cache_do_disco()
        
        # Se não conseguir carregar do disco, tenta inicializar vazio
        if not success:
            logger.warning("Não foi possível carregar cache do disco, inicializando vazio")
            _cache["dados"] = {
                "timestamp": datetime.now().isoformat(),
                "entidades": [],
                "contagem_por_dominio": {}
            }
            
            # Tenta criar o arquivo de cache vazio
            os.makedirs(CACHE_HISTORICO_DIR, exist_ok=True)
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(_cache["dados"], f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar cache: {e}")
        return False

# Versão síncrona do get_cache para uso em contextos não-async
def get_cache_sync():
    """
    Versão síncrona de get_cache para contextos não-async.
    Retorna o cache atual sem verificar atualizações.
    
    Returns:
        dict: Conteúdo atual do cache
    """
    global _cache
    
    # Se o cache não estiver carregado, carrega do disco de forma síncrona
    if not _cache["dados"]:
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    dados_carregados = json.load(f)
                    _cache["dados"] = dados_carregados
                    _cache["metadados"]["ultima_atualizacao"] = dados_carregados.get("timestamp")
                    logger.info(f"Cache carregado de forma síncrona. Timestamp: {_cache['metadados']['ultima_atualizacao']}")
        except Exception as e:
            logger.error(f"Erro ao carregar cache síncrono: {e}")
    
    return _cache["dados"]