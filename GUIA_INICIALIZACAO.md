# Guia de Inicialização Rápida - Analyst IA

Este guia explica como iniciar e visualizar dados reais no sistema Analyst IA.

## Requisitos

- Python 3.8 ou superior
- Node.js 16 ou superior
- npm 7 ou superior

## Iniciando o Sistema Completo

Para iniciar tanto o backend quanto o frontend com um único comando:

```bash
python iniciar_sistema.py
```

Este script irá:

1. Gerar dados de demonstração realistas
2. Iniciar o servidor backend na porta 8000
3. Iniciar o servidor frontend na porta 5173
4. Monitorar os processos e encerrar ambos quando você pressionar Ctrl+C

## Iniciando os Componentes Separadamente

### Backend

Para iniciar apenas o backend:

```bash
cd backend
python start_with_endpoints.py
```

O servidor estará disponível em <http://localhost:8000>

### Frontend

Para iniciar apenas o frontend:

```bash
cd frontend
npm run dev
```

A interface estará disponível em <http://localhost:5173>

## Gerando Dados de Demonstração

Para gerar apenas os dados de demonstração sem iniciar os servidores:

```bash
cd backend
python gerar_dados_demo.py
```

Isso criará arquivos JSON no diretório `backend/dados/` que serão servidos pela API.

## Visualizando Dados nas Páginas

Após iniciar o sistema, você pode acessar as diferentes páginas para visualizar os dados:

1. **Visão Geral** - [http://localhost:5173/](http://localhost:5173/)
   - Mostra resumo geral do ambiente monitorado
   - Exibe alertas ativos e status das entidades

2. **Cobertura** - [http://localhost:5173/cobertura](http://localhost:5173/cobertura)
   - Apresenta estatísticas de cobertura por domínio
   - Gráfico histórico de evolução da cobertura

3. **KPIs** - [http://localhost:5173/kpis](http://localhost:5173/kpis)
   - Exibe métricas-chave como Apdex, uptime e throughput
   - Apresenta comparativos e tendências recentes

4. **Tendências** - [http://localhost:5173/tendencias](http://localhost:5173/tendencias)
   - Gráficos de séries temporais para métricas principais
   - Análise comparativa entre períodos

5. **Insights** - [http://localhost:5173/insights](http://localhost:5173/insights)
   - Recomendações estratégicas baseadas nos dados
   - Métricas de ROI e impacto financeiro

6. **Chat IA** - [http://localhost:5173/chat](http://localhost:5173/chat)
   - Interface para consultas em linguagem natural
   - Análises contextualizadas com os dados coletados

## Personalizando os Dados

Para personalizar os dados exibidos, você pode:

1. Editar os arquivos JSON diretamente em `backend/dados/`
2. Modificar as funções geradoras em `backend/gerar_dados_demo.py`
3. Implementar coleta de dados reais substituindo as funções geradoras nos endpoints

## Solução de Problemas

### Dados não aparecem no frontend

- Verifique se os arquivos JSON estão presentes em `backend/dados/`
- Confirme que o backend está em execução na porta 8000
- Verifique a existência de erros no console do navegador
- Teste os endpoints diretamente: [http://localhost:8000/api/insights](http://localhost:8000/api/insights)

### Erro ao iniciar o servidor

- Verifique se as portas 8000 e 5173 estão disponíveis
- Confirme que todas as dependências foram instaladas
- Verifique permissões de escrita no diretório `backend/dados/`

### Frontend mostra tela em branco

- Verifique erros no console do navegador
- Confirme que não há conflitos nas importações do Vue
- Tente limpar o cache do navegador (Ctrl+F5)
