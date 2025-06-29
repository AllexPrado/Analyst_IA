# Atualização: Sistema New Relic Advanced Collector

## Visão Geral

Esta atualização implementa um coletor avançado para o New Relic que permite que o sistema Analyst IA tenha acesso a 100% dos dados disponíveis no New Relic, incluindo:

- Métricas padrão (Apdex, Response Time, Error Rate, Throughput)
- Logs detalhados
- Traces completos
- Backtraces de erros
- Queries SQL e desempenho
- Informações de execução de código (módulo, linha de código, tempo)
- Dados de distribuição
- Relacionamentos entre entidades

## Componentes Atualizados

### Novos Arquivos

- `utils/newrelic_advanced_collector.py` - Coletor avançado que utiliza NRQL e GraphQL
- `atualizar_cache_completo.py` - Script para atualizar o cache com todos os dados do New Relic
- `test_advanced_collector_integration.py` - Teste de integração do coletor avançado

### Arquivos Modificados

- `utils/cache.py` - Integração do coletor avançado ao sistema de cache
- `main.py` - Configuração para usar o coletor avançado por padrão
- `cache_integration.py` - Inicialização do sistema de cache avançado

## Novos Endpoints

### `/api/cache/atualizar_avancado`

Endpoint específico para atualizar o cache usando o coletor avançado. Este endpoint:

- Utiliza o script `atualizar_cache_completo.py` para coletar todos os dados avançados do New Relic
- Armazena os resultados no cache para uso em todo o sistema
- Retorna informações detalhadas sobre a atualização

## Como Testar

1. **Teste do Coletor Avançado**:
``powershell
   cd d:\projetos\Analyst_IA\backend
   python -m utils.newrelic_advanced_collector
   ``

2. **Atualização do Cache Completo**:
   ``powershell
   cd d:\projetos\Analyst_IA\backend
   python atualizar_cache_completo.py
   ``

3. **Verificação da Integração**:
   ``powershell
   cd d:\projetos\Analyst_IA\backend
   python test_advanced_collector_integration.py
   ``

4. **Via API (com a aplicação em execução)**:
   - Use o endpoint `/api/cache/atualizar_avancado` para forçar a atualização do cache usando o coletor avançado
   - Use o endpoint `/api/cache/diagnostico` para verificar o status do cache

## Cobertura de Dados

Esta atualização garante que o sistema tenha acesso a 100% dos dados disponíveis no New Relic, permitindo que o sistema ofereça análises mais precisas e completas, incluindo:

- **Logs**: Mensagens de log completas com contexto e metadados
- **Traces**: Informações detalhadas de transações, incluindo tempo de cada segmento
- **Erros**: Backtraces completos e informações de contexto
- **Queries SQL**: Consultas SQL executadas, incluindo tempo de execução e planos de execução
- **Execução de Código**: Informações sobre módulos e linhas de código que estão gerando problemas
- **Relacionamentos**: Conexões entre entidades diferentes no sistema

## Próximos Passos

1. Integrar a visualização dos dados avançados no frontend
2. Criar painéis específicos para cada tipo de dado avançado
3. Implementar análises automáticas com base nos novos tipos de dados
4. Otimizar o armazenamento e acesso aos dados avançados para melhorar o desempenho

---

### Data da atualização: Junho 2024
