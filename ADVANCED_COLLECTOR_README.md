# Sistema New Relic Advanced Collector

## Visão Geral

O Advanced Collector implementa um coletor completo para o New Relic que permite que o sistema Analyst IA tenha acesso a 100% dos dados disponíveis no New Relic, incluindo:

- Métricas padrão (Apdex, Response Time, Error Rate, Throughput)
- Logs detalhados
- Traces completos
- Backtraces de erros
- Queries SQL e desempenho
- Informações de execução de código (módulo, linha de código, tempo)
- Dados de distribuição
- Relacionamentos entre entidades
- Métricas de Kubernetes e infraestrutura
- Dados de funções serverless
- Análise de dashboards e widgets

## Componentes do Sistema

### Arquivos Principais

- `utils/advanced_newrelic_collector.py` - Coletor avançado que utiliza NRQL e GraphQL
- `atualizar_cache_completo.py` - Script para atualizar o cache com todos os dados do New Relic
- `test_advanced_collector.py` - Teste do coletor avançado

### Arquivos Integrados

- `utils/cache.py` - Integração do coletor avançado ao sistema de cache
- `main.py` - Configuração para usar o coletor avançado por padrão
- `cache_integration.py` - Inicialização do sistema de cache avançado

## Configuração e Credenciais

Para utilizar o coletor avançado, você precisa configurar suas credenciais do New Relic:

1. Crie um arquivo `.env` na raiz do projeto baseado no arquivo `.env.example`
2. Preencha as seguintes credenciais:
   - `NEW_RELIC_API_KEY` - API Key com permissões administrativas
   - `NEW_RELIC_QUERY_KEY` - Query Key para consultas NRQL
   - `NEW_RELIC_ACCOUNT_ID` - ID da sua conta no New Relic

Exemplo de arquivo `.env`:
```
NEW_RELIC_API_KEY=NRAK-XXXXXXXXXXXXXXXXXXXXXXXXX
NEW_RELIC_QUERY_KEY=NRQL-XXXXXXXXXXXXXXXXXXXXXXXXX
NEW_RELIC_ACCOUNT_ID=1234567
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXX
```

## Novos Endpoints

### `/api/cache/atualizar_avancado`

Endpoint específico para atualizar o cache usando o coletor avançado. Este endpoint:

- Utiliza o script `atualizar_cache_completo.py` para coletar todos os dados avançados do New Relic
- Armazena os resultados no cache para uso em todo o sistema
- Retorna informações detalhadas sobre a atualização

## Testes do Coletor Avançado

Para validar a implementação do coletor avançado, um script de teste foi criado: `test_advanced_collector.py`.

### Como Executar os Testes

#### Modo 1: Usando Credenciais Reais do New Relic

```bash
# No PowerShell ou CMD
python test_advanced_collector.py
```

#### Modo 2: Usando Dados Simulados (sem credenciais)

```bash
# No PowerShell
.\testar_simulado.ps1

# No CMD
testar_coletor_simulado.bat

# Alternativa manual
SET USE_MOCK_DATA=true
python test_advanced_collector.py
```

O modo de simulação é útil para desenvolvimento e verificação rápida do código sem necessidade de credenciais reais.

### Pré-requisitos para Testes

#### Para Testes com Credenciais Reais:

1. As credenciais do New Relic estão configuradas no arquivo `.env`
2. O arquivo `.env` está na raiz do projeto
3. As credenciais têm permissões suficientes para acessar os dados necessários

#### Para Testes com Dados Simulados:

1. Apenas Python 3.7+ instalado
2. Nenhuma credencial necessária

### Funcionalidades Testadas

O script de testes verifica as seguintes funcionalidades do coletor avançado:

1. **Métricas de Kubernetes**: Testa a coleta de dados de clusters Kubernetes
2. **Métricas de Funções Serverless**: Testa a coleta de dados de funções Lambda
3. **Análise de Dashboards**: Testa a análise de dashboards e extração de NRQL
4. **Extração de NRQL**: Testa a extração de consultas NRQL de todos os dashboards
5. **Dados de Infraestrutura**: Testa a coleta de dados avançados de infraestrutura
6. **Relatórios de Capacidade**: Testa a geração de relatórios de capacidade e uso de recursos
7. **Coleta Completa**: Testa a coleta completa de todos os dados disponíveis

### Resultados e Relatórios

