# Como Executar o Frontend

Se você estiver enfrentando uma tela branca no frontend, siga os passos abaixo para resolver o problema:

## Solução Implementada

1. Identificamos e corrigimos dois problemas principais:

   - **Duplicação do ícone faDatabase** no arquivo `main.js` - Este erro JavaScript estava impedindo o carregamento correto da aplicação.
   - **Problema com a definição de componentes** no arquivo `DomainMetrics.vue` - Usava uma API experimental de Vue 3 (`defineOptions`) que não era compatível com a configuração atual.

2. As correções implementadas foram:
   - Remoção da duplicação de `faDatabase` no `library.add()` do arquivo main.js
   - Atualização do modo de registro de componentes em `DomainMetrics.vue` para usar a sintaxe Vue padrão
   - Restauração da versão estável do componente `AdvancedDataPanel.vue`

## Executando o Frontend

Para executar o frontend, utilize um destes comandos:

```bash
cd frontend
npm run dev
```

Ou simplesmente:

```bash
cd frontend && npm run dev
```

## Verificação

Após iniciar o servidor de desenvolvimento, certifique-se de que:

1. Não há erros no console do navegador
2. A interface está sendo carregada corretamente
3. O componente AdvancedDataPanel está exibindo os dados quando disponíveis

## Solução de Problemas Adicionais

Se você ainda encontrar problemas:

1. Limpe o cache do navegador (Ctrl+F5)
2. Pare o servidor de desenvolvimento e reinicie
3. Verifique se há erros no terminal onde o servidor está sendo executado
