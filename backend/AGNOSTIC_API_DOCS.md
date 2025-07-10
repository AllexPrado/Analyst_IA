# API Inteligente Analyst_IA – Endpoints Agno

Esta documentação descreve os endpoints inteligentes disponíveis via `/agno`, prontos para integração com frontend, automações e sistemas externos.

---

## Endpoints Disponíveis


### 1. Gerar Relatório

**Descrição:** Gera um relatório técnico ou executivo sobre entidades monitoradas, consolidando dados do New Relic e análises inteligentes.

- **POST** `/agno/relatorio`
- **Body:**
  - `tipo` (obrigatório): "tecnico" ou "executivo". Define o formato e detalhamento do relatório.
  - `filtro` (opcional): Objeto com filtros, ex: `{ "entidade": "Api Sites" }` para restringir a entidade analisada.
  
  Exemplo:
  ```json
  {
    "tipo": "tecnico",
    "filtro": { "entidade": "Api Sites" }
  }
  ```
- **Resposta:**
  - `relatorio`: Objeto com o conteúdo do relatório gerado.
  
  Exemplo:
  ```json
  {
    "relatorio": {
      "entidade": "Api Sites",
      "periodo": "7d",
      "metricas": { /* ... */ },
      "alertas": [ /* ... */ ],
      "analise": "Tudo OK"
    }
  }
  ```
- **Erros comuns:**
  - 422 se faltar o campo `tipo` ou se valor inválido.
  - 400 se filtro inválido.

**Quando usar:** Para dashboards, relatórios gerenciais, automações de status e análises técnicas.

---


### 2. Corrigir Entidade

**Descrição:** Executa automação de correção para uma entidade específica, como restart, flush, limpeza de cache, etc.

- **POST** `/agno/corrigir`
- **Body:**
  - `entidade` (obrigatório): Nome da entidade a ser corrigida.
  - `acao` (obrigatório): "corrigir" (padrão) ou outra ação suportada.
  
  Exemplo:
  ```json
  {
    "entidade": "Api Sites",
    "acao": "corrigir"
  }
  ```
- **Resposta:**
  - `resultado`: Objeto com detalhes da automação executada.
  
  Exemplo:
  ```json
  {
    "resultado": {
      "status": "ok",
      "mensagem": "Cache limpo com sucesso."
    }
  }
  ```
- **Erros comuns:**
  - 422 se faltar campo obrigatório.
  - 404 se entidade não encontrada.

**Quando usar:** Para automação de correção, auto-healing, manutenção remota.

---


### 3. Disparar Alerta

**Descrição:** Dispara um alerta customizado para equipes, sistemas ou canais integrados.

- **POST** `/agno/alerta`
- **Body:**
  - `mensagem` (obrigatório): Texto do alerta.
  - `destino` (opcional): Canal ou equipe de destino.
  
  Exemplo:
  ```json
  {
    "mensagem": "Alerta crítico detectado!",
    "destino": "equipe"
  }
  ```
- **Resposta:**
  - `resultado`: Confirmação do disparo do alerta.
  
  Exemplo:
  ```json
  {
    "resultado": {
      "status": "enviado",
      "canal": "equipe"
    }
  }
  ```
- **Erros comuns:**
  - 422 se faltar mensagem.

**Quando usar:** Para alertas automáticos, notificações de incidentes, integrações com Slack, e-mail, etc.

---


### 4. Consultar Histórico

**Descrição:** Retorna o histórico de interações, decisões e ações de uma sessão ou usuário.

- **GET** `/agno/historico?session_id=<id>&limite=<n>`
  - `session_id` (obrigatório): ID da sessão/usuário.
  - `limite` (opcional): Quantidade máxima de registros (padrão: 10).

- **Resposta:**
  - `historico`: Lista de interações, decisões e ações.
  
  Exemplo:
  ```json
  {
    "historico": [
      { "data": "2025-07-09T10:00:00Z", "acao": "relatorio", "detalhe": "Relatório técnico gerado." },
      { "data": "2025-07-09T10:05:00Z", "acao": "correcao", "detalhe": "Cache limpo." }
    ]
  }
  ```
- **Erros comuns:**
  - 422 se faltar session_id.

**Quando usar:** Para exibir histórico ao usuário, auditoria, logs de decisões.

---


### 5. Analisar Intenção

**Descrição:** Analisa o texto enviado e retorna a intenção detectada (ex: consulta, correção, alerta).

