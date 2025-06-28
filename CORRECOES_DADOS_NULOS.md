# Correções de Dados Nulos no Analyst-IA

Este documento detalha as principais correções implementadas para resolver o problema de dados nulos e respostas genéricas no Analyst-IA.

## Problemas Corrigidos

1. **Qualidade de dados no cache**:
   - Entidades sem métricas reais estavam sendo exibidas no frontend
   - Cache armazenava e servia entidades "vazias"
   - IA recebia dados de baixa qualidade para análise

2. **Filtragem inadequada**:
   - Entidades sem métricas úteis não eram filtradas adequadamente
   - Frontend recebia dados nulos que resultavam em "N/A"
   - Chat IA não tinha informações suficientes para análises específicas

3. **Prompt inadequado para IA**:
   - Poucos dados técnicos sendo enviados à IA
   - Faltava contexto específico sobre métrica
   - System prompt não orientava adequadamente a IA

## Soluções Implementadas

### 1. Processador de Entidades Aprimorado

- Implementação de validação rigorosa de entidades:

```python
def is_entity_valid(entity: Dict) -> bool:
    # Verificação rigorosa de dados reais nas métricas
    has_real_data = False
    for period, metrics in entity.get('metricas', {}).items():
        # Verifica todas as métricas do período
        for metric_name, metric_data in metrics.items():
            # Verifica dados não-nulos
            if has_real_data:
                break
    # ...
```

- Filtragem melhorada para garantir apenas dados de qualidade:

```python
def filter_entities_with_data(entities: List[Dict]) -> List[Dict]:
    # Verificação pré-validação (estatísticas)
    if processed and processed.get('metricas'):
        # Coleta estatísticas de métricas disponíveis
        pass
    # ...
```

- Nova função para limpar entidades inválidas no cache:

```python
async def limpar_cache_de_entidades_invalidas():
    """
    Limpa o cache, removendo entidades sem dados válidos.
    """
    entidades_validas = filter_entities_with_data(_cache["dados"]["entidades"])
    _cache["dados"]["entidades"] = entidades_validas
    # ...
```

- Integração da limpeza no fluxo de atualização do cache:

```python
async def atualizar_cache_completo(coletar_contexto_fn):
    # Filtra entidades inválidas
    if entidades_originais:
        entidades_validas = filter_entities_with_data(entidades_originais)
        contexto['entidades'] = entidades_validas
    # ...
```

- Garantia de dados de qualidade para a IA:

```python
async def chat_endpoint(input: ChatInput):
    # Primeiro, limpa o cache de entidades inválidas
    entidades_removidas = await limpar_cache_de_entidades_invalidas()
    # Garante que as entidades sejam filtradas
    entidades = filter_entities_with_data(entidades_originais)
    # ...
```

- Prompt detalhado com dados relevantes:

```python
# Resumo detalhado do diagnóstico para IA
diagnostico_detalhado = []
apdex = safe_first(e.get('metricas',{}).get('30min',{}).get('apdex',[]),{}).get('score')
latencia = safe_first(e.get('metricas',{}).get('30min',{}).get('response_time_max',[]),{}).get('max.duration')
# ...
```

- System prompt técnico e específico:

```python
system_prompt = """
Você é um SRE sênior especialista em New Relic com profundo conhecimento técnico em:

1. Análise de métricas de APM, Browser, e infraestrutura
2. Consultas NRQL e dashboards analíticos
3. Troubleshooting de problemas de performance
4. Otimização de SLAs e SLOs

REGRAS:
- Responda APENAS baseado nos dados fornecidos
- Nunca invente dados ou métricas que não foram fornecidos
- Seja técnico, específico e direto
"""
```

## Resultados Esperados

1. **Frontend sem dados N/A**:
   - Componentes recebem apenas entidades com dados reais
   - Cards e gráficos exibem informações relevantes

2. **Chat IA com respostas técnicas**:
   - IA recebe dados específicos e detalhados
   - Respostas contêm referências às métricas reais
   - Incluem consultas NRQL relevantes quando apropriado

3. **Cache otimizado**:
   - Armazenamento apenas de entidades com valor analítico
   - Validação de qualidade antes de salvar

## Testes Implementados

1. `test_data_quality.py`: Verifica a qualidade dos dados no backend
2. `test_chat.py`: Testa o chat com diferentes cenários

## Próximos Passos

1. Monitorar a qualidade dos dados após as correções
2. Refinar as regras de validação conforme feedback
3. Implementar mais testes automatizados
4. Documentar métricas e dados válidos para referência
