# Interpretando os Resultados de Status do Sistema

Este documento explica como interpretar os resultados gerados pelos scripts de verificação de status do sistema Analyst IA.

## 1. Resultados do Script `verificar_status_sistema.py`

O script principal `verificar_status_sistema.py` fornece uma visão geral completa do sistema. Aqui está como interpretar os resultados:

### 1.1 Tabela de Status

```
+-------------------+------------+------------------------------------------------+
| Componente        | Status     | Detalhes                                       |
+===================+============+================================================+
| Agentes New Relic | ✅ Ativo   | Verificar logs para detalhes                   |
+-------------------+------------+------------------------------------------------+
| Automações MPC    | ❌ Inativo | Verificar status_automacoes_mpc.json para detalhes |
+-------------------+------------+------------------------------------------------+
```

- **Agentes New Relic**
  - ✅ Ativo: Os agentes estão funcionando corretamente e coletando dados
  - ❌ Inativo: Os agentes não estão funcionando ou não estão coletando dados
  - ❌ Erro: Ocorreu um erro ao verificar o status dos agentes

- **Automações MPC**
  - ✅ Ativo: As automações MPC estão em execução
  - ❌ Inativo: As automações MPC não estão em execução
  - ❌ Erro: Ocorreu um erro ao verificar o status das automações MPC

### 1.2 Tabela de Processos

```
+-------+----------------+------------------------------------------------+
| PID   | Nome           | Comando                                         |
+=======+================+================================================+
| 12345 | python.exe     | python start_unified.py                         |
+-------+----------------+------------------------------------------------+
| 12346 | python.exe     | python core_router.py                           |
+-------+----------------+------------------------------------------------+
```

Esta tabela lista todos os processos relacionados ao sistema que estão em execução atualmente. Se estiver vazia, significa que nenhum processo relacionado ao sistema foi encontrado.

### 1.3 Arquivo de Relatório

O script também gera um arquivo `status_sistema.json` com informações detalhadas sobre o status do sistema. Este arquivo inclui:

- Status dos agentes New Relic
- Status das automações MPC
- Detalhes sobre os processos em execução
- Timestamp da verificação

## 2. Resultados do Script `verificar_agentes_newrelic.py`

O script `verificar_agentes_newrelic.py` verifica especificamente o status dos agentes New Relic. Os logs gerados por este script fornecem informações detalhadas sobre:

- Conexão com a API do New Relic
- Quantidade de entidades monitoradas
- Distribuição de entidades por domínio
- Status de uma entidade de exemplo e suas dependências

Exemplo de interpretação dos logs:

```
INFO - Verificando entidades monitoradas pelo New Relic...
INFO - Encontradas 25 entidades monitoradas pelo New Relic
INFO - APM: 15 entidades
INFO - BROWSER: 5 entidades
INFO - INFRA: 5 entidades
```

- Se o script encontrar entidades, os agentes estão funcionando corretamente
- Se o script não encontrar entidades ou retornar erro, pode haver um problema com os agentes ou com a configuração da API

## 3. Resultados do Script `verificar_automacoes_mpc.py`

O script `verificar_automacoes_mpc.py` verifica o status das automações MPC (Model Context Protocol). O resultado é um objeto JSON com as seguintes informações:

```json
{
  "timestamp": "2025-07-12T19:25:58.193460",
  "configuracoes_mpc": {
    "encontradas": true,
    "quantidade": 1,
    "arquivos": ["status_automacoes_mpc.json"]
  },
  "processos_mpc": {
    "em_execucao": false,
    "quantidade": 0,
    "detalhes": []
  },
  "integracao_newrelic": false,
  "status_geral": "inativo"
}
```

- **configuracoes_mpc**: Indica se existem arquivos de configuração MPC no sistema
- **processos_mpc**: Indica se há processos MPC em execução
- **integracao_newrelic**: Indica se há integração com o New Relic
- **status_geral**: Resumo do status das automações MPC (ativo ou inativo)

## 4. Ações Baseadas nos Resultados

### 4.1 Se os Agentes New Relic Estiverem Inativos

1. Verifique se as chaves de API no arquivo `.env` estão corretas
2. Execute `python verificar_agentes_newrelic.py` para obter mais detalhes
3. Verifique os logs do sistema para erros relacionados ao New Relic
4. Reinicie o sistema com `python start_backend.py`

### 4.2 Se as Automações MPC Estiverem Inativas

1. Execute `python start_unified.py` para iniciar o sistema completo
2. Verifique se o `core_router.py` está funcionando corretamente
3. Verifique se os arquivos de configuração MPC estão presentes e válidos
4. Execute `python verificar_automacoes_mpc.py` novamente para verificar o status

### 4.3 Se o Sistema Estiver Funcionando Corretamente

1. Continue monitorando regularmente com `python verificar_status_sistema.py`
2. Configure alertas no New Relic para notificar sobre problemas
3. Verifique o painel do New Relic para confirmar que os dados estão sendo coletados corretamente

## 5. Resolução de Problemas Comuns

### 5.1 Erro de Conexão com a API do New Relic

```
ERROR - Erro ao verificar agentes New Relic: Erro ao coletar entidades: HTTPError
```

- Verifique se as chaves de API no arquivo `.env` estão corretas
- Verifique se a conexão com a internet está funcionando
- Verifique se o serviço New Relic está operacional

### 5.2 Nenhum Processo MPC em Execução

```json
"processos_mpc": {
  "em_execucao": false,
  "quantidade": 0,
  "detalhes": []
}
```

- Execute `python start_unified.py` para iniciar o sistema
- Verifique se há erros nos logs durante a inicialização
- Verifique se há dependências faltando

### 5.3 Erro ao Processar JSON

```
ERROR - Erro ao processar saída JSON das automações MPC: JSONDecodeError
```

- Verifique se os scripts estão retornando JSON válido
- Verifique se há erros nos logs que podem estar corrompendo a saída
