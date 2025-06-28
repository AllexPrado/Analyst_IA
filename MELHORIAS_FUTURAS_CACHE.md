# MELHORIAS FUTURAS DO SISTEMA DE CACHE

Este documento descreve as melhorias adicionais que podem ser implementadas no sistema de cache do Analyst IA para aumentar seu desempenho, confiabilidade e funcionalidade.

## 1. Atualização Incremental Real

Atualmente, a função `atualizar_cache_incremental` em `cache_advanced.py` usa um fallback para atualização completa. Uma implementação real da atualização incremental deve:

- Atualizar apenas as entidades selecionadas pelo filtro
- Preservar os dados das outras entidades
- Atualizar apenas métricas específicas, se necessário
- Manter um histórico de atualizações incrementais

### Implementação Proposta

```python
async def atualizar_cache_incremental(filtro=None):
    """
    Atualiza o cache de forma incremental, apenas para entidades específicas.
    
    Args:
        filtro: Filtro para selecionar as entidades que serão atualizadas
            
    Returns:
        bool: True se a atualização foi bem-sucedida, False caso contrário
    """
    logger.info(f"Iniciando atualização incremental do cache com filtro: {filtro}")
    
    try:
        # Obter o cache atual
        cache_atual = await get_cache(forcar_atualizacao=False)
        
        # Se o cache estiver vazio, faz uma atualização completa
        if not cache_atual or not cache_atual.get("entidades"):
            logger.info("Cache vazio, realizando atualização completa")
            return await atualizar_cache_completo(coletar_contexto_completo_avancado)
        
        # Selecionar entidades que correspondem ao filtro
        entidades_atuais = cache_atual.get("entidades", [])
        entidades_para_atualizar = []
        indices_entidades = {}
        
        # Aplicar filtros e guardar índices para atualização
        for i, entidade in enumerate(entidades_atuais):
            if corresponde_ao_filtro(entidade, filtro):
                entidades_para_atualizar.append(entidade)
                indices_entidades[entidade.get("guid")] = i
        
        # Se não houver entidades para atualizar, retorna False
        if not entidades_para_atualizar:
            logger.warning(f"Nenhuma entidade corresponde ao filtro: {filtro}")
            return False
        
        # Coletar dados atualizados apenas para as entidades selecionadas
        dados_atualizados = await coletar_dados_incrementais(entidades_para_atualizar)
        
        # Criar uma cópia do cache atual para atualização
        novo_cache = cache_atual.copy()
        novas_entidades = novo_cache.get("entidades", []).copy()
        
        # Atualizar apenas as entidades selecionadas
        for entidade_atualizada in dados_atualizados:
            guid = entidade_atualizada.get("guid")
            if guid in indices_entidades:
                # Substituir a entidade no índice correto
                novas_entidades[indices_entidades[guid]] = entidade_atualizada
        
        # Atualizar o cache com as novas entidades
        novo_cache["entidades"] = novas_entidades
        novo_cache["timestamp"] = datetime.now().isoformat()
        
        # Salvar o cache atualizado
        await salvar_cache_no_disco(novo_cache)
        
        # Atualizar o cache em memória
        global _cache
        _cache["dados"] = novo_cache
        _cache["metadados"]["ultima_atualizacao"] = novo_cache["timestamp"]
        _cache["metadados"]["tipo_ultima_atualizacao"] = "incremental"
        
        logger.info(f"Atualização incremental concluída: {len(entidades_para_atualizar)} entidades atualizadas")
        return True
    except Exception as e:
        logger.error(f"Erro na atualização incremental: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
```

## 2. Compressão do Cache

Para reduzir o uso de disco e melhorar a performance de I/O:

```python
async def salvar_cache_no_disco_comprimido(dados_cache):
    """Salva o cache no disco com compressão."""
    try:
        import gzip
        
        # Garantir que os diretórios existem
        os.makedirs(CACHE_HISTORICO_DIR, exist_ok=True)
        
        # Converter para JSON
        dados_json = json.dumps(dados_cache, ensure_ascii=False)
        
        # Comprimir e salvar
        async with aiofiles.open(CACHE_FILE_COMPRESSED, 'wb') as f:
            await f.write(gzip.compress(dados_json.encode('utf-8')))
            
        logger.info(f"Cache comprimido salvo em {CACHE_FILE_COMPRESSED}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar cache comprimido: {e}")
        return False
```

## 3. Sistema de Métricas de Desempenho

Implementar métricas para monitorar o desempenho do cache:

```python
class CacheMetrics:
    def __init__(self):
        self.hit_count = 0
        self.miss_count = 0
        self.update_count = 0
        self.update_time_total = 0
        self.query_time_total = 0
        self.query_count = 0
        self.last_update = None
        
    def record_hit(self):
        self.hit_count += 1
        
    def record_miss(self):
        self.miss_count += 1
    
    def record_update(self, duration_seconds):
        self.update_count += 1
        self.update_time_total += duration_seconds
        self.last_update = datetime.now()
    
    def record_query(self, duration_seconds):
        self.query_count += 1
        self.query_time_total += duration_seconds
    
    def get_hit_ratio(self):
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0
        return self.hit_count / total
    
    def get_avg_update_time(self):
        if self.update_count == 0:
            return 0
        return self.update_time_total / self.update_count
    
    def get_avg_query_time(self):
        if self.query_count == 0:
            return 0
        return self.query_time_total / self.query_count
    
    def to_dict(self):
        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_ratio": self.get_hit_ratio(),
            "update_count": self.update_count,
            "avg_update_time": self.get_avg_update_time(),
            "avg_query_time": self.get_avg_query_time(),
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
```

