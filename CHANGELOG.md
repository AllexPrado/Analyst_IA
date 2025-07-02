# Changelog

## [2.0.0] - 2025-07-01

### Adicionado
- Implementação completa do coletor avançado do New Relic (`AdvancedNewRelicCollector`)
- Cobertura para todos os tipos de dados do New Relic (entidades, métricas, logs, dashboards, alertas, distributed tracing, infraestrutura, Kubernetes, serverless, topologia de serviços, recursos de nuvem)
- Métodos para infraestrutura detalhada, topologia de serviços, relatório de capacidade, métricas de Kubernetes
- Coleta de alertas, análise de dashboards e extração de NRQL
- Mock collector (`MockNewRelicCollector`) para testes sem credenciais reais
- Scripts auxiliares para testes simulados (`testar_simulado.ps1`, `.bat`, `.sh`)
- Script de verificação de conectividade com o New Relic (`verificar_conectividade_newrelic.py`)
- Documentação extensiva em português para todos os componentes

### Corrigido
- Erros de digitação, sintaxe e funções incompletas
- Tratamento de exceções e timeouts em requisições HTTP
- Problemas de SSL em conexões com o New Relic
- Integração entre coletor e sistema de cache

### Melhorado
- Documentação atualizada em português para métodos principais
- Testes de sintaxe e integração aprimorados
- Sistema de cache otimizado para grandes volumes de dados
- Integração com frontend para visualização de novos dados
