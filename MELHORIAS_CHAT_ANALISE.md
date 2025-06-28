# Melhorias na Análise do Chat IA

Este documento descreve as melhorias implementadas no módulo de análise do Chat IA para garantir análises mais completas, inteligentes e personalizadas.

## Principais Melhorias

### 1. Filtragem Rigorosa de Entidades sem Dados Reais

- Implementada rejeição total de entidades com score 0 (sem dados relevantes)
- Aplicado filtro para garantir que apenas entidades com métricas reais sejam consideradas
- Sistema de fallback para manter cache anterior quando novas entidades são inválidas

### 2. Detecção de Intenção da Pergunta

- Análise avançada da pergunta do usuário para detectar o tipo de consulta
- Personalização do prompt baseado no tipo de pergunta (APIs lentas, SQL, erros, causa raiz)
- Filtragem de entidades mais relevantes para cada tipo de pergunta

### 3. Enriquecimento de Contexto

- Novo módulo `context_enricher.py` que analisa profundamente os dados disponíveis
- Detecção automática de tópicos na pergunta do usuário
- Análises especializadas para diferentes áreas:
  - Performance
  - Erros e exceções
  - Banco de dados e SQL
  - Frontend e experiência do usuário
  - Infraestrutura
  - Correlações entre métricas

### 4. Personalização por Tipo de Usuário

- Adaptação automática da resposta com base no perfil do usuário:
  - **Perfil Técnico**: Respostas detalhadas com dados técnicos, código, queries e troubleshooting
  - **Perfil Gestor**: Respostas concisas, diretas, focadas em impacto de negócio e próximos passos
- Detecção automática do tipo de usuário pela linguagem da pergunta

### 5. Instruções Específicas por Tipo de Pergunta

- Para perguntas sobre APIs lentas: foco em métricas de resposta, queries SQL e stacktraces
- Para perguntas sobre SQL: análise de queries lentas, frequência e otimizações
- Para análise de causa raiz: foco em correlações e identificação sistemática de problemas
- Para perguntas sobre erros: análise detalhada de exceções e stacktraces

## Como Usar os Novos Recursos

### Para Obter Análises Técnicas Detalhadas

Faça perguntas específicas e técnicas, como:

```text
Liste as 3 APIs mais lentas dos últimos 7 dias e detalhe a causa raiz da lentidão, incluindo queries SQL, stacktrace e função afetada.
```

### Para Obter Resumos Executivos

Faça perguntas com termos executivos, como:

Resumo executivo do status do ambiente nos últimos 7 dias, destacando os principais problemas e impactos.
``
Resumo executivo do status do ambiente nos últimos 7 dias, destacando os principais problemas e impactos.
``

## Exemplos de Queries NRQL para Análises Avançadas

Para complementar as análises, o Chat IA agora sugere queries NRQL específicas:

### Para Análise de APIs Lentas

```sql
SELECT average(duration) FROM Transaction WHERE appName = 'YourAppName' FACET name ORDER BY average(duration) DESC LIMIT 10 SINCE 7 days ago
```

### Para Queries SQL Lentas

```sql
SELECT count(*), average(duration), max(duration) FROM DatabaseStatement WHERE databaseCallCount > 0 FACET sql ORDER BY max(duration) DESC LIMIT 10
```

### Para Análise de Erros

```sql
SELECT * FROM TransactionError WHERE appName = 'YourAppName' ORDER BY timestamp DESC LIMIT 100 SINCE 24 hours ago
```

## Próximos Passos

1. Continuar aprimorando o módulo de enriquecimento de contexto
2. Implementar detecção automática de anomalias
3. Adicionar capacidade de gerar dashboards dinâmicos baseados nas análises
4. Implementar alertas proativos para problemas detectados
