# Documentação: Infraestrutura Avançada

Este documento descreve a implementação e solução de problemas da página de Infraestrutura Avançada no Analyst IA.

## Visão Geral

A página de Infraestrutura Avançada permite visualizar dados detalhados sobre a infraestrutura, incluindo:

1. **Kubernetes** - Clusters, nodes e pods, com métricas de desempenho e saúde
2. **Infraestrutura** - Servidores, recursos e alertas ativos
3. **Topologia** - Relacionamentos entre serviços, com métricas de desempenho

## Arquivos Principais

- Frontend:
  - `frontend/src/components/pages/InfraAvancada.vue`: Componente principal da página
  - `frontend/src/api/axios.js`: Configuração do cliente axios para chamadas à API

- Backend:
  - `backend/endpoints/avancados_endpoints.py`: Endpoints da API para dados avançados
  - `backend/cache/kubernetes_metrics.json`: Cache de dados Kubernetes
  - `backend/cache/infrastructure_detailed.json`: Cache de dados de infraestrutura
  - `backend/cache/service_topology.json`: Cache de dados de topologia

- Scripts de diagnóstico e manutenção:
  - `diagnostico_infra_avancada.py`: Verifica o status da infraestrutura avançada
  - `regenerar_cache_avancado.py`: Regenera os dados de cache se necessário
  - `iniciar_sistema_avancado.bat`: Script para iniciar o sistema com infraestrutura avançada

## Arquitetura

### Frontend

O componente `InfraAvancada.vue` foi implementado para exibir três tipos principais de dados:

1. **Kubernetes**: Exibição de clusters, nós e pods em várias visualizações, incluindo tabelas e gráficos
2. **Infraestrutura**: Visualização de servidores, recursos (CPU, memória, disco) e alertas ativos
3. **Topologia**: Visualização de relacionamentos entre serviços usando D3.js para renderização gráfica

O componente utiliza o sistema de abas para alternar entre essas visualizações, mantendo uma interface limpa e organizada.

### Backend

A implementação no backend consiste em três endpoints principais:

1. `/api/avancado/kubernetes`: Fornece dados sobre clusters, nós e pods Kubernetes
2. `/api/avancado/infraestrutura`: Fornece dados sobre servidores, recursos e alertas
3. `/api/avancado/topologia`: Fornece dados sobre serviços e suas relações

Cada endpoint pode carregar dados de arquivos de cache ou gerar dados simulados quando necessário.

## Melhorias Implementadas

Para garantir uma experiência robusta e tolerante a falhas, implementamos:

1. **Tratamento de erros avançado**: O frontend agora é capaz de continuar funcionando mesmo quando um ou mais tipos de dados falham no carregamento
2. **Cliente axios configurado**: Implementamos um cliente axios com configurações padronizadas, incluindo tratamento de erros e logging
3. **Feedback visual melhorado**: Mensagens de erro mais detalhadas, com sugestões claras para solução de problemas
4. **Scripts de diagnóstico**: Adicionamos ferramentas para verificar e corrigir rapidamente problemas com os dados
5. **Cache em múltiplos locais**: Dados são armazenados em mais de um local para aumentar a resiliência
6. **Documentação detalhada**: Descrição completa da arquitetura e procedimentos de solução de problemas

## Solução de Problemas

### Problema com Tela Branca

O problema da tela branca no frontend foi resolvido com as seguintes correções:

1. **Tratamento de erros robusto**: O componente agora gerencia falhas parciais sem quebrar completamente
2. **Importação correta de ícones**: Substituímos a referência ao ícone `faKubernetes` pelo ícone padrão `['fas', 'cubes']`
3. **Configuração correta do axios**: Implementamos uma configuração centralizada do axios para garantir que as chamadas à API sejam direcionadas corretamente
4. **Dados de fallback**: Mesmo quando os endpoints falham, o componente define valores vazios para evitar erros de referência nula

### Problema com Ícones

O problema com os ícones foi resolvido substituindo:
```javascript
{ id: 'kubernetes', name: 'Kubernetes', icon: ['fab', 'kubernetes'] }
```

Por:
```javascript
{ id: 'kubernetes', name: 'Kubernetes', icon: ['fas', 'cubes'] }
```

Isso elimina a dependência do ícone `faKubernetes` que não existe no Font Awesome.

## Como Verificar e Corrigir Problemas

1. **Executar o diagnóstico**:
   ```
   python diagnostico_infra_avancada.py
   ```
   Este script verifica a disponibilidade dos dados e do backend, mostrando um relatório detalhado.

2. **Regenerar os dados de cache**:
   ```
   python regenerar_cache_avancado.py
   ```
   Use este script para recriar os arquivos de cache quando necessário.

3. **Iniciar o sistema completo**:
   ```
   iniciar_sistema_avancado.bat
   ```
   Este script inicializa o sistema completo, verificando e regenerando o cache conforme necessário.

## Funcionamento da Página

A página agora carrega corretamente e exibe:

1. **Visão geral do Kubernetes**: Resumo de clusters, nós e pods
2. **Detalhes de clusters**: Tabela com todos os clusters e suas métricas
3. **Nós e pods**: Visualização de nós e pods problemáticos
4. **Infraestrutura de servidores**: Tabela de servidores com métricas de recursos
5. **Alertas ativos**: Lista de alertas ativos na infraestrutura
6. **Diagrama de topologia interativo**: Gráfico D3.js mostrando relacionamentos entre serviços
7. **Detalhes de serviços**: Métricas de desempenho para cada serviço
8. **Dependências**: Lista de dependências entre serviços

Cada seção inclui indicadores visuais de status (verde, amarelo, vermelho) e gráficos de barras para visualizar métricas de desempenho.

## Conclusão

A implementação da página de Infraestrutura Avançada agora está completa e robusta, oferecendo:

1. **Visualização completa**: Todos os dados relevantes de Kubernetes, infraestrutura e topologia
2. **Resiliência**: Tratamento adequado de erros e dados ausentes
3. **Desempenho**: Carregamento otimizado e renderização eficiente
4. **Manutenção**: Scripts de diagnóstico e manutenção para garantir o funcionamento contínuo

Esta implementação cumpre o objetivo de fornecer uma visão abrangente e detalhada da infraestrutura, permitindo que os usuários identifiquem rapidamente problemas e tomem decisões informadas.