Após a execução dos testes, um relatório detalhado é gerado no arquivo `advanced_collector_test_results.json`. Este relatório contém:

- Resumo dos testes executados
- Status de cada teste (PASSED, FAILED, SKIPPED)
- Detalhes dos resultados ou erros encontrados
- Estatísticas de cobertura

### Resolução de Problemas

Se você encontrar o erro "New Relic API Key não fornecida" ao executar os testes, você tem duas opções:

#### Opção 1: Configurar credenciais reais

1. Crie um arquivo `.env` na raiz do projeto com as credenciais do New Relic:
   ```
   NEW_RELIC_API_KEY=sua_api_key_aqui
   NEW_RELIC_QUERY_KEY=sua_query_key_aqui
   NEW_RELIC_ACCOUNT_ID=seu_account_id_aqui
   ```

2. Certifique-se de que as credenciais estão corretas e não têm espaços extras
3. Verifique se o arquivo `.env` está sendo carregado corretamente

#### Opção 2: Usar dados simulados para testes

Se você não tem acesso às credenciais do New Relic ou está em um ambiente de desenvolvimento sem conectividade, você pode executar os testes com dados simulados:

1. Use o script auxiliar fornecido:
   ```
   # No Windows (PowerShell)
   .\testar_coletor_simulado.ps1
   
   # No Windows (CMD)
   testar_coletor_simulado.bat
   ```

2. Ou execute manualmente definindo a variável de ambiente:
   ```
   # No PowerShell
   $env:USE_MOCK_DATA="true"; python test_advanced_collector.py
   
   # No CMD
   SET USE_MOCK_DATA=true && python test_advanced_collector.py
   
   # No Linux/macOS
   USE_MOCK_DATA=true python test_advanced_collector.py
   ```

O modo de simulação usa a classe `MockNewRelicCollector` em `utils/test_helpers.py` que gera dados realistas para permitir testes sem dependência externa.

> **Nota:** Os testes com dados simulados são úteis para desenvolvimento e validação do código, mas não substituem testes com dados reais antes da implantação em produção.

Para outros erros, verifique o log detalhado em `advanced_collector_test.log`.

### Erros Comuns e Soluções

#### 1. Erros SSL e Timeout

Se você encontrar erros como `ClientConnectionError('Connection lost: SSL shutdown timed out')` ou outros problemas relacionados a SSL, pode ser devido a:

- Problemas de rede ou firewall bloqueando conexões HTTPS
- Certificados SSL expirados ou inválidos
- Problemas de configuração do TLS

**Soluções:**
1. **Verifique sua conexão de rede** - Certifique-se de que você tem acesso à internet e que o firewall não está bloqueando as conexões com api.newrelic.com
2. **Use o modo simulado** - Se você estiver em um ambiente com restrições de rede, use o modo simulado:
   ```powershell
   .\testar_simulado.ps1
   ```
3. **Aumente o timeout** - Se os tempos de resposta forem longos, modifique a constante `DEFAULT_TIMEOUT` no arquivo `advanced_newrelic_collector.py`:
   ```python
   DEFAULT_TIMEOUT = 60.0  # Aumente para 60 segundos ou mais
   ```

#### 2. Método Faltante: `analyze_dashboard_widgets`

Se você encontrar um erro como `'AdvancedNewRelicCollector' object has no attribute 'analyze_dashboard_widgets'`, isso indica que a implementação mais recente foi atualizada e você precisa baixar as atualizações do repositório.

## Criando Arquivo de Credenciais

Para facilitar o uso do coletor avançado, crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```
NEW_RELIC_API_KEY=sua_api_key_aqui
NEW_RELIC_QUERY_KEY=sua_query_key_aqui
NEW_RELIC_ACCOUNT_ID=seu_account_id_aqui
```

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

### Verificando Conectividade

Antes de executar os testes com credenciais reais, recomendamos verificar a conectividade com o New Relic:

```powershell
# Verificação básica de conectividade
python verificar_conectividade_newrelic.py

# Aumentar o timeout se necessário
python verificar_conectividade_newrelic.py --timeout 60
```

Este script irá:
1. Verificar se as credenciais estão configuradas corretamente
2. Testar a conexão com a API do New Relic
3. Fornecer recomendações com base no resultado

Se o teste de conectividade falhar, recomendamos usar o modo de simulação para desenvolvimento.
