# Analyst_IA: Sistema Integrado de Monitoramento e Análise (Versão Avançada)

## Sobre o Projeto

Analyst_IA é um sistema integrado para monitoramento e análise de entidades do New Relic, projetado para detectar, correlacionar, analisar e fornecer recomendações sobre incidentes em sua infraestrutura de aplicações. Esta versão foi aprimorada com o coletor avançado do New Relic e sistema avançado de economia de tokens.

## Recursos Avançados

### Coletor Avançado New Relic

O sistema agora utiliza o coletor avançado que obtém todos os tipos de dados disponíveis na plataforma New Relic:

- **Métricas Tradicionais**: Apdex, Response Time, Error Rate, Throughput
- **Logs Detalhados**: Mensagens de log com contexto completo
- **Traces Distribuídos**: Fluxos de execução entre serviços
- **Queries SQL**: Consultas SQL com parâmetros e tempos de execução
- **Backtraces de Erros**: Pilhas de erros detalhadas
- **Métricas de Infraestrutura**: CPU, Memória, Disco, Rede

### Sistema de Economia de Tokens

O sistema foi aprimorado para economizar tokens da API OpenAI através de:

- **Filtragem Rigorosa**: Apenas entidades com dados reais são processadas (economia de 30-60%)
- **Processamento Inteligente**: Eliminação automática de dados nulos/vazios
- **Monitoramento de Economia**: Acompanhamento e visualização da economia de tokens
- **Coleta Avançada Otimizada**: Integração entre coletor avançado e filtros rigorosos

Para mais detalhes, consulte:

- [OTIMIZACAO_TOKENS.md](backend/OTIMIZACAO_TOKENS.md) - Detalhes técnicos da otimização
- [README_ECONOMIZADOR_TOKENS.md](backend/README_ECONOMIZADOR_TOKENS.md) - Guia completo do sistema de economia
- [RESUMO_INTEGRACOES.md](RESUMO_INTEGRACOES.md) - Resumo das integrações realizadas
- [BACKUP_E_RECUPERACAO.md](BACKUP_E_RECUPERACAO.md) - Procedimentos de backup e recuperação

## Componentes do Sistema

O sistema é composto por três componentes principais:

1. **Backend Principal** – Gerencia autenticação, sessões e orquestração geral.
2. **API de Incidentes** – Coleta, correlaciona e analisa incidentes com entidades do New Relic.
3. **Frontend** – Interface para visualização de dashboards e análises.

## Requisitos

- Python 3.8 ou superior
- Node.js 16 ou superior
- Chave de API do New Relic (`NEW_RELIC_API_KEY`)
- ID da Conta New Relic (`NEW_RELIC_ACCOUNT_ID`)
- Chave de API da OpenAI (`OPENAI_API_KEY`)

## Segurança e Dados Sensíveis

**IMPORTANTE**: Este projeto trabalha com dados sensíveis que não devem ser expostos publicamente.

- **Arquivos .env**: Nunca comite arquivos `.env` no repositório. Use sempre os arquivos `.env.example` como modelo e crie seus próprios arquivos `.env` localmente.
- **Chaves de API**: As chaves de API do New Relic e OpenAI são altamente sensíveis e nunca devem ser compartilhadas.
- **Dados de cache**: Os arquivos de cache em `backend/historico/` e `backend/contexts/` contêm dados sensíveis do New Relic e não devem ser compartilhados.
- **Logs**: Os arquivos de log podem conter informações sensíveis e devem ser mantidos apenas localmente.

Para preparar o projeto para um commit seguro:

```bash
# Verifique se não há dados sensíveis sendo rastreados pelo git
git status
# Se necessário, remova arquivos sensíveis do rastreamento (sem apagar os arquivos)
git rm --cached .env backend/.env frontend/.env
git rm --cached -r backend/historico/ backend/contexts/ logs/
```

## Configuração Inicial

1. Clone este repositório
2. Crie arquivos `.env` no diretório raiz, na pasta `backend` e na pasta `frontend` baseados nos respectivos arquivos `.env.example` fornecidos
3. Execute o script de instalação de dependências

   ```bash
   python install_dependencies.py
   
   # Para versão otimizada com economia de tokens
   pip install -r backend/requirements_otimizado.txt
   
   # Verificar se todas as dependências estão instaladas
   python backend/verificar_dependencias.py
   ```

## Como Executar

### Opção 1: Sistema Completo (Recomendado)

Execute o script de inicialização para iniciar todo o sistema:

```bash
python start_all.py
```

### Opção 2: Sistema Otimizado com Economia de Tokens

Execute o script de coleta otimizada para economizar tokens:

```bash
cd backend
python executar_coleta_otimizada.py
```

Depois monitore a economia de tokens:

```bash
python monitor_economia_tokens.py
```

### Opção 3: Iniciar Cada Componente Separadamente

1. Inicie o backend principal:

   ```bash
   cd backend
   python start_backend.py
   ```

2. Inicie o frontend:

   ```bash
   cd frontend
   npm run dev
   ```

## Acessando o Sistema

- Frontend: [http://localhost:5173](http://localhost:5173)
- API Principal: [http://localhost:8000/api](http://localhost:8000/api)
- Documentação da API: [http://localhost:8000/docs](http://localhost:8000/docs)

## Funcionalidades Principais

### Monitoramento em Tempo Real

- Dashboard com KPIs das aplicações
- Métricas de performance (Apdex, Throughput, Erro)
- Alertas e incidentes detectados

### Análise por IA

- Diagnóstico automático de problemas
- Correlação entre alertas e métricas
- Sugestões de resolução baseadas nos padrões detectados

### Relatórios e Documentação

- Geração de relatórios em PDF
- Documentação de incidentes
- Histórico de análises e resoluções

## Economia de Recursos

Esta versão implementa diversas otimizações para redução do consumo de tokens da OpenAI:

1. **Caching inteligente**: Armazena respostas frequentes
2. **Truncagem adaptativa**: Reduz o contexto conforme necessário
3. **Filtragem de entidades**: Processa apenas entidades relevantes
4. **Compressão semântica**: Resumo de incidentes antes da análise
5. **Circuit breaker**: Evita chamadas desnecessárias à API

## Solução de Problemas

Se encontrar algum erro, verifique:

- Logs em `logs/analyst_ia.log`
- Status da API em `/api/health`
- Configuração de credenciais no arquivo `.env`

Para problemas específicos, consulte a documentação completa em `/docs/troubleshooting.md`.

## Contribuição

Para contribuir com este projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nome-da-feature`)
3. Faça commit das suas alterações (`git commit -m 'Adiciona nova feature'`)
4. Faça push para a branch (`git push origin feature/nome-da-feature`)
5. Abra um Pull Request

## Licença

Este projeto é licenciado sob a licença MIT - veja o arquivo LICENSE.md para detalhes.
