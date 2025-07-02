# Guia de Inicialização do Sistema Analyst_IA

Este guia contém instruções detalhadas para iniciar o sistema Analyst_IA corretamente, garantindo que todos os componentes funcionem de forma integrada.

## Pré-requisitos

- Python 3.8 ou superior
- Node.js 14 ou superior
- npm 6 ou superior
- Dependências Python instaladas (`pip install -r requirements.txt`)
- Dependências Node.js instaladas (`cd frontend && npm install`)

## Opção 1: Inicialização Unificada (Recomendado)

Para iniciar todo o sistema com um único comando:

```bash
# No Windows (PowerShell)
python start_system.py

# No Linux/MacOS
python3 start_system.py
```

Este script vai:
1. Verificar e corrigir o cache de dados
2. Iniciar o servidor backend (FastAPI)
3. Iniciar o servidor frontend (Vite/Vue)

## Opção 2: Usando Tarefas do VS Code

Se estiver usando o VS Code, pode utilizar a tarefa "Iniciar Sistema Completo":

1. Abra a paleta de comandos (Ctrl+Shift+P ou Cmd+Shift+P)
2. Digite "Run Task" e selecione "Tasks: Run Task"
3. Selecione "Iniciar Sistema Completo"

## Opção 3: Inicialização Manual

### 1. Verificar e corrigir o cache

```bash
cd backend
python check_and_fix_cache.py
```

### 2. Iniciar o backend

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Iniciar o frontend

Em um novo terminal:

```bash
cd frontend
npm run dev
```

## Verificando se o sistema está funcionando

1. API Docs: http://localhost:8000/docs
2. Frontend: http://localhost:5173
3. API Status: http://localhost:8000/api/health

Para testar todos os endpoints da API rapidamente:

```bash
cd backend
python test_api_endpoints.py
```

Para testar apenas o chat:

```bash
cd backend
python test_chat.py
```

## Solução de Problemas

### Backend não inicia

- Verifique se todas as dependências Python estão instaladas: `pip install -r requirements.txt`
- Verifique se o diretório `dados` existe na pasta backend
- Verifique os logs em `backend/logs` para identificar erros específicos

### Frontend não inicia

- Verifique se todas as dependências Node.js estão instaladas: `cd frontend && npm install`
- Verifique se a configuração do proxy no `vite.config.js` está correta
- Tente limpar o cache: `cd frontend && npm cache clean --force && npm install`

### Erros de módulo não encontrado

- Verifique a estrutura de diretórios e os caminhos relativos no código
- Verifique se o Python está usando o ambiente correto com as dependências instaladas

### Dados não aparecem no frontend

- Verifique se o cache foi gerado corretamente: `python backend/check_and_fix_cache.py`
- Teste os endpoints da API diretamente para confirmar que estão retornando dados: `python backend/test_api_endpoints.py`

### Erros no endpoint de chat

- Verifique se o servidor está rodando: `curl http://localhost:8000/api/health`
- Teste o endpoint de chat diretamente: `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d "{\"pergunta\":\"Como está o sistema?\"}"`

## Estrutura do Projeto

```
analyst_IA/
├── backend/
│   ├── dados/              # Dados gerados e cache
│   ├── endpoints/          # Endpoints da API
│   │   ├── chat_endpoints.py
│   │   ├── kpis_endpoints.py
│   │   └── ...
│   ├── historico/          # Cache histórico 
│   ├── logs/               # Logs do sistema
│   ├── utils/              # Utilidades compartilhadas
│   │   ├── cache.py
│   │   ├── cache_advanced.py
│   │   └── ...
│   ├── check_and_fix_cache.py  # Script para verificar e corrigir cache
│   ├── main.py             # Ponto de entrada do backend
│   └── requirements.txt    # Dependências Python
├── frontend/
│   ├── public/             # Arquivos públicos
│   ├── src/                # Código fonte do frontend
│   │   ├── api/            # Integrações com API
│   │   ├── components/     # Componentes Vue
│   │   └── ...
│   ├── index.html          # Página principal
│   └── package.json        # Dependências Node.js
├── start_system.py         # Script para iniciar o sistema completo
├── test_api_endpoints.py   # Testes dos endpoints
└── README.md               # Documentação principal
```

## Roadmap

Após a estabilização do sistema atual, planejamos evoluir para uma arquitetura baseada em:

1. MCP (Multi-Component Pipeline) para fluxos de trabalho modulares e reutilizáveis
2. Framework Agno para agentes autônomos
3. Automação e inteligência artificial avançada

Essa evolução será implementada de forma incremental, garantindo que cada etapa esteja funcionando corretamente antes de avançar para a próxima.
