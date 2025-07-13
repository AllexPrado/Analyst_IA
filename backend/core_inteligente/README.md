# Core Inteligente - MPC (Model Context Protocol)

Este diretório contém o núcleo inteligente do projeto Analyst_IA, implementado usando o protocolo MPC (Model Context Protocol).

## O que é MPC?

O MPC (Model Context Protocol) é um protocolo para comunicação estruturada entre modelos de IA e sistemas/agentes. Ele permite:

1. Comunicação bidirecional entre agentes e o sistema principal
2. Passagem de contexto entre diferentes componentes do sistema
3. Automação baseada em IA para diagnóstico e resolução de problemas
4. Interface consistente para diferentes tipos de agentes inteligentes

## Arquitetura do MPC no Analyst_IA

A arquitetura do MPC no projeto Analyst_IA é composta por:

1. **Agentes Especializados**: Componentes de IA com funções específicas
2. **Router MPC**: Componente central que coordena a comunicação entre agentes
3. **Contexto Compartilhado**: Mecanismo para compartilhar informações entre agentes
4. **Ferramentas de Diagnóstico**: Utilitários para monitorar e depurar o sistema

## Agentes Disponíveis

| ID | Nome | Descrição | Endpoint |
|----|------|-----------|----------|
| diagnostico | Agente de Diagnóstico | Realiza diagnósticos do sistema e identifica problemas | /diagnose |
| correcao | Agente de Correção Automática | Corrige problemas identificados no sistema | /autofix |
| otimizacao | Agente de Otimização | Otimiza o desempenho do sistema | /optimize |
| seguranca | Agente de Segurança | Realiza verificações de segurança no sistema | /security_check |
| coleta | Agente de Coleta de Dados | Coleta dados de métricas e eventos do sistema | /coletar_newrelic |

## Como se Comunicar com os Agentes

### Usando o Módulo `mpc_agent_communication.py`

O módulo `mpc_agent_communication.py` fornece uma interface simplificada para comunicação com os agentes MPC.

#### Exemplo Básico:

```python
from core_inteligente.mpc_agent_communication import send_agent_command

async def exemplo_comunicacao():
    # Enviar comando para o agente de diagnóstico
    resposta = await send_agent_command(
        agent_id="diagnostico",
        action="run_diagnostic",
        parameters={"scope": "full"},
        context={"urgency": "high"}
    )
    
    print(f"Status: {resposta.status}")
    print(f"Dados: {resposta.data}")
    
    # Se houver erro
    if resposta.status == "error":
        print(f"Erro: {resposta.error_message}")
```

### Enviar Comando para Todos os Agentes

```python
from core_inteligente.mpc_agent_communication import broadcast_to_agents

async def exemplo_broadcast():
    # Enviar o mesmo comando para todos os agentes
    respostas = await broadcast_to_agents(
        action="status_update",
        parameters={"check_health": True}
    )
    
    for agent_id, resposta in respostas.items():
        print(f"Agente {agent_id}: {resposta.status}")
```

### Verificar Status dos Agentes

```python
from core_inteligente.mpc_agent_communication import get_agent_status

async def exemplo_status():
    # Verificar status de todos os agentes
    status = await get_agent_status()
    print(f"Status dos agentes: {status}")
    
    # Ou verificar status de um agente específico
    status_diagnostico = await get_agent_status("diagnostico")
    print(f"Status do agente de diagnóstico: {status_diagnostico}")
```

### Consultar Histórico de Comunicações

```python
from core_inteligente.mpc_agent_communication import get_agent_history

def exemplo_historico():
    # Obter as últimas 10 comunicações com todos os agentes
    historico = get_agent_history(limit=10)
    
    # Ou obter histórico de um agente específico
    historico_diagnostico = get_agent_history(agent_id="diagnostico", limit=10)
```

## Configuração dos Agentes

A configuração dos agentes é armazenada em `config/mpc_agents.json`. Você pode editar este arquivo para:

1. Adicionar/remover agentes
2. Ativar/desativar agentes específicos
3. Modificar endpoints e comportamentos dos agentes
4. Configurar tempos limite e tentativas de reconexão

## Uso Avançado

### Criando um Novo Agente

Para criar um novo agente, siga estas etapas:

1. Implemente um novo endpoint no router de agentes
2. Adicione o agente ao arquivo de configuração `config/mpc_agents.json`
3. Reinicie o serviço MPC para que o novo agente seja carregado

### Personalização de Contextos

Os contextos são estruturas de dados importantes no MPC. Eles podem conter:

- Metadados sobre a requisição
- Estado atual do sistema
- Informações históricas relevantes
- Parâmetros de configuração

### Diagnóstico e Depuração

Para diagnosticar problemas com agentes MPC:

1. Verifique os logs em `logs/mpc_communication_history.json`
2. Use o script `verificar_automacoes_mpc.py` para verificar o status geral
3. Envie comandos de diagnóstico específicos aos agentes

## Integração com outros Sistemas

O MPC foi projetado para integrar facilmente com:

- Sistema de monitoramento (local ou New Relic)
- APIs externas para coleta de dados adicionais
- Mecanismos de alertas e notificações
- Painéis de controle e visualização de dados

## Exemplos Práticos

### Diagnóstico Completo do Sistema

```python
import asyncio
from core_inteligente.mpc_agent_communication import send_agent_command

async def diagnostico_completo():
    resposta = await send_agent_command(
        agent_id="diagnostico",
        action="run_diagnostic",
        parameters={
            "scope": "full",
            "include_metrics": True,
            "include_logs": True,
            "include_errors": True
        }
    )
    
    if resposta.status == "success":
        print("Diagnóstico completo realizado com sucesso!")
        print(f"Resultado: {resposta.data}")
    else:
        print(f"Erro no diagnóstico: {resposta.error_message}")

# Executar o diagnóstico
asyncio.run(diagnostico_completo())
```

### Otimização Automática

```python
import asyncio
from core_inteligente.mpc_agent_communication import send_agent_command

async def otimizar_sistema():
    resposta = await send_agent_command(
        agent_id="otimizacao",
        action="optimize_system",
        parameters={
            "target_areas": ["cache", "database", "api_endpoints"],
            "aggressive_mode": False,
            "backup_first": True
        }
    )
    
    if resposta.status == "success":
        print("Sistema otimizado com sucesso!")
        print(f"Melhorias aplicadas: {resposta.data.get('improvements_applied')}")
        print(f"Economia estimada: {resposta.data.get('estimated_savings')}")
    else:
        print(f"Erro na otimização: {resposta.error_message}")

# Executar a otimização
asyncio.run(otimizar_sistema())
```
