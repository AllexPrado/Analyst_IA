# Pipeline de Dados do Analyst_IA

Este documento explica em detalhes o fluxo de dados no sistema Analyst_IA, desde a coleta de dados do New Relic até a visualização no frontend.

## Visão Geral da Pipeline

O sistema Analyst_IA implementa uma pipeline de dados robusta que consiste em cinco etapas principais:

1. **Coleta de Dados** - Extração de dados do New Relic (reais ou simulados)
2. **Processamento e Armazenamento** - Transformação e armazenamento em cache
3. **Exposição via API** - Disponibilização dos dados através de endpoints REST
4. **Serviços Frontend** - Camada de abstração para comunicação com a API
5. **Visualização** - Consumo e exibição nos componentes do frontend

```
┌─────────────┐     ┌────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   New Relic │     │            │     │             │     │   Serviços  │     │             │
│     API     │ ──> │  Backend   │ ──> │ API REST    │ ──> │  Frontend   │ ──> │ Componentes │
│  (ou dados  │     │  (Cache)   │     │ (Endpoints) │     │   (API)     │     │   Vue.js    │
│  simulados) │     │            │     │             │     │             │     │             │
└─────────────┘     └────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     Coleta          Processamento        Exposição        Abstração FE        Visualização
```

## 1. Coleta de Dados

### Fonte Real: New Relic API

Quando configurada com credenciais reais, o sistema coleta dados diretamente da API do New Relic:

- **Script principal**: `advanced_newrelic_collector.py`
- **Autenticação**: Utiliza `NEW_RELIC_ACCOUNT_ID` e `NEW_RELIC_API_KEY` do arquivo `.env` ou variáveis de ambiente
- **Script de configuração**: `verificar_config_dados_reais.py` (verifica e orienta sobre configuração)
- **Script de integração**: `integrar_dados_reais_newrelic.py` (extrai e integra dados reais)
- **Tipos de dados coletados**:
  - Métricas de aplicações (Apdex, Response Time, Throughput, etc.)
  - Dados de infraestrutura (CPU, memória, disco, etc.)
  - Dados de Kubernetes (clusters, pods, nodes, etc.)
  - Topologia de serviços
  - Logs e traces

Para configurar dados reais, execute:
```bash
python verificar_config_dados_reais.py
```

Para mais detalhes, consulte [CONFIGURACAO_DADOS_REAIS.md](CONFIGURACAO_DADOS_REAIS.md).

### Fonte Alternativa: Dados Simulados

Quando as credenciais do New Relic não estão disponíveis, o sistema usa dados simulados:

- **Scripts**: `regenerar_cache_avancado.py`
- **Geração de dados**: Baseada em padrões realistas que simulam ambientes de produção
- **Tipos de dados simulados**: Os mesmos tipos disponíveis em dados reais

### Frequência de Coleta

- **Coleta única**: Através do script `integrar_dados_reais_newrelic.py`
- **Coleta periódica**: Através do script `sincronizar_periodico_newrelic.py` (configurável, padrão: 30 minutos)

## 2. Processamento e Armazenamento

### Transformação de Dados

Antes de serem armazenados, os dados passam por um processo de transformação:

- **Normalização**: Estruturação em formato consistente
- **Enriquecimento**: Adição de metadados úteis
- **Filtragem**: Remoção de dados irrelevantes ou nulos
- **Cálculo de métricas derivadas**: Estatísticas úteis para análise

### Sistema de Cache

Os dados processados são armazenados em arquivos de cache:

- **Localização**: Diretório `backend/cache/`
- **Formato**: Arquivos JSON estruturados
- **Principais arquivos**:
  - `kubernetes_metrics.json` - Dados de Kubernetes
  - `infrastructure_detailed.json` - Dados de infraestrutura
  - `service_topology.json` - Dados de topologia de serviços
  - `applications_metrics.json` - Métricas de aplicações
  - `serverless_functions.json` - Funções serverless

### Mecanismo de Fallback

O sistema implementa um mecanismo inteligente de fallback:

- Se a coleta de dados reais falhar, utiliza o cache existente
- Se não houver cache, utiliza dados simulados
- Rastreamento do status de origem dos dados (real vs. simulado)

## 3. Exposição via API

### Arquitetura da API

- **Framework**: FastAPI
- **Servidor**: Uvicorn
- **Porta padrão**: 8000

### Principais Endpoints

- **Endpoints de saúde**:
  - `GET /api/health` - Status geral da API
  
- **Endpoints avançados**:
  - `GET /api/avancado/kubernetes` - Dados de Kubernetes
  - `GET /api/avancado/infraestrutura` - Dados de infraestrutura
  - `GET /api/avancado/topologia` - Dados de topologia de serviços

- **Endpoints de entidades**:
  - `GET /api/entidades` - Lista de entidades monitoradas
  - `GET /api/entidades/{entity_id}` - Detalhes de uma entidade específica
  - `GET /api/entidades/{entity_id}/metricas` - Métricas de uma entidade

### Documentação da API

A API é auto-documentada usando Swagger UI:
- **URL**: http://localhost:8000/docs
- **Detalhes**: Descrição completa de endpoints, parâmetros, esquemas e exemplos de respostas

## 4. Serviços Frontend

### Arquitetura de Serviços

Para melhorar a comunicação entre os componentes Vue e a API REST, o sistema implementa uma camada de serviços no frontend:

- **Responsabilidade**: Abstrair a lógica de comunicação com a API REST e gerenciar cache em memória
- **Localização**: Diretório `frontend/src/api/`
- **Principais serviços**:
  - `advancedDataService.js` - Serviço para dados avançados (Kubernetes, infraestrutura, topologia)

### Cache em Memória

Os serviços frontend implementam um mecanismo de cache em memória:

- **Objetivo**: Reduzir o número de requisições à API para dados que mudam com pouca frequência
- **Duração**: Configurável por serviço (padrão: 5 minutos)
- **Estratégia**: Utilização de objetos JavaScript para armazenar resultados das requisições
- **Invalidação**: Manual (método `clearCache()`) ou por expiração de tempo

### Interface do Serviço

Os serviços expõem uma interface consistente para os componentes:

```javascript
// Exemplo de uso do advancedDataService
import advancedDataService from '../api/advancedDataService'

// Obter dados com cache (default: true)
const k8sData = await advancedDataService.getKubernetesData()

// Forçar refresh ignorando cache
const freshData = await advancedDataService.getKubernetesData(false)

// Obter todos os dados em paralelo
const allData = await advancedDataService.getAllAdvancedData()
```

### Benefícios

1. **Separação de responsabilidades**: Componentes focam na apresentação, serviços na obtenção de dados
2. **Reutilização de código**: Múltiplos componentes podem utilizar o mesmo serviço
3. **Consistência**: Garantia de que todos os componentes usam a mesma lógica para obter dados
4. **Manutenção facilitada**: Alterações nos endpoints ou na lógica de obtenção são centralizadas

## 5. Visualização no Frontend

A visualização no frontend é realizada através de componentes Vue.js que consomem os dados expostos pela API. Os principais componentes e suas funções incluem:

- **`App.vue`**: Componente raiz que configura o roteamento e o estado global
- **`Home.vue`**: Página inicial que exibe um resumo das métricas
- **`DetalhesEntidade.vue`**: Página que exibe detalhes e métricas de uma entidade específica
- **`GraficoLinhas.vue`**: Componente para exibição de gráficos de linhas para métricas ao longo do tempo
- **`TabelaDados.vue`**: Componente para exibição de dados tabulares

Os componentes utilizam as bibliotecas Vuetify para o design e Chart.js para a exibição de gráficos.

## Ciclo de Vida dos Dados

### 1. Inicialização do Sistema

```
┌─────────────────────┐
│ iniciar_sistema.py  │
└─────────────────────┘
           │
           ▼
┌─────────────────────┐    ┌─────────────────────┐
│ check_and_fix_cache │───>│ regenerar_cache.py  │
└─────────────────────┘    └─────────────────────┘
           │                         │
           │                         │
           ▼                         ▼
┌─────────────────────┐    ┌─────────────────────┐
│   backend/main.py   │    │    cache/*.json     │
└─────────────────────┘    └─────────────────────┘
           │                         │
           ▼                         │
┌─────────────────────┐              │
│ frontend (npm run)  │<─────────────┘
└─────────────────────┘
```

### 2. Sincronização de Dados

```
┌────────────────────────────┐
│sincronizar_periodico_*.py  │
└────────────────────────────┘
              │
              ▼
┌────────────────────────────┐     ┌────────────────┐
│ advanced_newrelic_collector│────>│   New Relic    │
└────────────────────────────┘     │      API       │
              │                    └────────────────┘
              ▼
┌────────────────────────────┐
│     backend/cache/*.json   │
└────────────────────────────┘
              │
              ▼
┌────────────────────────────┐
│      API Endpoints         │
└────────────────────────────┘
              │
              ▼
┌────────────────────────────┐
│     Frontend Components    │
└────────────────────────────┘
```

## Benefícios da Arquitetura

1. **Separação de Responsabilidades**:
   - Cada componente tem uma função clara e bem definida
   - Facilita manutenção e expansão do sistema

2. **Resiliência**:
   - Sistema de fallback garante funcionamento mesmo com falhas
   - Cache persiste dados mesmo quando a fonte original está indisponível

3. **Escalabilidade**:
   - Possibilidade de escalar componentes individualmente
   - Facilidade de migração para banco de dados em vez de cache em arquivo

4. **Segurança**:
   - Dados sensíveis ficam apenas no backend
   - Frontend só acessa dados via API controlada

## Customização da Pipeline

A pipeline pode ser personalizada em vários aspectos:

1. **Frequência de Sincronização**:
   - Configure o intervalo no script `sincronizar_periodico_newrelic.py`
   - Exemplo: `--intervalo 15` para sincronizar a cada 15 minutos

2. **Tipos de Dados**:
   - Modifique os coletores para incluir ou excluir tipos específicos de dados
   - Adicione novos arquivos de cache e endpoints correspondentes

3. **Transformação de Dados**:
   - Personalize os formatos de saída nos métodos de transformação
   - Adicione cálculos adicionais ou métricas derivadas

4. **Exibição no Frontend**:
   - Crie novos componentes de visualização
   - Modifique os existentes para diferentes layouts ou estilos

## Monitoramento da Pipeline

O sistema inclui ferramentas para monitorar a saúde da pipeline de dados:

1. **Diagnóstico**:
   - Use `diagnostico_infra_avancada.py` para verificar o status do cache e API
   - Analise logs em `logs/` para identificar problemas

2. **Relatórios de Integração**:
   - Gerados após sincronização em `relatorio_integracao_dados_reais.json`
   - Contêm informações sobre status, tamanho e atualidade dos dados

3. **Alertas**:
   - Configure alertas para falhas na coleta de dados
   - Monitore a saúde do sistema via `/api/health`

## Conclusão

A pipeline de dados do Analyst_IA foi projetada para ser robusta, flexível e fácil de manter. Com uma clara separação de responsabilidades e mecanismos de fallback, o sistema garante que os dados estejam sempre disponíveis para visualização, seja utilizando dados reais do New Relic ou dados simulados quando necessário.

A compreensão desta pipeline é fundamental para estender o sistema, diagnosticar problemas ou otimizar seu funcionamento para necessidades específicas.
