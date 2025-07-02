# Configuração de Dados Reais do New Relic

Este documento explica como configurar e usar dados reais do New Relic no sistema Analyst_IA, em vez dos dados simulados padrão.

## Pré-requisitos

Para usar dados reais, você precisa:

1. **Conta no New Relic**: Uma conta ativa na plataforma [New Relic](https://newrelic.com/)
2. **API Key**: Uma chave de API válida com permissões para leitura de dados
3. **Account ID**: O ID da sua conta New Relic

## Obter suas credenciais do New Relic

1. Faça login no [New Relic One](https://one.newrelic.com/)
2. Acesse o menu do usuário no canto superior direito
3. Selecione **API keys**
4. Copie sua **API Key** existente ou crie uma nova com permissões de leitura
5. O **Account ID** pode ser encontrado na URL quando você está logado: `https://one.newrelic.com/<ACCOUNT_ID>/...`

## Configuração do sistema

### Método 1: Usando o arquivo .env (Recomendado)

1. **Crie um arquivo `.env`** na raiz do projeto (use o arquivo `.env.sample` como modelo)

2. **Adicione suas credenciais**:

```
NEW_RELIC_API_KEY=sua_api_key_aqui
NEW_RELIC_ACCOUNT_ID=seu_account_id_aqui
```

3. **Execute o script de verificação** para validar sua configuração:

```bash
python verificar_config_dados_reais.py
```

### Método 2: Usando variáveis de ambiente

**Windows (PowerShell)**:

```powershell
$env:NEW_RELIC_ACCOUNT_ID = "seu_account_id"
$env:NEW_RELIC_API_KEY = "sua_api_key"
```

**Linux/Mac**:

```bash
export NEW_RELIC_ACCOUNT_ID=seu_account_id
export NEW_RELIC_API_KEY=sua_api_key
```

## Integrando Dados Reais

Após configurar as credenciais, você precisa sincronizar os dados reais do New Relic:

```bash
# Sincronização manual uma única vez
python integrar_dados_reais_newrelic.py

# Para visualizar mais opções
python integrar_dados_reais_newrelic.py --help
```

## Verificação da Integração

Após a sincronização, um relatório será gerado em `relatorio_integracao_dados_reais.json`. Você pode verificar o status da integração usando:

```bash
python verificar_config_dados_reais.py
```

## Sincronização Periódica (Opcional)

Para manter os dados sempre atualizados, configure uma sincronização periódica:

```bash
# Sincroniza a cada 30 minutos (padrão)
python sincronizar_periodico_newrelic.py

# Sincroniza a cada hora
python sincronizar_periodico_newrelic.py --intervalo 60
```

## Iniciando o Sistema com Dados Reais

Após configurar e sincronizar os dados reais, você pode iniciar o sistema completo:

```bash
# Windows
iniciar_sistema_com_dados_reais.bat

# Linux/Mac ou PowerShell
python iniciar_sistema_com_dados_reais.py
```

## Solução de Problemas

### Problemas comuns:

1. **Erro "Credenciais inválidas"**: Verifique se suas credenciais foram digitadas corretamente no arquivo `.env`

2. **Erro "Falha na conexão"**: Verifique:
   - Se você tem acesso à internet
   - Se seu firewall não está bloqueando as requisições para o New Relic
   - Se suas credenciais estão corretas e ativas

3. **Dados não aparecem na interface**: Execute:
   ```bash
   python check_and_fix_cache.py
   ```
   
4. **Erros de sintaxe no frontend (Failed to parse source)**:
   - Verifique os arquivos JavaScript em `frontend/src/api/` quanto a erros de sintaxe
   - Certifique-se de que não há caracteres Unicode não ASCII nos arquivos .js
   - Verifique se todos os blocos de código estão corretamente fechados

5. **Usando dados reais mas vendo dados simulados**: Verifique se você usou o script correto para iniciar o sistema:
   ```bash
   # Para Linux/Mac ou CMD:
   python iniciar_sistema_com_dados_reais.py
   
   # Para PowerShell:
   .\iniciar_sistema_com_dados_reais.ps1
   ```

## Alternando entre Dados Reais e Simulados

Você pode alternar entre dados reais e simulados configurando a variável `USE_SIMULATED_DATA` no arquivo `.env`:

```
# Para forçar o uso de dados simulados mesmo com credenciais válidas
USE_SIMULATED_DATA=true

# Para usar dados reais (quando credenciais estão disponíveis)
USE_SIMULATED_DATA=false
```

## Conclusão

Ao seguir estas instruções, você poderá configurar o Analyst_IA para trabalhar com dados reais do New Relic, proporcionando análises e visualizações com base no seu ambiente real de produção.