## 4. Cache Hierárquico

Implementar um sistema de cache em camadas para melhorar a performance:

1. **Memória**: Cache em memória para acesso rápido
2. **Disco**: Persistência em disco para dados completos
3. **Redis** (opcional): Cache distribuído para deployment em múltiplos servidores

```python
class CacheHierarquico:
    def __init__(self):
        self.memory_cache = {}
        self.redis_client = None
        
    async def get(self, key, nivel="memoria"):
        # Tenta primeiro na memória
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # Se não encontrado e nivel > memória, tenta no disco
        if nivel in ["disco", "redis"]:
            # Carrega do disco
            # ...
            
        # Se não encontrado e nivel > disco, tenta no Redis
        if nivel == "redis" and self.redis_client:
            # Carrega do Redis
            # ...
            
        return None
```

## 5. Testes Automatizados

Desenvolver testes unitários e de integração para o sistema de cache:

### 5.1. Testes Unitários

```python
def test_verificar_integridade_cache():
    """Testa a verificação de integridade do cache."""
    # Criar um cache de teste
    cache_teste = {
        "timestamp": datetime.now().isoformat(),
        "entidades": [
            {"guid": "1", "name": "Entidade 1", "domain": "APM", "dados": {"metricas": []}},
            {"guid": "2", "name": "Entidade 2", "domain": "BROWSER", "dados": {"metricas": []}}
        ]
    }
    
    # Salvar o cache de teste
    salvar_cache_no_disco(cache_teste)
    
    # Verificar integridade
    resultado = verificar_integridade_cache()
    
    # Verificar resultados
    assert resultado["integridade"] is True
    assert resultado["total_entidades"] == 2
    assert "APM" in resultado["entidades_por_dominio"]
    assert resultado["entidades_por_dominio"]["APM"] == 1
```

### 5.2. Testes de Integração

```python
async def test_integracao_cache_sistema():
    """Teste de integração do cache com o sistema."""
    # Inicializar o sistema de cache
    resultado = await inicializar_sistema_cache()
    assert resultado is True
    
    # Obter dados do cache
    cache = await get_cache(forcar_atualizacao=False)
    assert cache is not None
    assert "entidades" in cache
    
    # Fazer uma consulta que usa o cache
    resposta = await processar_consulta_ia("Mostrar estatísticas de performance da aplicação XYZ")
    assert resposta is not None
```

## 6. Monitoramento e Telemetria

Adicionar telemetria para monitorar o sistema de cache em produção:

```python
def registrar_telemetria_cache(evento, dados=None):
    """Registra eventos de telemetria do cache."""
    try:
        dados_telemetria = {
            "timestamp": datetime.now().isoformat(),
            "evento": evento,
            "dados": dados or {}
        }
        
        # Registrar no arquivo de log de telemetria
        with open(TELEMETRIA_LOG, "a") as f:
            f.write(json.dumps(dados_telemetria) + "\n")
        
        # Se configurado, enviar para sistema externo de monitoramento
        if ENVIAR_TELEMETRIA:
            # Implementar envio para sistema externo
            pass
    except Exception as e:
        logger.error(f"Erro ao registrar telemetria: {e}")
```

## 7. Implementação de TTL (Time-to-Live) por Entidade

Definir tempos de vida diferentes para diferentes tipos de dados no cache:

```python
TTL_CONFIG = {
    "APM": 24 * 60 * 60,  # 24 horas para dados de APM
    "BROWSER": 12 * 60 * 60,  # 12 horas para dados de Browser
    "MOBILE": 24 * 60 * 60,  # 24 horas para dados de Mobile
    "SYNTHETICS": 6 * 60 * 60,  # 6 horas para dados de Synthetic
    "DEFAULT": 24 * 60 * 60  # Valor padrão
}

def verificar_ttl_entidade(entidade):
    """Verifica se uma entidade excedeu seu TTL."""
    try:
        # Obter timestamp da última atualização da entidade
        timestamp_str = entidade.get("ultima_atualizacao")
        if not timestamp_str:
            return True  # Se não tem timestamp, considerar expirado
            
        timestamp = datetime.fromisoformat(timestamp_str)
        
        # Obter TTL para o domínio da entidade
        dominio = entidade.get("domain", "").upper()
        ttl = TTL_CONFIG.get(dominio, TTL_CONFIG["DEFAULT"])
        
        # Verificar se expirou
        agora = datetime.now()
        diferenca = (agora - timestamp).total_seconds()
        
        return diferenca > ttl
    except Exception:
        return True  # Em caso de erro, considerar expirado
```

## 8. Conclusão

Estas melhorias levarão o sistema de cache do Analyst IA ao próximo nível, garantindo:

- **Melhor desempenho** através de compressão e cache hierárquico
- **Menor uso de recursos** através de atualizações incrementais
- **Maior confiabilidade** através de testes automatizados
- **Melhor visibilidade** através de métricas e telemetria

Recomenda-se implementar estas melhorias de forma gradual, começando pelas mais críticas: atualização incremental, compressão e testes automatizados.
