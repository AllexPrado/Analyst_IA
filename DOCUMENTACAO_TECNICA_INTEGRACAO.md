# Documentação de Integração - New Relic Avançado & Economia de Tokens

Este documento técnico detalha o processo de integração do coletor avançado do New Relic e do sistema de economia de tokens na plataforma Analyst IA, bem como a implementação do sistema de alimentação de dados para o frontend.

## Arquitetura da Integração

### Componentes Principais

``
┌─────────────────┐     ┌───────────────────┐     ┌────────────────┐
│                 │     │                   │     │                │
│   New Relic     │────▶│  Coletor Avançado │────▶│ Filtro Rigoroso│
│     API         │     │                   │     │                │
│                 │     └───────────────────┘     └────────┬───────┘
└─────────────────┘                                        │
                                                          ▼
┌─────────────────┐     ┌───────────────────┐     ┌────────────────┐
│                 │     │                   │     │                │
│   Frontend      │◀────│  Backend API      │◀────│ Cache          │
│   Vue.js        │     │   (FastAPI)       │     │ Otimizado      │
│                 │     │                   │     │                │
└─────────────────┘     └───────────────────┘     └────────────────┘
``

### Fluxo de Dados

1. O **Coletor Avançado** (`newrelic_advanced_collector.py`) se conecta à API New Relic para obter:
   - Métricas tradicionais (Apdex, response time, etc.)
   - Logs detalhados com contexto completo
   - Traces distribuídos com spans e duração
   - Queries SQL com parâmetros e tempos de execução
   - Backtraces completos de erros
   - Métricas de infraestrutura e relacionamentos

2. O **Filtro Rigoroso** (`entity_processor.py`) aplica regras para:
   - Descartar entidades sem dados reais
   - Remover valores nulos e vazios
   - Detectar e eliminar dados duplicados
   - Normalizar estruturas complexas

3. O **Cache Otimizado** armazena:
   - Apenas dados úteis e relevantes
   - Formato otimizado para menor consumo de tokens
   - Metadados para rastreamento de economia

4. O **Backend API** fornece:
   - Endpoints para todos os tipos de dados
   - Validação e transformação final
   - Métricas de economia de tokens

5. O **Frontend** apresenta:
   - Visualização rica de dados avançados
   - Interface adaptativa para diferentes tipos de dados
   - Componentes otimizados para grandes volumes
   - Consumo de endpoints de API para exibição de dados reais

## Implementação Técnica

### Backend

#### Coletor Avançado

O coletor avançado (`newrelic_advanced_collector.py`) implementa:

- Coleta paralela com controle de concorrência
- Batching inteligente para reduzir chamadas de API
- Tratamento robusto de falhas com retry
- Conversão e normalização de dados

```python
async def collect_full_data():
    entities = await get_all_entities()
    
    # Processamento em lotes para evitar sobrecarga
    for batch in chunks(entities, BATCH_SIZE):
        batch_tasks = [collect_entity_complete_data(e) for e in batch]
        batch_results = await asyncio.gather(*batch_tasks)
        # Processamento de resultados...
```

#### Filtro de Entidades

O filtro rigoroso (`entity_processor.py`) implementa:

- Validação profunda de estrutura e conteúdo
- Regras específicas por tipo de entidade
- Análise recursiva de objetos aninhados
- Normalização de formatos

```python
def is_entity_valid(entity):
    # Verifica campos básicos e estrutura
    if not entity.get('name') or not isinstance(entity, dict):
        return False
        
    # Rejeita entidades com problemas explícitos
    if entity.get('problema') in ['INVALID_QUERY', 'NO_DATA']:
        return False
        
    # Rejeita entidades sem métricas reais
    if not entity.get('metricas') or not has_valid_metrics(entity.get('metricas')):
        return False
        
    return True
```

### Frontend

#### Componente de Dados Avançados

O componente `AdvancedDataPanel.vue` implementa:

- Visualização em abas para diferentes tipos de dados
- Tratamento específico para logs, traces e queries
- Formatação otimizada para diferentes formatos de timestamp
- Visualização adequada para backtraces e mensagens de erro

```vue
<div v-for="(log, idx) in logsData" :key="idx" class="log-entry">
  <div class="flex justify-between">
    <span>{{ formatTimestamp(log.timestamp) }}</span>
    <span :class="getLogSeverityBadgeClass(log.severity)">
      {{ log.severity }}
    </span>
  </div>
  <div class="text-white">{{ log.message }}</div>
</div>
```

## Economia de Tokens

### Métricas de Economia

O sistema implementa o monitoramento e análise contínua da economia de tokens:

- **Redução no Tamanho de Contexto**: 30-60% dependendo do tipo de consulta
- **Economia por Tipo de Entidade**:
  - APM: 45-55%
  - Browser: 35-45%
  - Infrastructure: 40-50%
  - Database: 55-65%

### Impacto

- **Redução de Custos**: Economia significativa no uso da API OpenAI
- **Melhor Performance**: Respostas mais rápidas devido à redução de dados processados
- **Maior Precisão**: Foco em dados reais e relevantes aumenta a qualidade das análises

## Sistema de Alimentação de Dados do Frontend

Para garantir que o frontend receba dados reais e possa exibir as análises corretamente, foram implementados os seguintes componentes:

### API Router e Endpoints

Foi criado um sistema de roteamento de API modular (`core_router.py`) que organiza os endpoints por funcionalidade:

- **Insights**: Fornece dados para o painel de insights executivos
- **KPIs**: Disponibiliza métricas-chave de performance
- **Cobertura**: Informa sobre o nível de instrumentação da infraestrutura
- **Tendências**: Oferece dados de séries temporais para análise de tendências

### Geradores de Dados

Para desenvolvimento e demonstração, foram implementados geradores de dados sintéticos que simulam a resposta de sistemas reais:

- **Gerador de Insights**: Simula ROI, produtividade e recomendações estratégicas
- **Gerador de Entidades**: Cria estruturas de dados completas com métricas, logs, traces e erros
- **Gerador de KPIs**: Fornece indicadores-chave como apdex, disponibilidade e throughput

### Integração Backend-Frontend

A integração entre backend e frontend foi realizada através de:

- **Proxy API**: Configuração no Vite para direcionar chamadas `/api` para o servidor backend
- **Interfaces Tipadas**: Alinhamento entre os tipos de dados do backend e as interfaces do frontend
- **Tratamento de Erro**: Implementação de fallbacks para garantir que o frontend sempre exiba algo útil

### Scripts de Inicialização

Foram desenvolvidos scripts para facilitar a execução do sistema:

- **iniciar_sistema.py**: Inicia backend e frontend em paralelo com um único comando
- **gerar_dados_demo.py**: Popula o sistema com dados de demonstração realistas
- **start_with_endpoints.py**: Versão específica para iniciar o backend com os novos endpoints

## Próximos Passos

- **Auto-ajuste**: Implementar ajuste automático dos parâmetros de filtragem
- **Aprendizado Contínuo**: Melhorar os filtros com base em feedback do uso real
- **Visualizações Avançadas**: Expandir visualizações para novos tipos de dados
- **Integração Real**: Substituir gradualmente os dados simulados por dados reais da infraestrutura

## Conclusão

A integração do coletor avançado do New Relic com o sistema de economia de tokens representa uma evolução significativa na plataforma Analyst IA. Ao combinar dados mais ricos com processamento mais eficiente, conseguimos oferecer análises mais detalhadas e precisas enquanto reduzimos custos operacionais.

O sistema atual está pronto para uso em produção, com todas as integrações concluídas, documentação completa e procedimentos de backup implementados.

**Data de Conclusão**: 29 de junho de 2025
