# Analyst_IA: Sistema Integrado de Monitoramento e Análise

## Sobre o Projeto

Analyst_IA é um sistema integrado para monitoramento e análise de entidades do New Relic, projetado para detectar, correlacionar, analisar e fornecer recomendações sobre incidentes em sua infraestrutura de aplicações.

## Componentes do Sistema

O sistema é composto por três componentes principais:

1. **Backend Principal** - Gerencia a autenticação, sessões e orquestração geral
2. **API de Incidentes** - Coleta, correlaciona e analisa incidentes com entidades do New Relic
3. **Frontend** - Interface para visualização de dashboards e análises

## Requisitos

- Python 3.8+
- Node.js 16+
- New Relic API Key
- New Relic Account ID

## Configuração

1. Clone o repositório
2. Configure as variáveis de ambiente:

   ```env
   NEW_RELIC_API_KEY=sua-api-key
   NEW_RELIC_ACCOUNT_ID=seu-account-id
   ```

3. Instale as dependências do backend:

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Instale as dependências do frontend:

   ```bash
   cd frontend
   npm install
   ```

## Iniciando o Sistema

1. **Backend Principal**

   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **API de Incidentes**

   ```bash
   cd backend
   uvicorn api_incidentes:app --port 8002 --reload
   ```

3. **Frontend**

   ```bash
   cd frontend
   npm run dev
   ```

## Verificando o Sistema

Para verificar se todos os componentes estão funcionando corretamente:

```bash
cd backend
python verificar_sistema.py
```

## Adicionando Dados de Exemplo

Para adicionar dados de exemplo ao sistema:

```bash
curl -X POST http://localhost:8002/adicionar-dados-exemplo
```

## URLs Importantes

- **Backend Principal**: [http://localhost:8000](http://localhost:8000)
- **API de Incidentes**: [http://localhost:8002](http://localhost:8002)
- **Frontend**: [http://localhost:5174](http://localhost:5174)

## Endpoints da API

### Backend Principal

- `GET /api/status` - Status do sistema
- `GET /api/entidades` - Lista de entidades do New Relic

### API de Incidentes

- `GET /incidentes` - Lista completa de incidentes
- `GET /entidades` - Entidades correlacionadas com incidentes
- `GET /resumo` - Estatísticas de incidentes
- `GET /analise/{incidente_id}` - Análise detalhada de um incidente
- `GET /status-cache` - Status do cache de dados
- `GET /correlacionar` - Força correlação de incidentes e entidades
- `GET /analise_causa_raiz/{incidente_id}` - Análise de causa raiz
- `POST /adicionar-dados-exemplo` - Adiciona dados de exemplo

## Arquivos Importantes

- `backend/main.py` - Ponto de entrada do backend principal
- `backend/api_incidentes.py` - API de incidentes e correlação
- `backend/coletor_new_relic.py` - Ponte para coleta de dados do New Relic
- `backend/utils/newrelic_collector.py` - Coleta de dados do New Relic
- `frontend/src/components/Dashboard.vue` - Componente principal do dashboard

## Recursos Adicionais

Para mais detalhes sobre a implementação e funcionalidades, consulte:

- [RELATORIO_FINAL.md](RELATORIO_FINAL.md) - Relatório detalhado de implementação
- [backend/verificar_sistema.py](backend/verificar_sistema.py) - Script para verificação do sistema

## Contribuição

Para contribuir com o projeto, por favor, siga as instruções em [CONTRIBUINDO.md](CONTRIBUINDO.md).
