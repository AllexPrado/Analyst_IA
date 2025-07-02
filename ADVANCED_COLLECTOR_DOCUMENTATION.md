# Coletor Avançado do New Relic - Documentação

## Visão Geral

O Coletor Avançado do New Relic foi implementado para expandir significativamente a capacidade do sistema Analyst_IA em coletar, armazenar e utilizar 100% dos dados relevantes e disponíveis do New Relic. Esta implementação permite diagnósticos completos, análise profunda e respostas acionáveis para os usuários, garantindo que todas as informações relevantes estejam disponíveis para o sistema de IA.

## Novos Recursos Implementados

O Coletor Avançado oferece as seguintes capacidades:

### 1. Coleta Completa de Entidades e Métricas

- **Coleta paginada de todas as entidades**: Garante que todas as entidades monitoradas sejam coletadas, independentemente do seu número.
- **Coleta por domínio**: APM, Browser, Mobile, Infraestrutura e Synthetic.
- **Coleta de atributos e metadados**: Informações detalhadas sobre cada entidade.

### 2. Coleta de Métricas Específicas

- **Métricas de Kubernetes**: Estado de clusters, nós, pods, deployments e contêineres, incluindo eventos e alertas.
- **Métricas de funções serverless**: Invocações, duração, erros, cold starts e uso de memória de funções Lambda.
- **Métricas de infraestrutura**: Uso de CPU, memória, disco e rede de hosts e contêineres.

### 3. Análise de Dashboards e NRQL

- **Extração de queries NRQL**: Analisa dashboards e extrai todas as consultas NRQL usadas em widgets.
- **Análise de estrutura de dashboards**: Páginas, widgets e visualizações.

### 4. Dados Avançados de Infraestrutura

- **Topologia de serviços**: Mapeamento de dependências entre serviços.
- **Detalhes de hosts**: Métricas detalhadas e processos em execução.
- **Dados de contêineres**: Estado, uso de recursos e informações detalhadas.
- **Recursos cloud**: Informações sobre recursos AWS, Azure e GCP.

### 5. Relatórios de Capacidade

- **Análise de uso de recursos**: CPU, memória, disco e rede.
- **Saúde dos serviços**: Taxas de erro e métricas de duração.
- **Recomendações de escala**: Identificação de hosts com alta utilização e sugestões de escalabilidade.

### 6. Integração e Sincronização

- **Sincronização periódica**: Atualização automática de dados em intervalos configuráveis.
- **Relatórios de cobertura**: Visibilidade sobre quais dados foram coletados.
- **Cache estruturado**: Armazenamento eficiente de dados para acesso rápido.

## Como Usar os Novos Recursos

### Executar Testes do Coletor Avançado

```bash
# Executar teste completo do coletor avançado
python test_advanced_collector.py
```

Este teste verifica todas as novas funcionalidades implementadas, incluindo coleta de métricas de Kubernetes, serverless, análise de dashboards, coleta de dados de infraestrutura e geração de relatórios de capacidade.

### Sincronizar Dados do New Relic

```bash
# Sincronização completa (uma única vez)
python sincronizar_newrelic_avancado.py --once

# Iniciar sincronização periódica (a cada 30 minutos)
python sincronizar_newrelic_avancado.py --periodic --interval 30

# Especificar número de execuções para sincronização periódica
python sincronizar_newrelic_avancado.py --periodic --interval 60 --executions 24
```

### Iniciar o Sistema com Sincronização Avançada

```bash
# Iniciar o sistema com sincronização completa antes
python iniciar_sistema_avancado.py

# Iniciar o sistema com sincronização periódica em background
python iniciar_sistema_avancado.py --periodic-sync

# Iniciar o sistema sem sincronização
python iniciar_sistema_avancado.py --no-sync
```

## Tarefas do VS Code

Foram adicionadas novas tarefas ao VS Code para facilitar o uso do coletor avançado:

1. **Testar Coletor Avançado (Novo)**: Executa os testes completos do coletor avançado.
2. **Sincronizar New Relic (Completo)**: Realiza uma sincronização completa dos dados.
3. **Iniciar Sincronização Periódica (30min)**: Inicia sincronização automática a cada 30 minutos.
4. **Iniciar Sistema com Sincronização Avançada**: Inicia o sistema completo com sincronização avançada.

## Estrutura dos Dados Coletados

O coletor avançado organiza os dados na seguinte estrutura:

```
{
  "collected_at": "2023-06-01T12:00:00.000000",
  "entities": {
    "APM": [...],
    "BROWSER": [...],
    "MOBILE": [...],
    "INFRA": [...],
    "SYNTH": [...]
  },
  "metrics": {...},
  "logs": {...},
  "alerts": {...},
  "dashboards": {...},
  "distributed_tracing": {...},
  "kubernetes_data": {...},
  "serverless_data": {...},
  "infrastructure_details": {
    "hosts": {...},
    "containers": {...},
    "kubernetes": {...},
    "services_topology": {...},
    "cloud_resources": {...}
  },
  "capacity_report": {
    "cpu_usage": {...},
    "memory_usage": {...},
    "disk_usage": {...},
    "network_usage": {...},
    "service_health": {...},
    "scaling_recommendations": {...}
  },
  "dashboard_nrql": {...},
  "coverage_report": {...}
}
```

## Logs e Relatórios

- Logs detalhados são gerados em `logs/sincronizar_newrelic_avancado.log`
- Relatórios de cobertura são salvos em `reports/coverage_report_*.json`
- Dados coletados são armazenados em `backend/cache/newrelic_data_*.json`
- O arquivo mais recente está sempre disponível como `backend/cache/newrelic_data_latest.json`

## Próximos Passos e Melhorias Futuras

1. **Otimização de Performance**:
   - Implementar coleta assíncrona paralela para aumentar a velocidade
   - Adicionar compressão de dados para reduzir tamanho do cache

2. **Expansão da Cobertura**:
   - Adicionar coleta de atributos customizados
   - Expandir integração com serviços cloud específicos
   - Implementar coleta de logs avançados e análise de padrões

3. **Visualização de Dados**:
   - Criar dashboards administrativos para monitorar o status da sincronização
   - Adicionar painéis de qualidade de dados
   - Visualizar topologia de serviços no frontend

4. **Integrações Adicionais**:
   - Implementar exportação de dados para outros sistemas
   - Adicionar suporte a outras fontes de dados além do New Relic
   - Criar conectores para sistemas de alerta externos

## Conclusão

O Coletor Avançado do New Relic representa uma expansão significativa na capacidade do sistema Analyst_IA de fornecer análises completas e informações acionáveis. Com a implementação desses recursos, o sistema agora pode coletar 100% dos dados relevantes do New Relic, permitindo diagnósticos mais precisos, análises mais profundas e recomendações mais úteis para os usuários.
