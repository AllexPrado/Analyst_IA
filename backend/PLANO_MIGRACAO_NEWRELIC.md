# PLANO DE MIGRAÇÃO DO NEW RELIC

## Situação Atual

O sistema Analyst_IA está utilizando o plano gratuito do New Relic que tem limite de 100 GB de ingestão de dados por mês. Este limite foi excedido, resultando na impossibilidade de continuar coletando telemetria ou visualizando os dados das APMs e VMs monitoradas.

Como solução temporária, implementamos:
- Script para desativar os agentes New Relic (`desativar_newrelic_emergencia.py`)
- Sistema de monitoramento local (`monitoramento_local.py`)
- Relatórios baseados no monitoramento local (`gerar_relatorio_monitoramento.py`)

## Plano de Ação para Migração Completa

### Fase 1: Estabilização (Imediata)

- [x] Desativar agentes New Relic para evitar exceder ainda mais o limite
- [x] Implementar monitoramento local básico
- [x] Configurar relatórios locais

**Duração**: 1-2 dias

### Fase 2: Análise e Planejamento (1-2 semanas)

1. **Avaliação do uso atual**:
   - Levantar quais métricas eram essenciais no New Relic
   - Identificar quais serviços precisam de monitoramento prioritário
   - Determinar requisitos de alertas e notificações

2. **Avaliação de alternativas**:
   - Prometheus + Grafana (código aberto, sem limites)
   - Datadog (possui plano gratuito e integrações similares)
   - Zabbix (código aberto, robusto para monitoramento de infraestrutura)
   - Elastic APM (integração com Elasticsearch)

3. **Análise de custos**:
   - Estimar custos de infraestrutura para alternativas self-hosted
   - Comparar planos das soluções em nuvem
   - Avaliar esforço de migração para cada alternativa

### Fase 3: Implementação da Nova Solução (2-4 semanas)

1. **Configuração da Infraestrutura**:
   - Preparar servidores/containers para a nova solução
   - Configurar bancos de dados para armazenamento de métricas
   - Implementar backups e políticas de retenção

2. **Implantação gradual**:
   - Começar com monitoramento de infraestrutura básica
   - Adicionar APMs e monitoramento de aplicação
   - Configurar dashboards e visualizações

3. **Configuração de alertas**:
   - Implementar alertas críticos
   - Configurar notificações (e-mail, Slack, etc.)
   - Criar documentação de resposta a incidentes

### Fase 4: Migração Completa (1-2 semanas)

1. **Validação da nova solução**:
   - Verificar se todas as métricas necessárias estão sendo coletadas
   - Validar dashboards e alertas
   - Realizar testes de carga para garantir escalabilidade

2. **Descomissionamento do New Relic**:
   - Remover agentes permanentemente
   - Cancelar/suspender a conta (se aplicável)
   - Arquivar dados históricos importantes

3. **Treinamento da equipe**:
   - Capacitar equipe na nova solução
   - Documentar procedimentos de manutenção
   - Estabelecer processos para adição de novos serviços ao monitoramento

### Fase 5: Otimização Contínua

1. **Revisão periódica**:
   - Avaliar volume de dados e necessidades de armazenamento
   - Ajustar políticas de retenção
   - Refinar alertas para reduzir falsos positivos

2. **Automação**:
   - Integração com pipeline de CI/CD para monitoramento automático de novos serviços
   - Implementar auto-remediação para problemas conhecidos

## Recomendação de Solução

Baseado na necessidade de monitorar APMs e VMs sem custos elevados, nossa recomendação é:

### Prometheus + Grafana (Stack Open Source)

**Componentes**:
- **Prometheus**: Coleta e armazenamento de métricas
- **Grafana**: Visualização e dashboards
- **AlertManager**: Gerenciamento e roteamento de alertas
- **Node Exporter**: Monitoramento de servidores/VMs
- **Blackbox Exporter**: Monitoramento de endpoints HTTP/TCP

**Vantagens**:
- Solução completamente gratuita e open source
- Alta escalabilidade e flexibilidade
- Grande comunidade e muitas integrações disponíveis
- Controle total sobre dados e retenção

**Desvantagens**:
- Requer infraestrutura própria
- Curva de aprendizado inicial
- Configuração mais manual comparada a soluções SaaS

## Próximos Passos Imediatos

1. **Reunião de kickoff** para definir requisitos detalhados de monitoramento
2. **Avaliação técnica** das alternativas propostas
3. **Prova de conceito** com a solução escolhida usando um subconjunto de serviços
4. **Plano detalhado de implementação** com cronograma e responsáveis

## Conclusão

A migração do New Relic para uma solução alternativa é uma oportunidade para reavaliação e otimização do monitoramento do Analyst_IA. Com um plano estruturado e uma abordagem gradual, podemos garantir a continuidade do monitoramento sem interrupções significativas e sem exceder limites ou custos inesperados.