- **POST** `/agno/intencao`
- **Body:**
  - `texto` (obrigatório): Texto a ser analisado.
  
  Exemplo:
  ```json
  {
    "texto": "Quais entidades estão com erro?"
  }
  ```
- **Resposta:**
  - `intencao`: Objeto com a intenção detectada.
  
  Exemplo:
  ```json
  {
    "intencao": {
      "tipo": "consulta",
      "entidade": "Api Sites"
    }
  }
  ```
- **Erros comuns:**
  - 422 se faltar texto.

**Quando usar:** Para chatbots, automações baseadas em linguagem natural, UX conversacional.

---


### 6. Executar Playbook

**Descrição:** Executa um playbook (sequência de ações inteligentes) com contexto customizado.

- **POST** `/agno/playbook`
- **Body:**
  - `nome` (obrigatório): Nome do playbook.
  - `contexto` (opcional): Objeto com contexto adicional.
  
  Exemplo:
  ```json
  {
    "nome": "relatorio_tecnico",
    "contexto": { "entidade": "Api Sites" }
  }
  ```
- **Resposta:**
  - `resultado`: Resultado do playbook executado.
  
  Exemplo:
  ```json
  {
    "resultado": {
      "relatorio": { /* ... */ },
      "status": "ok"
    }
  }
  ```
- **Erros comuns:**
  - 422 se faltar nome.

**Quando usar:** Para automações complexas, execuções em lote, rotinas de diagnóstico.

---


### 7. Executar Ação Plugável

**Descrição:** Executa uma ação customizada, como webhook, integração externa, etc.

- **POST** `/agno/acao`
- **Body:**
  - `acao` (obrigatório): Objeto descrevendo a ação (tipo, url, payload, etc).
  
  Exemplo:
  ```json
  {
    "acao": {
      "tipo": "webhook",
      "url": "https://hooks.slack.com/...",
      "payload": { "msg": "Teste" }
    }
  }
  ```
- **Resposta:**
  - `resultado`: Resultado da ação executada.
  
  Exemplo:
  ```json
  {
    "resultado": {
      "status": "ok",
      "mensagem": "Webhook enviado."
    }
  }
  ```
- **Erros comuns:**
  - 422 se faltar campo obrigatório.

**Quando usar:** Para integrações externas, automações plugáveis, notificações customizadas.

---


### 8. Correlacionar Eventos

**Descrição:** Analisa e correlaciona eventos para identificar padrões, picos e anomalias.

- **POST** `/agno/correlacionar`
- **Body:**
  - `eventos` (obrigatório): Lista de eventos a serem correlacionados.
  
  Exemplo:
  ```json
  {
    "eventos": [
      { "tipo": "erro", "timestamp": "2025-07-09T10:00:00Z" },
      { "tipo": "alerta", "timestamp": "2025-07-09T10:05:00Z" }
    ]
  }
  ```
- **Resposta:**
  - `correlacao`: Objeto com padrões e picos identificados.
  
  Exemplo:
  ```json
  {
    "correlacao": {
      "padroes": ["erro-sequencial"],
      "picos": ["10:05"]
    }
  }
  ```
- **Erros comuns:**
  - 422 se faltar eventos.

**Quando usar:** Para análise de incidentes, dashboards de eventos, automação de resposta.

---


### 9. Consultar Contexto/Memória

**Descrição:** Recupera o contexto/memória de uma sessão, útil para UX personalizada e continuidade de conversas.

- **GET** `/agno/contexto?session_id=<id>`
  - `session_id` (obrigatório): ID da sessão/usuário.

- **Resposta:**
  - `contexto`: Objeto com o contexto/memória da sessão.
  
  Exemplo:
  ```json
  {
    "contexto": {
      "usuario": "joao",
      "ultima_acao": "relatorio"
    }
  }
  ```
- **Erros comuns:**
  - 422 se faltar session_id.

**Quando usar:** Para chatbots, UX personalizada, continuidade de processos.

---


### 10. Registrar Feedback

**Descrição:** Registra feedback do usuário sobre respostas, automações ou UX.

- **POST** `/agno/feedback`
- **Body:**
  - `feedback` (obrigatório): Objeto com `mensagem` (texto) e `score` (1-5).
  
  Exemplo:
  ```json
  {
    "feedback": { "mensagem": "Ótima resposta!", "score": 5 }
  }
  ```
