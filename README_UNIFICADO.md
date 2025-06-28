# Analyst-IA: Sistema Unificado

Este documento contém instruções sobre como iniciar corretamente o sistema Analyst-IA após as correções de unificação do backend e frontend.

## Visão Geral

O Analyst-IA foi unificado para usar apenas um backend principal que serve todos os dados necessários para o frontend. As principais melhorias incluem:

- Remoção de múltiplos backends concorrentes
- Correção do endpoint de chat
- Garantia de dados reais em todas as visualizações
- Implementação de componentes à prova de falhas no frontend
- Adição do endpoint `/api/health` para monitoramento

## Como Iniciar o Sistema

### 1. Iniciar o Backend Unificado

Execute o script unificado para iniciar o backend:

```bash
python start_unified_backend.py
```

Este script irá:

- Encerrar quaisquer instâncias antigas do backend
- Iniciar apenas o backend unificado na porta 8000
- Configurar todos os diretórios necessários

### 2. Iniciar o Frontend

Em um novo terminal, navegue até a pasta do frontend e execute:

```bash
cd frontend
npm install
npm run dev
```

O frontend estará disponível em: [http://localhost:5173](http://localhost:5173)

## Verificação do Sistema

Para verificar se o sistema está funcionando corretamente, execute:

```bash
python validar_frontend_backend.py
```

Este script verifica todos os endpoints críticos e valida a comunicação entre o frontend e o backend.

## Solução de Problemas

### Se o Chat não funcionar

1. Verifique se existe o parâmetro 'temperatura' sendo passado para a função `gerar_resposta_ia()`. Este parâmetro não é suportado e causa erro.
2. Verifique se a chave da API OpenAI está configurada corretamente.
3. Confirme que o backend está utilizando o arquivo `unified_backend.py`.

### Se os dados não aparecerem no frontend

1. Verifique o arquivo `vite.config.js` para garantir que o proxy está configurado corretamente para a porta 8000.
2. Confirme que todas as entidades estão sendo processadas corretamente pelo backend.
3. Confirme que o componente `SafeApexChart.vue` está sendo utilizado para renderizar os gráficos.

## Arquivos Principais

- `unified_backend.py`: Backend unificado com todos os endpoints necessários
- `start_unified_backend.py`: Script para iniciar o backend unificado
- `validar_frontend_backend.py`: Script para validar a comunicação entre frontend e backend

## Endpoints Disponíveis

- `/api/health`: Verifica o estado de saúde do backend
- `/api/status`: Fornece informações sobre o cache e as entidades
- `/api/entidades`: Retorna a lista de entidades com métricas
- `/api/kpis`: Retorna KPIs consolidados
- `/api/cobertura`: Retorna dados de cobertura de monitoramento
- `/api/tendencias`: Retorna dados de análise de tendências
- `/api/insights`: Retorna insights gerados automaticamente
- `/api/chat`: Endpoint para conversa com a IA técnica
