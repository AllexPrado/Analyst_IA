# Exemplos de Requisições e Respostas dos Endpoints Analyst_IA

## 1. /health
**Requisição:**
```
GET /health
```
**Resposta:**
```json
{"status": "ok"}
```

---

## 2. /api/incidentes
### a) Sem eventos encontrados
**Requisição:**
```
GET /api/incidentes
```
**Resposta:**
```json
{"erro": true, "mensagem": "Nenhum evento válido de incidente encontrado na conta New Relic.", "eventos_disponiveis": [], "timestamp": "2025-07-09T15:52:15.419094"}
```

### b) Com eventos encontrados (exemplo fictício)
**Resposta:**
```json
{"erro": false, "mensagem": "Incidentes encontrados.", "eventos_disponiveis": [
  {"id": "123", "nome": "Erro API", "status": "aberto", "inicio": "2025-07-09T14:00:00"}
], "timestamp": "2025-07-09T15:55:00.000000"}
```

---

## 3. /api/chat
### a) Sem mensagem
**Requisição:**
```
POST /api/chat
Body: {"mensagem": ""}
```
**Resposta:**
```json
{"erro": true, "mensagem": "Mensagem não pode ser vazia."}
```

### b) Com mensagem válida
**Requisição:**
```
POST /api/chat
Body: {"mensagem": "Explique o último incidente."}
```
**Resposta:**
```json
{"erro": false, "resposta": "O último incidente registrado foi 'Erro API', iniciado em 2025-07-09T14:00:00."}
```

---

## 4. /api/analise-causa-raiz
**Requisição:**
```
POST /api/analise-causa-raiz
Body: {"incidente_id": "123"}
```
**Resposta:**
```json
{"erro": false, "causa_raiz": "Falha de autenticação na API externa.", "acoes_recomendadas": ["Revisar credenciais", "Monitorar logs"]}
```

---

## 5. /api/status-cache
**Requisição:**
```
GET /api/status-cache
```
**Resposta:**
```json
{"status": "ok", "cache_atualizado": true, "ultima_atualizacao": "2025-07-09T15:00:00"}
```

---

Esses exemplos podem ser usados na apresentação, documentação ou para testes rápidos via Postman/curl.
