# Analyst_IA - Frontend

Frontend moderno em Vue.js 3 para o sistema de análise inteligente Analyst_IA, integrado com backend Python e dados reais do New Relic.

## 🚀 Quick Start

### Windows
```bash
# Executar script automatizado
.\start.bat
```

### Linux/Mac
```bash
# Dar permissão e executar script automatizado
chmod +x start.sh
./start.sh
```

### Manual
```bash
# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm run dev

# Abrir no navegador
# http://localhost:5173
```

## 🏗️ Arquitetura

### Stack Tecnológica
- **Vue.js 3** - Framework reativo
- **Vue Router** - Roteamento SPA
- **Vuex** - Gerenciamento de estado
- **Tailwind CSS** - Estilização
- **Font Awesome** - Ícones
- **ApexCharts** - Gráficos interativos
- **Axios** - Cliente HTTP
- **Marked** - Renderização Markdown

### Estrutura de Pastas
```
src/
├── api/                    # Camada de API
│   ├── backend.js         # Endpoints do backend
│   └── axios.js           # Configuração Axios
├── components/            # Componentes Vue
│   ├── pages/            # Páginas principais
│   ├── ui/               # Componentes de UI
│   └── tabs/             # Componentes de tabs
├── utils/                # Utilitários
├── composables/          # Composables Vue 3
├── router.js             # Configuração de rotas
├── store.js              # Store Vuex
└── main.js               # Ponto de entrada
```

## 🔌 Integração com Backend

### Configuração de Proxy
```javascript
// vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

### Endpoints Disponíveis
- `GET /api/status` - Status geral do sistema
- `GET /api/health` - Health check do backend
- `GET /api/kpis` - Indicadores de performance
- `GET /api/logs` - Logs recentes
- `GET /api/alertas` - Alertas ativos
- `GET /api/incidentes` - Incidentes críticos
- `POST /api/chat` - Chat com IA

### Tratamento de Erros
```javascript
// Resposta padrão de erro
{
  erro: true,
  mensagem: "Descrição do erro"
}
```

## 🧩 Componentes Principais

### 1. VisaoGeral.vue
- Dashboard principal com status do sistema
- Cards de métricas críticas
- Gráficos de incidentes e latência
- Diagnóstico da IA

### 2. ChatPanel.vue
- Interface de chat com IA
- Integração com backend para respostas contextuais
- Formatação Markdown das respostas
- Histórico de conversas

### 3. BackendStatus.vue
- Indicador de status do backend
- Health check automático
- Feedback visual de conectividade

### 4. CriticalDataCard.vue
- Cards reutilizáveis para exibir métricas
- Carregamento automático de dados
- Tratamento de erro integrado

## 🔧 Utilitários

### apiValidation.js
```javascript
import { validateApiData, sanitizeApiData, safeApiCall } from '@/utils/apiValidation'

// Validar dados da API
const isValid = validateApiData(data, 'array')

// Sanitizar dados para exibição
const safeValue = sanitizeApiData(value, 'N/A')

// Chamada segura à API
const { error, data } = await safeApiCall(() => getStatus())
```

## 🎨 Estilização

### Tema Escuro
- Paleta consistente em tons de cinza
- Cores de destaque: azul, verde, amarelo, vermelho
- Gradientes sutis para profundidade
- Hover effects e transições suaves

### Responsividade
- Mobile-first design
- Grid responsivo com Tailwind
- Componentes adaptáveis a diferentes telas

## 🚦 Status e Validação

### Indicadores de Status
- **Verde**: Sistema operacional
- **Amarelo**: Alertas ativos
- **Vermelho**: Erros críticos
- **Cinza**: Status desconhecido

### Validação de Dados
- Verificação de conectividade com backend
- Fallbacks para dados indisponíveis
- Tratamento de timeouts e erros de rede

## 🔍 Debug e Troubleshooting

### Logs do Console
```javascript
// Verificar logs de API
console.log('Resposta da API:', response)

// Verificar erros de conexão
console.error('Erro na API:', error)
```

### DevTools
1. Abrir DevTools (F12)
2. Aba Network - verificar requisições
3. Console - verificar erros JavaScript
4. Vue DevTools - inspecionar estado

### Problemas Comuns

#### Backend Offline
```bash
# Verificar se backend está rodando
curl http://localhost:8000/health

# Iniciar backend se necessário
cd ../backend && python main.py
```

#### CORS/Proxy Issues
```bash
# Verificar configuração do proxy no vite.config.js
# Reiniciar servidor de desenvolvimento
npm run dev
```

#### Timeout nas Requisições
```javascript
// Aumentar timeout no axios (backend.js)
timeout: 90000 // 90 segundos
```

## 📦 Build e Deploy

### Desenvolvimento
```bash
npm run dev        # Servidor de desenvolvimento
```

### Produção
```bash
npm run build      # Build para produção
npm run serve      # Preview do build
```

### Variáveis de Ambiente
```bash
# .env.local
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=Analyst_IA
```

## 🧪 Testes

### Manual Testing
1. Seguir checklist em `TESTE_INTEGRACAO.md`
2. Verificar todos os endpoints
3. Testar cenários de erro
4. Validar responsividade

### Automated Testing (Futuro)
- Unit tests com Vitest
- E2E tests com Playwright
- Component testing com Vue Test Utils

## 📈 Performance

### Otimizações
- Lazy loading de componentes
- Compressão de assets
- Caching de requisições
- Debounce em inputs

### Monitoramento
- Time to First Byte (TTFB)
- Largest Contentful Paint (LCP)
- First Input Delay (FID)
- Cumulative Layout Shift (CLS)

## 🤝 Contribuição

### Code Style
- ESLint configurado
- Prettier para formatação
- Conventional commits
- TypeScript (futuro)

### Guidelines
1. Usar composables para lógica reutilizável
2. Componentes pequenos e focados
3. Props tipadas e validadas
4. Tratamento de erro consistente

---

**Desenvolvido com ❤️ para análise inteligente de infraestrutura**
