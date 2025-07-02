# Documentação de Dados Avançados

## Introdução

Este documento detalha a implementação e uso dos recursos avançados de visualização de dados na plataforma Analyst IA. Estes recursos fornecem acesso a informações detalhadas sobre infraestrutura, Kubernetes e topologia de serviços, permitindo uma análise mais profunda e completa do ambiente monitorado.

## Componentes Implementados

### 1. Backend (FastAPI)

Os endpoints avançados são expostos através da API REST utilizando FastAPI:

- `/api/avancado/kubernetes` - Dados detalhados de clusters Kubernetes
- `/api/avancado/infraestrutura` - Informações de servidores e alertas de infraestrutura
- `/api/avancado/topologia` - Mapeamento de relacionamentos entre serviços

Estes endpoints são implementados no arquivo `backend/endpoints/avancados_endpoints.py` e registrados no roteador principal `core_router.py`.

### 2. Frontend (Vue.js)

A interface de usuário para visualização dos dados avançados está implementada em:

- `frontend/src/components/pages/InfraAvancada.vue` - Componente principal com três abas:
  - Kubernetes: Visão geral de clusters, nós e pods
  - Infraestrutura: Detalhes de servidores e alertas ativos
  - Topologia: Visualização interativa das relações entre serviços

### 3. Visualização de Topologia

A visualização de topologia é implementada utilizando a biblioteca D3.js, que permite:

- Representação visual dos serviços como nós
- Conexões entre serviços representadas como linhas direcionadas
- Cores indicando o estado de saúde de cada serviço
- Interatividade com arrasto e tooltip para detalhes

## Dados Disponíveis

### Kubernetes

- Visão geral de clusters, nós e pods
- Métricas de utilização de recursos (CPU, memória)
- Estado de saúde dos componentes
- Detalhes de pods problemáticos

### Infraestrutura

- Lista de servidores com detalhes de recursos
- Utilização de CPU, memória e disco
- Alertas ativos com severidade e duração
- Distribuição por regiões e tipos de servidor

### Topologia de Serviços

- Mapa interativo das relações entre serviços
- Métricas de desempenho (Apdex, tempo de resposta)
- Taxas de erro e throughput
- Dependências e número de chamadas entre serviços

## Como Utilizar

1. Inicie o sistema completo usando a tarefa "Iniciar Sistema Completo"
2. Acesse a interface web em `http://localhost:3000`
3. Navegue até a seção "Infra Avançada" no menu principal
4. Alterne entre as abas para visualizar os diferentes tipos de dados

## Testes

O arquivo `test_advanced_endpoints.py` na raiz do projeto permite testar os endpoints avançados:

```bash
python test_advanced_endpoints.py
```

O script verifica:
- Disponibilidade dos endpoints
- Formato correto dos dados retornados
- Presença de todos os campos necessários

## Personalização

### Dados Reais vs. Simulados

O sistema tenta carregar dados reais dos arquivos de cache:

- `backend/cache/kubernetes_metrics.json`
- `backend/cache/infrastructure_detailed.json`
- `backend/cache/service_topology.json`

Se os arquivos não existirem ou estiverem vazios, o sistema gera dados simulados automaticamente para demonstração.

### Visualização da Topologia

Para personalizar a visualização de topologia:

1. Modifique os parâmetros da simulação de força no método `renderTopologyGraph()`
2. Ajuste cores, tamanhos e estilos no mesmo método
3. Adicione mais interatividade conforme necessário

## Próximos Passos

- Implementar histórico de métricas para análise de tendências
- Adicionar mais detalhes para cada nó de serviço na topologia
- Implementar alertas em tempo real
- Expandir a visualização para incluir filtros e agrupamentos
