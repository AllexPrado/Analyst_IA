# Documentação de Integração Frontend-Backend

## Visão Geral da Integração

Este documento detalha como a integração entre o frontend e o backend do **Analyst IA** foi implementada, com foco em garantir que dados reais, não-nulos e não-vazios sejam exibidos em todas as páginas do frontend (KPIs, Insights, Cobertura, Tendências, Chat IA, etc.).

## Arquitetura da Integração

### Fluxo de Dados

``
┌────────────────┐     ┌─────────────────┐     ┌────────────────┐
│ New Relic API  │────▶│   Backend API   │────▶│    Frontend    │
│ (Dados Reais)  │     │  (Processamento)│     │  (Interface)   │
└────────────────┘     └─────────────────┘     └────────────────┘
                               ▲
                               │
                      ┌────────┴───────┐
                      │ Arquivos JSON  │
                      │  (Cache/Demo)  │
                      └────────────────┘
``

### Componentes Principais

1. **Backend**:
   - **Endpoints REST API**: Fornecem dados para o frontend
   - **Processadores de Dados**: Transformam dados brutos em formato utilizável
   - **Sistema de Fallback**: Usa dados simulados quando dados reais não estão disponíveis

2. **Frontend**:
   - **Componentes Vue.js**: Exibem dados de forma amigável
   - **API Service**: Centraliza chamadas para o backend
   - **Tratamento de Dados Nulos**: Garante que a interface não quebre com dados incompletos

## Endpoints da API

| Endpoint | Descrição | Frontend Component |
|---------|-----------|-------------------|
| `/kpis` | Indicadores-chave de performance | `Kpis.vue` |
| `/tendencias` | Análises de tendências | `Tendencias.vue` |
| `/cobertura` | Cobertura de monitoramento | `Cobertura.vue` |
| `/insights` | Insights de negócio | `Insights.vue` |
| `/chat` | Histórico e respostas do chat | `ChatPanel.vue` |
| `/entidades` | Entidades monitoradas | Vários componentes |
| `/status` | Estado do sistema | Vários componentes |
| `/health` | Verificação de saúde da API | Não exibido (diagnóstico) |
| `/data/{filename}` | Acesso genérico a dados | Utilizado para debug |

## Estrutura de Dados

### KPIs

Os KPIs fornecem métricas essenciais de desempenho como disponibilidade, taxa de erro, e latência:

```json
{
  "disponibilidade": {
    "uptime": 99.95,
    "total_servicos": 52,
    "servicos_disponiveis": 51
  },
  "erros": {
    "taxa_erro": 0.5,
    "total_requisicoes": 250000,
    "requisicoes_com_erro": 1250
  }
}
```

### Tendências

Dados históricos que mostram como métricas evoluem ao longo do tempo:

```json
{
  "apdex": {
    "labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
    "series": [{
      "name": "Apdex",
      "data": [0.82, 0.84, 0.81, 0.83, 0.87, 0.89]
    }]
  }
}
```

### Cobertura

Informações sobre quanto da infraestrutura está sendo monitorada:

```json
{
  "total_entidades": 180,
  "monitoradas": 153,
  "porcentagem": 85.0,
  "por_dominio": {
    "APM": {
      "total": 48,
      "monitoradas": 41
    }
  }
}
```

### Insights

Recomendações e análises de negócio:

```json
{
  "roiMonitoramento": 5.3,
  "economiaTotal": 45000,
  "recomendacoes": [{
    "titulo": "Otimização de queries SQL lentas",
    "impacto": 8.5
  }]
}
```

## Mecanismo de Fallback

Para garantir que a interface nunca exiba dados vazios ou nulos, implementamos um mecanismo de fallback em três níveis:

1. **Nível Backend**:
   - Primeiro tenta carregar dados reais do New Relic
   - Se falhar, tenta carregar dados de arquivos JSON em cache
   - Se falhar novamente, gera dados simulados estatisticamente relevantes

2. **Nível Frontend**:
   - Implementa verificação de nullish para todos os campos
   - Usa valores padrão quando necessário
   - Exibe mensagens informativas quando não há dados

3. **Nível de Componente**:
   - Componentes como `SafeApexChart` e `SafeDataDisplay` tratam dados nulos
   - Fallbacks visuais com ícones e mensagens explicativas
   - States de carregamento que previnem exibição parcial

## Verificação da Integração

### Como verificar se os dados estão sendo exibidos corretamente

1. **Executar o script de verificação**:
   ``
   python verificar_integracao.py
   ``
   Este script verifica:
   - Se todos os arquivos de dados existem
   - Se todos os endpoints estão respondendo
   - Se a estrutura dos dados está correta

2. **Verificar no console do navegador**:
   - Abrir o console do navegador (F12)
   - Verificar logs de "Dados recebidos do backend"
   - Confirmar que não há erros 404 ou 500

3. **Testes visuais**:
   - Abra cada página do frontend
   - Verifique se há dados em todos os painéis
   - Verifique se os gráficos mostram dados válidos

## Solução de Problemas

### Página em branco ou erros de JavaScript

1. Verifique os logs do console do navegador
2. Execute `npm run build` no diretório frontend para verificar erros de compilação
3. Verifique se o endpoint `/health` está respondendo corretamente

### Gráficos vazios ou "N/A" em muitos campos

1. Verifique se os arquivos JSON em `backend/dados` existem
2. Execute `python backend/gerar_todos_dados_demo.py` para regenerar dados
3. Verifique logs do backend para erros de processamento

### Backend não inicia

1. Verifique logs para erros de importação ou módulos faltantes
2. Execute `python backend/test_imports.py` para verificar dependências
3. Verifique se os diretórios `backend/endpoints` e `backend/dados` existem

## Como adicionar novos dados reais

Para adicionar novos tipos de dados reais à integração:

1. **Backend**:
   - Crie um novo coletor em `backend/utils/`
   - Adicione um novo endpoint em `backend/endpoints/`
   - Registre o endpoint em `backend/core_router.py`
   - Adicione gerador de dados simulados para fallback

2. **Frontend**:
   - Adicione uma nova função de API em `frontend/src/api/backend.js`
   - Crie ou atualize componente que consumirá os dados
   - Implemente tratamento de nullish e fallbacks visuais

## Monitorando a economia de tokens OpenAI

Para monitorar e otimizar o uso de tokens da API OpenAI:

1. Execute o script de análise:
   ``
   python backend/monitor_economia_tokens.py

   ``

2. Verifique o dashboard no arquivo:

   ``
   backend/dados/metricas/uso_tokens.json
   ``

3. Ajuste os parâmetros de consumo em:
   ``
   backend/utils/ai_config.py
   ``

## Inicialização Robusta

Para iniciar o sistema com todas as verificações:

```bash
python iniciar_com_verificacao.py
```

Este script:

1. Gera todos os dados necessários
2. Verifica a integridade dos arquivos
3. Inicia backend e frontend
4. Verifica a integração completa

---

Última atualização: 29 de junho de 2025
