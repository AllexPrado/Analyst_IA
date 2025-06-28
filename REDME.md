# 🧠 Analyst_IA — NOC Inteligente com New Relic + OpenAI GPT

Plataforma profissional de monitoramento e análise com IA, unindo **New Relic**, **OpenAI** e **tecnologia frontend interativa (Vue + Tailwind)** para atuar como um verdadeiro **NOC/DevOps/Engenharia de Performance autônomo**.

## 🚀 Funcionalidades

- 🔍 Diagnósticos automatizados de erros, lentidão e gargalos
- 📊 Dashboard interativo com rankings e insights técnicos
- 🤖 Chat com IA que responde técnicos e gestores (GPT-4o)
- 🧠 Cruzamento de dados APM, Browser, Logs, Traces e Banco
- 🛠️ Geração de relatórios técnicos e PDF com um clique
- 📦 Backend FastAPI com integração ao New Relic e OpenAI

## 📁 Estrutura do Projeto

Analyst_IA/
│
├── backend/              # API FastAPI (Diagnóstico com OpenAI + New Relic)
│   ├── main.py
│   └── utils/
│       ├── openai_connector.py
│       ├── newrelic_collector.py
│       ├── analise_cruzada.py
│       ├── persona_detector.py
│       └── ...
│
├── frontend/            # Interface web em Vue 3 + Tailwind
│   ├── public/
│   └── src/
│       ├── components/
│       ├── App.vue
│       └── main.js
│
├── .env                 # Chaves do New Relic e OpenAI
├── Dockerfile
├── docker-compose.yml
└── README.md

## 🔧 Requisitos

- Python 3.11+
- Node.js 18+
- Docker Desktop com WSL2 habilitado
- Conta New Relic com API key
- Conta OpenAI com chave GPT-4o

## ✅ Instalação

### 1. Clone o projeto

```bash
git clone https://github.com/seu-usuario/analyst_ia.git
cd analyst_ia
```

### 2. Configure as variáveis de ambiente

OPENAI_API_KEY=sk-...
NEW_RELIC_API_KEY=...
NEW_RELIC_ACCOUNT_ID=...
OPENAI_MODEL=gpt-4o

## ▶️ Executando sem Docker

### Backend (FastAPI)

```bash
cd backend
python -m venv venv
venv\Scripts\activate         # Windows
source venv/bin/activate     # Linux/Mac
pip install -r ../requirements.txt

uvicorn main:app --reload --port 8000
```

### Frontend (Vue)

```bash
cd frontend
npm install
npm run dev
```

## 🐳 Executando com Docker

```bash
cd Analyst_IA
docker compose up --build
```

## 🌐 Acesso

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend (API): [http://localhost:8000/docs](http://localhost:8000/docs)

## 🧪 Exemplos de Perguntas

- Quais são as APIs mais lentas dos últimos 7 dias?
- Liste os maiores erros de backend de hoje.
- Analise se houve impacto de performance após o último deploy.
- Me mostre o ranking das páginas com pior LCP.
- Quais entidades não estão enviando dados para o New Relic?

## 📝 Recursos Adicionais

- Geração de PDF (relatorios/)
- Geração de Markdown técnico
- Testes técnicos simulados
- Histórico salvo automaticamente (chat_history.json)
- Pronto para ser integrado ao GitHub Actions ou CI/CD

👨‍💻 Autor
Desenvolvido por [Alex Santos Prado]
Profissional em monitoramento, observabilidade e IA aplicada a engenharia de software.

📄 Licença
Este projeto é open-source, mas requer chaves de API do OpenAI e New Relic. Respeite os termos de uso de ambas as plataformas.

---

📌 **Próximo passo:**  
Salve esse conteúdo como `README.md` na raiz do seu projeto.  
Ele serve como **documentação oficial** para você, seu time e seu gestor!

Se quiser, posso te ajudar também a integrar isso com **GitHub Pages**, **vercel**, **Netlify**, ou CI/CD depois. Deseja?
