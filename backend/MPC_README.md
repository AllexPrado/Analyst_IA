# MPC (Model Context Protocol) - Documentação

## Visão Geral

O MPC (Model Context Protocol) é um sistema de comunicação entre agentes inteligentes que permite:

1. **Comunicação estruturada** entre componentes do sistema
2. **Contexto compartilhado** entre diferentes agentes
3. **Coordenação de ações** através de agentes especializados
4. **Automação inteligente** para diagnóstico e resolução de problemas

## Hierarquia de Agentes

O sistema MPC implementa uma hierarquia de agentes:

1. **Agno** - Agente principal de orquestração
   - Recebe mensagens em linguagem natural
   - Coordena ações com outros agentes
   - Mantém contexto da conversação

2. **Agent-S** - Agente de serviço
   - Executa tarefas específicas sob comando do Agno
   - Realiza diagnósticos e correções automáticas
   - Monitora continuamente o sistema

3. **Agentes especializados** - Executam tarefas específicas
   - Diagnóstico: Analisa o estado do sistema
   - Correção: Resolve problemas identificados
   - Otimização: Melhora desempenho do sistema
   - Segurança: Verifica vulnerabilidades
   - Coleta: Coleta dados e métricas

## Como Iniciar o Sistema

### Passo 1: Iniciar o Servidor MPC

O servidor MPC precisa estar em execução para que os agentes possam se comunicar:

```
.\iniciar_servidor_mpc.bat
```

ou

```
python mpc_server.py
```

> **IMPORTANTE:** O servidor MPC roda por padrão na porta 10876, enquanto o backend principal utiliza a porta 8000. Isso permite que ambos funcionem simultaneamente sem conflitos.

### Passo 2: Conversar com o Agno

Para conversar com o Agno, utilize o script interativo:

```
.\falar_com_agno.bat
```

ou

```
python conversar_com_agno.py
```

## Exemplos de Uso

### Exemplo Básico - Conversa Interativa

O modo mais simples é usar o script interativo:

```
python conversar_com_agno.py
```

Exemplo de conversa:
```
Você: Como está o sistema hoje?
Agno: Analisei o sistema e todos os serviços estão operando normalmente. 
      O uso de CPU está em 23%, memória em 45% e disco em 62%.

Você: Alguma recomendação para melhorar o desempenho?
Agno: Realizei otimizações no sistema, incluindo ajustes no cache e 
      nas consultas de banco de dados. Melhorei o tempo de resposta
      em aproximadamente 15%.
```

### Exemplo Avançado - Usando a API Python

Para uso programático, utilize o módulo `agno_interface.py`:

```python
from core_inteligente.agno_interface import AgnoInterface

# Criar interface e iniciar sessão
agno = AgnoInterface()
session_id = agno.iniciar_sessao()

# Enviar mensagem
resposta = await agno.enviar_mensagem("Preciso de um diagnóstico do sistema")
print(resposta["mensagem"])

# Verificar status dos agentes
status = await agno.verificar_status()
print(status)
```

## Scripts Disponíveis

| Script | Descrição |
|--------|-----------|
| `iniciar_servidor_mpc.bat` | Inicia o servidor MPC para comunicação entre agentes |
| `falar_com_agno.bat` | Interface de linha de comando simples para conversar com o Agno |
| `conversar_com_agno.py` | Interface de linha de comando mais robusta para conversar com o Agno |
| `exemplo_agno.py` | Exemplos de diferentes formas de comunicação com o Agno |
| `mpc_status_panel.py` | Interface gráfica para monitorar o status dos agentes |
| `mpc_cli.py` | Ferramenta de linha de comando para interagir com agentes MPC |

## Módulos Principais

| Módulo | Descrição |
|--------|-----------|
| `core_inteligente/mpc_agent_communication.py` | Biblioteca principal para comunicação com agentes |
| `core_inteligente/agno_interface.py` | Interface simplificada para comunicação com o Agno |
| `core_inteligente/agent_tools.py` | Ferramentas e ações disponíveis para os agentes |
| `core_inteligente/agno_agent.py` | Implementação do agente Agno |
| `core_inteligente/context_storage.py` | Armazenamento e gestão de contexto |

## Fluxo de Comunicação

O fluxo de comunicação funciona da seguinte forma:

1. **Usuário → Agno**: Envio de mensagem em linguagem natural
2. **Agno → Agent-S**: Tradução da intenção em comandos específicos
3. **Agent-S → Agentes especializados**: Execução de tarefas específicas
4. **Agentes → Agent-S → Agno → Usuário**: Retorno dos resultados

## Configuração

A configuração dos agentes é armazenada em `config/mpc_agents.json`. Este arquivo é criado automaticamente na primeira execução.

Exemplo de configuração:
```json
{
  "agents": [
    {
      "id": "diagnostico",
      "name": "Agente de Diagnóstico",
      "description": "Realiza diagnósticos do sistema e identifica problemas",
      "endpoint": "/diagnose",
      "enabled": true
    },
    ...
  ],
  "base_url": "http://localhost:10876/agent",
  "timeout": 30,
  "retry_attempts": 3,
  "retry_delay": 5
}
```

## Perguntas Frequentes

### Como adicionar um novo agente?

1. Adicione-o ao arquivo de configuração `config/mpc_agents.json`
2. Implemente o endpoint correspondente no servidor MPC
3. Atualize a documentação conforme necessário

### Como resolver problemas de porta em uso?

Se você encontrar erros de "porta em uso" (Errno 10048) ao iniciar o servidor MPC:

1. Verifique se já existe uma instância do servidor MPC rodando
2. Use o script `diagnosticar_integracao_mpc.py` para diagnóstico automático
3. Use o script `verificar_mpc.py` para checar o status atual do servidor MPC
4. Tente uma porta alternativa usando `python mpc_server.py --port 12345`

### Como o Agent-S sabe o que fazer?

O Agent-S possui um loop automático (`agent_s_auto_loop`) que executa a cada 60 segundos para:
1. Realizar diagnósticos do sistema
2. Aplicar correções automáticas quando necessário
3. Otimizar o desempenho do sistema

### Como funciona a passagem de contexto?

O contexto é mantido pela classe `ContextStorage` e cada sessão possui um ID único. O Agno utiliza este contexto para manter o histórico da conversa e proporcionar respostas mais relevantes.