- **Resposta:**
  - `resultado`: Confirmação do registro do feedback.
  
  Exemplo:
  ```json
  {
    "resultado": "Feedback registrado."
  }
  ```
- **Erros comuns:**
  - 422 se faltar campo obrigatório.

**Quando usar:** Para avaliação de respostas, melhoria contínua da IA, UX.

---


### 11. Coletar Dados do New Relic (com cache)

**Descrição:** Coleta dados avançados do New Relic (métricas, logs, erros, processos, etc) para uma ou mais entidades, com uso de cache para otimizar custos.

- **POST** `/agno/coletar_newrelic`
- **Body:**
  - `entidade` (opcional): Nome da entidade. Se omitido e `tipo` for "entidades", retorna lista geral.
  - `periodo` (obrigatório): Intervalo de dados. Ex: "7d", "24h", "30min".
  - `tipo` (obrigatório): "metricas" ou "entidades".
  
  Exemplo:
  ```json
  {
    "entidade": "Api Sites",
    "periodo": "7d",
    "tipo": "metricas"
  }
  ```
- **Resposta:**
  - `fonte`: "cache" ou "newrelic" (origem dos dados).
  - `dados`: Objeto com os dados coletados (estrutura varia conforme tipo e entidade).
  
  Exemplo:
  ```json
  {
    "fonte": "cache",
    "dados": {
      "cpu": 12.5,
      "memory": 1024,
      "erros": 0,
      "logs": [ /* ... */ ]
    }
  }
  ```
- **Erros comuns:**
  - 422 se faltar campo obrigatório.
  - 404 se entidade não encontrada.

**Quando usar:** Para dashboards, automações, monitoramento, análise de incidentes, relatórios.

---

---

## Guia de Integração Frontend ↔ Backend Analyst_IA (New Relic/Agno)

### 1. Visão Geral

- Todos os endpoints do backend estão documentados neste arquivo e seguem o padrão REST, retornando sempre JSON.
- O núcleo inteligente (Agno) centraliza automação, relatórios, correção, alertas, histórico, intenção, playbooks, ações, contexto, feedback e coleta de dados do New Relic.
- O endpoint principal para dados do New Relic é `/agno/coletar_newrelic`, que já utiliza cache para otimizar custos e performance.

---

### 2. Como consumir os dados do New Relic no frontend

**Endpoint principal:**

- **POST** `/agno/coletar_newrelic`
- **Body:**
  ```json
  {
    "entidade": "Api Sites", // opcional para tipo 'entidades'
    "periodo": "7d",         // exemplos: '7d', '24h', '30min'
    "tipo": "metricas"       // ou "entidades"
  }
  ```
- **Resposta:**
  ```json
  {
    "fonte": "cache" | "newrelic",
    "dados": { /* dados coletados, estrutura varia conforme tipo */ }
  }
  ```


**Dicas e Política de Coleta:**
- Sempre valide o campo `fonte` para saber se os dados vieram do cache ou de uma consulta nova ao New Relic.
- O campo `dados` pode conter métricas, logs, erros, traces, processos, uso de recursos, etc. Estruture o frontend para tratar diferentes formatos.
- **Atenção:** Para evitar consumo excessivo de tokens e custos, a coleta de dados do New Relic pelo backend é realizada apenas 1 vez a cada 24 horas para cada entidade/tipo/período. Novas requisições dentro desse intervalo retornam os dados do cache.
- O campo `periodo` controla o intervalo de dados retornados, mas a atualização real ocorre a cada 24h. Se precisar de dados mais recentes, consulte a equipe de backend.

---

## Observações e Checklist para Integração Frontend

### 1. Endpoints suportados

O frontend deve consumir **apenas** os endpoints documentados sob `/agno/`. Exemplos principais:

- `/agno/relatorio` (POST): Geração de relatórios técnicos/executivos.
- `/agno/corrigir` (POST): Automação de correção.
- `/agno/alerta` (POST): Disparo de alertas.
- `/agno/historico` (GET): Histórico de interações.
- `/agno/intencao` (POST): Análise de intenção/chat.
- `/agno/playbook` (POST): Execução de playbooks.
- `/agno/acao` (POST): Execução de ações plugáveis.
- `/agno/correlacionar` (POST): Correlação de eventos.
- `/agno/contexto` (GET): Consulta de contexto/memória.
- `/agno/feedback` (POST): Registro de feedback.
- `/agno/coletar_newrelic` (POST): Coleta de dados do New Relic (com cache de 24h).

