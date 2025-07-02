# Integrando Dados Reais do New Relic no Analyst_IA

Este documento detalha o processo de integração de dados reais do New Relic no sistema Analyst_IA. A partir de agora, o sistema pode operar tanto com dados simulados (como estava anteriormente) quanto com dados reais extraídos diretamente da API do New Relic.

## 1. Visão Geral da Integração

O sistema foi ampliado para suportar a coleta, processamento e visualização de dados reais do New Relic, incluindo:

- Dados de infraestrutura Kubernetes
- Métricas detalhadas de infraestrutura
- Dados de topologia de serviços
- Aplicações e métricas de desempenho
- Funções serverless

### 1.1 Benefícios da Integração com Dados Reais

- **Diagnósticos precisos**: Baseados em dados reais do ambiente
- **Insights acionáveis**: Informações atualizadas para tomada de decisão
- **Visualizações completas**: Dashboards alimentados com dados reais
- **Análise preditiva**: Possibilidade de identificar tendências com base em dados históricos reais

## 2. Pré-requisitos

Para usar dados reais do New Relic, você precisará de:

- **Account ID do New Relic**: Identificador da sua conta
- **API Key do New Relic**: Chave de API com permissões de leitura

### 2.1 Configuração das Credenciais

As credenciais podem ser fornecidas de duas formas:

#### Variáveis de Ambiente (Recomendado)

```bash
# Windows (PowerShell)
$env:NEW_RELIC_ACCOUNT_ID = "seu_account_id"
$env:NEW_RELIC_API_KEY = "sua_api_key"

# Windows (CMD)
set NEW_RELIC_ACCOUNT_ID=seu_account_id
set NEW_RELIC_API_KEY=sua_api_key

# Linux/Mac
export NEW_RELIC_ACCOUNT_ID=seu_account_id
export NEW_RELIC_API_KEY=sua_api_key
```

#### Parâmetros de Linha de Comando

Os scripts de integração aceitam as credenciais como parâmetros:

```bash
python integrar_dados_reais_newrelic.py --account-id seu_account_id --api-key sua_api_key
```

## 3. Novos Scripts e Funcionalidades

### 3.1 Integração de Dados Reais

O script `integrar_dados_reais_newrelic.py` é responsável por coletar, transformar e armazenar dados reais do New Relic:

- **Coleta de dados**: Usa a API do New Relic para obter dados completos
- **Transformação**: Converte os dados para o formato usado pelo frontend
- **Armazenamento**: Salva os dados no sistema de cache para uso pelo backend/frontend
- **Modo simulado**: Continua suportando dados simulados quando credenciais não estão disponíveis

### 3.2 Sincronização Periódica

O script `sincronizar_periodico_newrelic.py` mantém os dados atualizados periodicamente:

- **Agendamento**: Executa a sincronização em intervalos configuráveis
- **Execução em segundo plano**: Pode rodar como um serviço contínuo
- **Logs detalhados**: Mantém registros das sincronizações
- **Opção de execução única**: Pode ser executado uma única vez com flag `--once`

### 3.3 Inicialização do Sistema com Dados Reais

Os scripts `iniciar_sistema_com_dados_reais.py` e `iniciar_sistema_com_dados_reais.bat` iniciam o sistema completo com dados reais:

1. Verifica credenciais do New Relic
2. Integra dados reais ou simulados conforme disponibilidade
3. Inicia sincronização periódica em segundo plano
4. Inicia o backend e frontend do sistema

## 4. Arquivos de Cache e Formato de Dados

Os dados reais são armazenados nos seguintes arquivos de cache:

- `kubernetes_metrics.json`: Métricas de clusters, nodes e pods Kubernetes
- `infrastructure_detailed.json`: Métricas detalhadas de hosts e serviços
- `service_topology.json`: Dados de topologia e relacionamento entre serviços
- `applications_metrics.json`: Métricas de aplicações
- `serverless_functions.json`: Dados de funções serverless

### 4.1 Estrutura de Dados

Cada arquivo de cache segue uma estrutura específica para atender às necessidades do frontend:

#### Kubernetes

```json
{
  "clusters": [...],
  "nodes": [...],
  "pods": [...],
  "summary": {
    "total_clusters": 3,
    "total_nodes": 10,
    ...
  }
}
```

#### Infraestrutura

```json
{
  "hosts": [...],
  "services": [...],
  "summary": {
    "total_hosts": 25,
    ...
  }
}
```

#### Topologia

```json
{
  "nodes": [...],
  "edges": [...],
  "summary": {
    "total_services": 15,
    ...
  }
}
```

## 5. Relatório de Integração

Após cada integração de dados reais, é gerado um relatório `relatorio_integracao_dados_reais.json` contendo:

- Timestamp da integração
- Modo de operação (real ou simulado)
- Status dos arquivos de cache
- Informações sobre tamanho e última modificação dos arquivos

Este relatório é útil para diagnosticar problemas de integração e verificar se os dados estão sendo atualizados corretamente.

## 6. Modo de Operação: Real vs. Simulado

O sistema opera em dois modos:

- **Modo Real**: Usa dados extraídos diretamente da API do New Relic
- **Modo Simulado**: Usa dados gerados internamente quando credenciais não estão disponíveis

O modo de operação é determinado automaticamente pela presença das credenciais do New Relic. Se as credenciais não estiverem disponíveis, o sistema entra em modo simulado, garantindo que sempre haja dados para visualização.

## 7. Monitoramento e Logs

Todas as operações de integração e sincronização geram logs detalhados:

- `logs/integracao_dados_reais.log`: Log das operações de integração
- `logs/sincronizacao_periodica.log`: Log das operações de sincronização periódica
- `logs/iniciar_sistema_real.log`: Log de inicialização do sistema com dados reais

## 8. Troubleshooting

### 8.1 Problemas Comuns e Soluções

#### Credenciais Inválidas

**Sintoma**: Mensagem "Erro ao extrair dados do New Relic" nos logs

**Solução**: Verifique se as credenciais estão corretas e têm as permissões necessárias

#### Erros de API Rate Limiting

**Sintoma**: Falhas intermitentes na coleta de dados

**Solução**: Aumente o intervalo de sincronização para evitar rate limiting

#### Cache Desatualizado

**Sintoma**: Dados desatualizados no frontend

**Solução**: Execute `python integrar_dados_reais_newrelic.py` para forçar uma atualização

## 9. Próximos Passos

Para continuar melhorando a integração com dados reais:

1. **Implementar cache de dados históricos**: Armazenar dados históricos para análise de tendências
2. **Adicionar alertas proativos**: Usar dados reais para gerar alertas automáticos
3. **Expandir cobertura de dados**: Integrar mais tipos de dados do New Relic
4. **Otimizar visualizações**: Criar visualizações específicas para cada tipo de dados real

## 10. Conclusão

A integração de dados reais do New Relic no sistema Analyst_IA representa um avanço significativo na capacidade de diagnosticar e analisar problemas em ambientes de produção. Com dados reais, as visualizações e recomendações do sistema se tornam mais precisas e acionáveis, permitindo decisões mais informadas e rápidas.

Para começar a usar dados reais, configure as credenciais do New Relic conforme descrito na seção 2 e execute o script `iniciar_sistema_com_dados_reais.py` ou `iniciar_sistema_com_dados_reais.bat`.

---

*Última atualização: 28 de maio de 2023*
