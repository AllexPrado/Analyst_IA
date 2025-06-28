# Como Executar o Frontend do Analyst IA

Este documento explica como executar e testar o frontend do Analyst IA após a implementação completa de todas as páginas.

## Pré-requisitos

- Node.js (versão 14.x ou superior)
- NPM (normalmente vem com o Node.js)
- Backend do Analyst IA em execução (necessário para carregar dados reais)

## Instalação

1. Navegue até a pasta do frontend:

   ```bash
   cd d:\projetos\Analyst_IA\frontend
   ```

2. Instale as dependências:

   ```bash
   npm install
   ```

## Executando o Projeto

1. Para iniciar o servidor de desenvolvimento:

   ```bash
   npm run dev
   ```

2. Acesse o frontend em seu navegador:

   ```url
   http://localhost:5173
   ```

## Páginas Implementadas

Todas as páginas principais estão implementadas e integradas com o backend:

1. **Visão Geral** - Dashboard principal com status, alertas e diagnostico
2. **Cobertura** - Análise de cobertura de monitoramento
3. **KPIs** - Métricas principais de performance
4. **Tendências** - Análise de tendências e previsões
5. **Insights** - Recomendações estratégicas e resumo executivo
6. **Chat IA** - Interface conversacional com assistente inteligente
7. **Core Inteligente** - Painel administrativo do motor cognitivo

## Funcionalidades Implementadas

- ✅ Integração real com backend via API (com fallback para dados visuais)
- ✅ Tema escuro/claro toggle com persistência via Vuex
- ✅ Navegação entre todos os módulos
- ✅ Layout responsivo para diferentes tamanhos de tela
- ✅ Gráficos interativos e visuais
- ✅ Feedback visual para o usuário
- ✅ Design consistente conforme os prints de referência

## Testando o Sistema

1. **Navegação**: Teste a navegação entre todas as páginas principais usando o menu superior.

2. **Toggle Tema**: Use o botão "Dark Mode"/"Light Mode" no canto superior direito para alternar entre os temas.

3. **Integração Backend**: Se o backend estiver em execução, os componentes carregarão dados reais. Caso contrário, serão exibidos dados visuais de exemplo para manter a funcionalidade.

4. **Interatividade**: Experimente os filtros, seleção de períodos, botões e outras interações disponíveis.

5. **Responsividade**: Redimensione a janela do navegador para testar o comportamento responsivo.

## Solução de Problemas

- Se encontrar erros de console relacionados à conexão com a API, verifique se o backend está em execução corretamente.

- Se os componentes visuais não forem renderizados corretamente, verifique se todas as dependências foram instaladas:

  ```bash
  npm install
  ```

- Para problemas de renderização específicos, verifique a versão do navegador (recomendamos Chrome ou Firefox atualizados).