**Não utilize endpoints antigos** como `/api/`, `/chat`, `/entidades`, `/resumo-geral`, etc. Eles não são mais suportados.

### 2. Exemplo de integração frontend (arquivo backend.js)

```js
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000', // Use sempre a raiz, pois todos os endpoints são /agno/
  timeout: 90000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

const handleApiResponse = async (promise) => {
  try {
    const response = await promise
    if (response.data && response.data.erro) {
      return { erro: true, mensagem: response.data.mensagem || 'Dados indisponíveis no momento.' }
    }
    return response.data
  } catch (error) {
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
      return { erro: true, mensagem: 'Backend não está em execução. Inicie o backend na porta 8000.' }
    }
    if (error.code === 'ECONNABORTED') {
      return { erro: true, mensagem: 'Timeout na requisição. Tente novamente.' }
    }
    if (error.response?.status === 404) {
      return { erro: true, mensagem: 'Endpoint não encontrado no backend.' }
    }
    if (error.response?.status === 500) {
      return { erro: true, mensagem: 'Erro interno do servidor. Verifique os logs do backend.' }
    }
    return { erro: true, mensagem: error?.response?.data?.mensagem || 'Erro ao acessar dados do backend.' }
  }
}

// Exemplos de funções para os novos endpoints:
export const coletarNewRelic = (payload) =>
  handleApiResponse(api.post('/agno/coletar_newrelic', payload))

export const getHistorico = (session_id, limite = 10) =>
  handleApiResponse(api.get(`/agno/historico?session_id=${session_id}&limite=${limite}`))

export const analisarIntencao = (texto) =>
  handleApiResponse(api.post('/agno/intencao', { texto }))

export const registrarFeedback = (feedback) =>
  handleApiResponse(api.post('/agno/feedback', { feedback }))

export const gerarRelatorio = (tipo, filtro) =>
  handleApiResponse(api.post('/agno/relatorio', { tipo, filtro }))

// ...demais funções conforme endpoints documentados

export default api
```

### 3. Política de cache e coleta New Relic

- O backend coleta dados do New Relic apenas 1 vez a cada 24 horas para cada entidade/tipo/período.
- Novas requisições dentro desse intervalo retornam os dados do cache, sem consumir tokens adicionais.
- O frontend deve informar ao usuário quando os dados são de cache (campo `fonte`).
- Caso precise de atualização forçada, consulte a equipe de backend.

### 4. Checklist para integração sem erros

- [ ] Usar apenas endpoints `/agno/` documentados.
- [ ] Validar todos os campos obrigatórios antes de enviar requests.
- [ ] Tratar todos os tipos de resposta (sucesso, erro, dados vazios).
- [ ] Exibir ao usuário a origem dos dados (`fonte`).
- [ ] Usar `session_id` para manter contexto.
- [ ] Testar todos os endpoints relevantes do Agno.
- [ ] Consultar exemplos de payloads e respostas na documentação.
- [ ] Reportar qualquer comportamento inesperado ao backend.

---

Se seguir este guia, o frontend terá acesso a 100% dos recursos do backend e dos dados do New Relic, com performance, segurança e sem surpresas. Para dúvidas ou integrações avançadas, consulte a equipe de backend.

---

### 3. Boas práticas para integração

- **Validação de Payload:** Sempre envie os campos esperados conforme a documentação. Campos ausentes ou tipos errados retornam erro 422.
- **Tratamento de Erros:** Trate respostas HTTP 4xx/5xx no frontend. Exemplo de erro 422:
  ```json
  {
    "detail": [
      {
        "loc": ["body", "periodo"],
        "msg": "field required",
        "type": "value_error.missing"
      }
    ]
  }
  ```
- **Session ID:** Use o campo `session_id` nos endpoints que aceitam para manter contexto/histórico por usuário.
- **Paginação e Limites:** Para endpoints que retornam listas (ex: histórico), utilize os parâmetros de limite/paginação.
- **Feedback:** Utilize `/agno/feedback` para registrar avaliações de respostas e melhorar a IA.

---


### 4. Integração Agent-S ↔ Agno (Automação Inteligente)

#### O que é o Agent-S?
O Agent-S é um agente de automação que monitora eventos, logs e condições do backend, executando ações inteligentes automaticamente via endpoints do Agno. Ele pode corrigir entidades, disparar alertas, registrar histórico e atuar como "auto-healing" do sistema.

