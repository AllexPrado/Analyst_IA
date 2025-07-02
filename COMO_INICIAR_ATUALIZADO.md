# Guia de Inicialização do Sistema Analyst_IA

Este guia explica como iniciar corretamente o sistema Analyst_IA, com todas as verificações e correções de cache necessárias para garantir que os dados sejam exibidos corretamente.

## Requisitos

- Python 3.8+ instalado
- Node.js 16+ instalado
- Navegador moderno (Chrome, Firefox, Edge)

## Estrutura do Sistema

O sistema é composto de duas partes principais:

1. **Backend**: API FastAPI que fornece dados para o frontend
2. **Frontend**: Aplicação Vue.js que exibe os dados em um dashboard

## Método 1: Inicialização Automatizada (Recomendado)

A forma mais simples é usar o script de inicialização completo:

```powershell
# No Windows
.\INICIAR_SISTEMA_COMPLETO.bat
```

Este script irá:
1. Verificar e corrigir o cache
2. Iniciar o backend
3. Iniciar o frontend

## Método 2: Inicialização Manual (Para Desenvolvimento)

### Passo 1: Verificar e Corrigir o Cache

```powershell
cd backend
python check_and_fix_cache.py
```

Isto garante que o sistema tenha dados de teste válidos se não houver dados reais disponíveis.

### Passo 2: Iniciar o Backend

```powershell
cd backend
python main.py
```

O servidor estará disponível em http://localhost:8000

### Passo 3: Iniciar o Frontend

```powershell
cd frontend
npm run dev
```

O frontend estará disponível em http://localhost:5173

## Método 3: Usando Tarefas do VS Code

O projeto inclui tarefas pré-configuradas no VS Code que podem ser executadas:

1. **Run Frontend Dev**: Inicia o servidor de desenvolvimento do frontend
2. **Verificar e Corrigir Cache**: Verifica e corrige o cache antes de iniciar o backend
3. **Iniciar Backend com Cache Verificado**: Executa a verificação do cache e inicia o backend
4. **Iniciar Sistema Completo**: Inicia tanto o backend quanto o frontend

Para executar uma tarefa, use a paleta de comandos do VS Code (Ctrl+Shift+P) e digite "Tasks: Run Task", então selecione a tarefa desejada.

## Testando o Sistema

Para verificar se o sistema está funcionando corretamente, você pode executar:

```powershell
cd backend
.\test_api.ps1
```

Este script testa todos os endpoints principais e verifica se estão retornando respostas válidas.

## Possíveis Problemas e Soluções

### 1. Tela em Branco no Frontend

- **Solução**: Verifique se o backend está rodando e se o proxy no frontend está configurado corretamente.

### 2. Dados Não Aparecem em Alguns Painéis

- **Solução**: Execute novamente `check_and_fix_cache.py` para regenerar os dados de teste.

### 3. Erro no Chat

- **Solução**: Verifique se o cache foi inicializado corretamente e se o backend está executando sem erros.

### 4. Erro de CORS no Frontend

- **Solução**: Verifique se as configurações de CORS no backend estão permitindo requisições do frontend.

## Estrutura de Dados

Os dados do sistema são organizados em:

- `dados/`: Contém os arquivos JSON com dados para cada módulo
- `historico/`: Contém o cache de dados históricos e de entidades
- `logs/`: Contém logs do sistema

## Melhores Práticas

1. Sempre execute a verificação do cache antes de iniciar o backend
2. Para desenvolvimento, mantenha os dados de teste atualizados
3. Para produção, configure as variáveis de ambiente para acessar dados reais do New Relic
