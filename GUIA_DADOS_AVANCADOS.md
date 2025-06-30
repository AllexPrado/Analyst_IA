# Guia de Utilização - Dados Avançados do New Relic

Este guia explica como utilizar os novos recursos avançados do coletor New Relic integrado no Analyst IA.

## Visão Geral

A nova integração avançada fornece acesso a mais tipos de dados do New Relic, incluindo:

- **Logs detalhados**: Mensagens de log com contexto completo
- **Traces distribuídos**: Fluxos de execução entre serviços com spans
- **Queries SQL**: Consultas com parâmetros e tempos de execução
- **Backtraces de erros**: Pilhas de erros detalhadas

Estes dados são exibidos no painel de visualização avançada em cada entidade monitorada.

## Acessando Dados Avançados

### No Dashboard

1. Navegue até qualquer domínio (APM, Browser, Infra, etc.)
2. Selecione uma entidade para visualizar seus detalhes
3. Localize a seção "Dados avançados" no painel da entidade
4. Clique nas abas para alternar entre diferentes tipos de dados

![Painel de Dados Avançados](./frontend/src/assets/screenshots/advanced-panel.png)

### No Chat IA

O Chat IA agora tem acesso aos dados avançados e pode responder perguntas específicas como:

- "Mostre-me os erros recentes na aplicação X"
- "Quais queries SQL estão mais lentas no serviço Y?"
- "Mostre-me os logs de erro do último incidente"
- "Qual a distribuição de tempo de resposta da API Z?"

## Tipos de Dados Avançados

### Logs

Os logs incluem:

- **Timestamp**: Quando o log foi gerado
- **Nível**: ERROR, WARNING, INFO, DEBUG, etc.
- **Mensagem**: O conteúdo do log
- **Contexto**: Dados adicionais associados ao log

Exemplo de uso:
> "Filtre os logs de ERROR da aplicação X nas últimas 24 horas"

### Traces

Os traces incluem:

- **Nome da transação**: Identificador da operação
- **Duração**: Tempo total de execução
- **Timestamp**: Quando o trace foi iniciado
- **Spans**: Operações individuais dentro da transação
  - Nome do span
  - Duração
  - Tipo (DB, HTTP, etc.)

Exemplo de uso:
> "Quais são as transações mais lentas no serviço X?"

### Queries SQL

Os dados de queries incluem:

- **SQL**: A consulta executada
- **Duração**: Tempo de execução
- **Timestamp**: Quando foi executada
- **Banco de dados**: Tipo e/ou nome do banco
- **Parâmetros**: Valores passados para a query (quando disponível)

Exemplo de uso:
> "Mostre-me as queries mais lentas no banco de dados Y"

### Erros

Os dados de erros incluem:

- **Mensagem**: Descrição do erro
- **Tipo**: Classe ou categoria do erro
- **Timestamp**: Quando ocorreu
- **Backtrace**: Pilha de chamadas que levou ao erro
- **Contexto**: Informações adicionais sobre o ambiente

Exemplo de uso:
> "Quais erros ocorreram após o deploy de ontem?"

## Atualizando o Cache de Dados Avançados

Para atualizar manualmente o cache com dados avançados:

1. Navegue até Configurações > Cache
2. Clique em "Atualizar Cache Avançado"

Ou utilize a API diretamente:

```bash
curl -X POST http://localhost:8000/api/cache/atualizar_avancado
```

## Dicas de Uso Eficiente

1. **Filtragem no frontend**: Use os filtros disponíveis para focar em dados específicos
2. **Perguntas específicas**: No Chat IA, perguntas específicas geram respostas mais precisas
3. **Correlação de dados**: Compare logs, traces e erros para diagnosticar problemas complexos
4. **Exportação**: Use os botões de exportação para salvar dados para análise externa

## Resolução de Problemas

### Dados não aparecem no painel avançado

Possíveis causas:

- O tipo de entidade não suporta esse dado específico
- Os dados não estão disponíveis no período selecionado
- A instrumentação do New Relic não está configurada para coletar esses dados

Solução:

1. Verifique se a instrumentação do New Relic está correta
2. Tente atualizar o cache avançado
3. Verifique se o período selecionado contém atividade

### Cache avançado não atualiza

Possíveis causas:

- Problemas de credenciais New Relic
- Timeout na API New Relic
- Erro interno no coletor avançado

Solução:

1. Verifique os logs do backend em `backend/logs/analyst_ia.log`
2. Confirme se as credenciais do New Relic estão corretas
3. Tente o endpoint de diagnóstico: `/api/cache/diagnostico`

## Suporte

Para problemas técnicos com os dados avançados:

- Consulte a documentação técnica completa em `DOCUMENTACAO_TECNICA_INTEGRACAO.md`
- Verifique os logs do backend para erros específicos
- Contate o suporte técnico com os logs e detalhes específicos do problema