#### Como o Agent-S interage com o Agno?
- O Agent-S consome os endpoints REST do Agno, como `/corrigir`, `/alerta`, `/feedback`, etc.
- Todas as ações automáticas do Agent-S são registradas no histórico e podem ser visualizadas pelo frontend.
- O frontend pode exibir status, logs e histórico das ações do Agent-S normalmente, usando os endpoints já documentados.

#### Exemplo de automação do Agent-S (Python):
```python
import requests
AGNO_URL = "http://localhost:8000/agno"
payload = {"entidade": "Api Sites", "acao": "corrigir"}
resp = requests.post(f"{AGNO_URL}/corrigir", json=payload)
print(resp.json())
```

#### Como visualizar as ações do Agent-S no frontend?
- Use `/agno/historico` para listar todas as ações, inclusive as automáticas do Agent-S.
- O campo `mensagem` ou `detalhe` pode indicar que a ação foi executada pelo Agent-S.
- Exemplo de resposta:
```json
{
  "historico": [
    { "data": "2025-07-09T10:10:00Z", "acao": "correcao", "detalhe": "Agent-S: Correção automática executada." },
    { "data": "2025-07-09T10:11:00Z", "acao": "alerta", "detalhe": "Agent-S: Alerta disparado para equipe." }
  ]
}
```

#### Checklist para integração Agent-S
- [x] Agent-S executa automações via endpoints do Agno
- [x] Todas as ações são registradas e visíveis no histórico
- [x] Frontend pode exibir status, logs e histórico normalmente
- [x] Integração transparente, sem necessidade de endpoints extras

---

### 4. Exemplos de uso no frontend

#### Coletar métricas de uma entidade
```js
const response = await fetch('/agno/coletar_newrelic', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    entidade: 'Api Sites',
    periodo: '7d',
    tipo: 'metricas'
  })
});
const data = await response.json();
// data.fonte, data.dados
```

#### Consultar histórico de interações
```js
const response = await fetch('/agno/historico?session_id=sess_20250709&limite=5');
const data = await response.json();
// data.historico
```

#### Registrar feedback
```js
await fetch('/agno/feedback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    feedback: { mensagem: 'Ótima resposta!', score: 5 }
  })
});
```

---

### 5. Dicas para uso avançado

- **Automação:** Use endpoints como `/agno/relatorio`, `/agno/corrigir`, `/agno/alerta`, `/agno/playbook` para automações inteligentes baseadas nos dados do New Relic.
- **Dashboards:** Consuma `/agno/coletar_newrelic` periodicamente para alimentar dashboards em tempo real.
- **Alertas:** Implemente lógica no frontend para disparar alertas automáticos via `/agno/alerta` com base em thresholds dos dados coletados.
- **Contexto Dinâmico:** Use `/agno/contexto` para recuperar o contexto/memória da sessão e personalizar a experiência do usuário.

---

### 6. Observações Finais

- Todos os endpoints são stateless, exceto quando `session_id` é usado.
- O backend já faz cache inteligente dos dados do New Relic, mas o frontend pode exibir ao usuário se os dados são "reais" ou "cache".
- Para dúvidas sobre payloads, consulte sempre a documentação atualizada.
- Em caso de erro inesperado, envie o payload e resposta para a equipe de backend para análise.

---

### 7. Checklist para integração sem erros

- [ ] Validar todos os campos obrigatórios antes de enviar requests.
- [ ] Tratar todos os tipos de resposta (sucesso, erro, dados vazios).
- [ ] Exibir ao usuário a origem dos dados (`fonte`).
- [ ] Usar `session_id` para manter contexto.
- [ ] Testar todos os endpoints relevantes do Agno.
- [ ] Consultar exemplos de payloads e respostas na documentação.
- [ ] Reportar qualquer comportamento inesperado ao backend.

---

### 8. Sobre os logs do backend

- Os logs mostram que a coleta de dados do New Relic está funcionando corretamente, sem erros críticos.
- Warnings do tipo "resposta NRQL sem campo 'results'" são esperados quando não há dados para o período/entidade consultada.
- O backend está pronto para integração total, basta o frontend consumir conforme orientado.

---

Se seguir este guia, o frontend terá acesso a 100% dos recursos do backend e dos dados do New Relic, com performance, segurança e sem surpresas. Para dúvidas ou integrações avançadas, consulte a equipe de backend.

> Última atualização: 09/07/2025
