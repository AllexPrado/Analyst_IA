# Teste de Integração Frontend-Backend - Analyst_IA

## Pré-requisitos
1. **Backend deve estar rodando na porta 8000**
   ```bash
   cd backend
   python main.py
   ```

2. **Frontend deve estar rodando na porta 5173**
   ```bash
   cd frontend
   npm run dev
   ```

## Checklist de Testes

### ✅ 1. Teste de Conectividade
- [ ] Abrir http://localhost:5173
- [ ] Verificar indicador "Backend Online" no canto superior direito
- [ ] Se aparecer "Backend Offline", verificar se o backend está rodando

### ✅ 2. Teste da Página Visão Geral
- [ ] Navegar para a página inicial (/)
- [ ] Verificar se os cards de status carregam dados reais
- [ ] Verificar se não há dados mockados (números fixos como 999, 123, etc.)
- [ ] Observar console do navegador para erros de API

### ✅ 3. Teste dos Cards Críticos
- [ ] Verificar se os 4 cards no final da página carregam:
  - Logs Recentes
  - Alertas Ativos  
  - Dashboards
  - Incidentes Críticos
- [ ] Se aparecer "!" ou erro, verificar logs do backend

### ✅ 4. Teste do Chat IA
- [ ] Navegar para /chat
- [ ] Testar perguntas simples:
  - "Qual o status atual do sistema?"
  - "Mostre os principais alertas"
- [ ] Verificar se a IA responde com dados reais do backend

### ✅ 5. Teste de KPIs
- [ ] Navegar para /kpis
- [ ] Verificar se métricas carregam dados reais
- [ ] Verificar se gráficos são populados com dados do backend

## Resolução de Problemas

### 🔴 Backend Offline
```bash
# 1. Verificar se o backend está rodando
curl http://localhost:8000/health

# 2. Se não estiver, iniciar o backend
cd backend
python main.py
```

### 🔴 Erros de CORS
```bash
# Verificar se o proxy do Vite está configurado corretamente
# Arquivo: frontend/vite.config.js
# Deve ter proxy '/api' -> 'http://localhost:8000'
```

### 🔴 Timeout nas Requisições
```bash
# Aumentar timeout no arquivo backend.js se necessário
# Timeout atual: 90 segundos
```

### 🔴 Dados Não Carregam
1. Abrir DevTools (F12)
2. Ir para aba Network
3. Recarregar a página
4. Verificar se requisições para /api/* estão falhando
5. Verificar resposta das APIs no backend

## Comandos Úteis para Debug

### Frontend
```bash
# Ver logs do frontend
npm run dev

# Build para produção
npm run build
```

### Backend  
```bash
# Ver logs detalhados do backend
python main.py

# Testar endpoints diretamente
curl http://localhost:8000/status
curl http://localhost:8000/health
curl http://localhost:8000/kpis
```

## Estrutura de Resposta Esperada do Backend

### /status
```json
{
  "status": "Operacional",
  "alertas": 5,
  "errosCriticos": 0,
  "dominios": {
    "APM": {"count": 10, "alertas": 2, "erros": 0},
    "INFRA": {"count": 8, "alertas": 1, "erros": 0}
  }
}
```

### /health
```json
{
  "status": "healthy",
  "timestamp": "2025-01-06T10:30:00Z"
}
```

## Logs Importantes

### Frontend Console
- Verificar mensagens de erro da API
- Verificar se dados estão sendo recebidos corretamente

### Backend Console  
- Verificar logs das queries New Relic
- Verificar se não há erros de autenticação
- Verificar se rate limits não estão sendo atingidos

## Validação Final

### ✅ Integração Completa
- [ ] Todos os componentes carregam dados reais
- [ ] Não há componentes de teste (TestComponent, TestChat)
- [ ] Chat IA responde com contexto real
- [ ] Indicador de status do backend está funcionando
- [ ] Tratamento de erro está funcionando corretamente
- [ ] Performance está adequada (< 5s para carregar dados)

---

**Data de criação:** 06/01/2025  
**Última atualização:** 06/01/2025
