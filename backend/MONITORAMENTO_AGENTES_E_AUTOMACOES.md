# Monitoramento e Gerenciamento de Agentes New Relic e Automações MPC

Este documento fornece instruções sobre como verificar o status, monitorar e gerenciar os agentes do New Relic e as automações MPC no sistema Analyst IA.

## 1. Verificação de Status

### 1.1 Verificação Rápida de Status

Para uma verificação rápida do status do sistema, execute:

```bash
python verificar_status_sistema.py
```

Este comando mostrará uma tabela resumida com o status dos agentes New Relic e das automações MPC, além de listar processos relevantes em execução.

### 1.2 Verificação Detalhada de Agentes New Relic

Para verificar especificamente o status dos agentes New Relic:

```bash
python verificar_agentes_newrelic.py
```

Este comando verifica:
- Conexão com a API do New Relic
- Entidades monitoradas
- Coleta de dependências
- Funcionamento geral dos agentes

### 1.3 Verificação Detalhada de Automações MPC

Para verificar especificamente o status das automações MPC:

```bash
python verificar_automacoes_mpc.py
```

Este comando verifica:
- Arquivos de configuração MPC
- Processos MPC em execução
- Integração com New Relic
- Status geral das automações

## 2. Arquivos de Log e Diagnóstico

Os seguintes arquivos de log e diagnóstico são gerados:

- `status_sistema.json` - Visão geral do sistema
- `status_automacoes_mpc.json` - Detalhes sobre as automações MPC
- Logs em `./logs/` - Logs detalhados do sistema

## 3. Como Garantir que os Agentes Estão Funcionando

Os agentes do New Relic funcionam automaticamente uma vez que:

1. As chaves API estão configuradas corretamente no arquivo `.env`
2. O coletor do New Relic está integrado ao sistema (já implementado)
3. As entidades estão sendo monitoradas no painel do New Relic

Para confirmar que os agentes estão funcionando corretamente:

- Verifique se há entidades sendo monitoradas (usando `verificar_agentes_newrelic.py`)
- Confira se as dependências estão sendo coletadas corretamente
- Verifique no painel do New Relic se os dados estão sendo recebidos

## 4. Como Garantir que as Automações MPC Estão Funcionando

As automações MPC (Model Context Protocol) funcionam automaticamente uma vez que:

1. O serviço `core_router.py` esteja em execução
2. Os arquivos de configuração MPC estejam presentes
3. A integração com o New Relic esteja funcionando

Para confirmar que as automações MPC estão funcionando corretamente:

- Verifique se há processos MPC em execução (usando `verificar_automacoes_mpc.py`)
- Confira se os arquivos de configuração estão presentes
- Verifique se as ações automáticas estão sendo executadas conforme esperado

## 5. Inicializando o Sistema Manualmente

Se o sistema não estiver em execução, você pode iniciá-lo com:

```bash
python start_unified.py  # Inicia o backend unificado com suporte a MPC
```

Para iniciar apenas o coletor do New Relic:

```bash
python start_backend.py  # Inicia apenas o backend com agentes New Relic
```

## 6. Solução de Problemas

### 6.1 Agentes New Relic

Se os agentes New Relic não estiverem funcionando:

1. Verifique se as chaves API no arquivo `.env` estão corretas
2. Confirme se a conexão com a API do New Relic está funcionando
3. Verifique os logs para erros específicos
4. Reinicie o backend com `python start_backend.py`

### 6.2 Automações MPC

Se as automações MPC não estiverem funcionando:

1. Verifique se o `core_router.py` está em execução
2. Confirme se os arquivos de configuração MPC estão presentes
3. Verifique os logs para erros específicos
4. Reinicie o sistema com `python start_unified.py`

## 7. Métricas e Monitoramento Contínuo

Para monitoramento contínuo:

1. Configure alertas no New Relic para notificar sobre problemas
2. Execute o script `verificar_status_sistema.py` periodicamente (pode ser agendado)
3. Verifique os logs regularmente para identificar possíveis problemas

## 8. Considerações de Performance

Para garantir o melhor desempenho:

1. Ajuste os parâmetros de coleta no arquivo `newrelic_collector.py`
2. Otimize as consultas GraphQL para reduzir o uso de recursos
3. Configure o RateLimitController para evitar limites de API
4. Monitore o uso de recursos do sistema (CPU, memória)
