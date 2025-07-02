# Melhoria da Pipeline de Dados - Frontend

## Melhorias Implementadas

### 1. Criação de Serviço Centralizado para Dados Avançados

Foi criado o arquivo `advancedDataService.js` que implementa uma camada de abstração entre os componentes do frontend e a API do backend. Este serviço oferece as seguintes vantagens:

- **Centralização de chamadas API**: Todas as chamadas relacionadas a dados avançados agora são gerenciadas em um único arquivo.
- **Cache em memória**: Implementação de cache em memória com tempo de expiração configurável (5 minutos por padrão).
- **Interface consistente**: Métodos padronizados para obtenção de diferentes tipos de dados.
- **Melhor gestão de erros**: Tratamento centralizado de erros nas chamadas de API.
- **Redução de código duplicado**: Os componentes não precisam mais implementar lógica de chamada API.

### 2. Integração com o Componente InfraAvancada.vue

O componente `InfraAvancada.vue` foi atualizado para utilizar o novo serviço:

- Substituição das chamadas diretas para o `apiClient` por chamadas ao serviço centralizado.
- Manutenção da lógica existente de tratamento de erros e exibição de estados de carregamento.
- Opção para forçar o refresh dos dados ignorando o cache quando necessário.

## Benefícios para a Pipeline de Dados

### Camada de Abstração Adicional

A inclusão de uma camada de serviço adicional fortalece a pipeline de dados seguindo o padrão:

```
New Relic API -> Backend (Cache) -> API REST -> Serviço Frontend -> Componentes Vue
```

### Melhor Performance

O cache em memória no frontend reduz a quantidade de requisições à API backend para dados que não mudam com frequência, melhorando a performance e a experiência do usuário.

### Manutenção Facilitada

Qualquer mudança nos endpoints ou na forma como os dados são obtidos só precisa ser feita em um único lugar (o serviço), sem necessidade de modificar cada componente individualmente.

### Consistência de Dados

A centralização da lógica de obtenção de dados garante que todos os componentes que utilizem os mesmos dados recebam versões consistentes.

## Próximos Passos

1. **Expandir o serviço** para cobrir outros tipos de dados além dos dados avançados.
2. **Implementar revalidação automática** para atualizar dados em segundo plano.
3. **Adicionar mecanismos de retry** para maior resiliência em caso de falhas temporárias na API.
4. **Integrar com o Vuex/Pinia** para gerenciamento de estado global mais robusto.

## Implementação Técnica

O serviço implementa métodos específicos para cada tipo de dado avançado:

- `getKubernetesData()`: Dados relacionados ao Kubernetes
- `getInfrastructureData()`: Dados detalhados de infraestrutura
- `getTopologyData()`: Dados de topologia de serviços
- `getAllAdvancedData()`: Obtém todos os tipos de dados em paralelo

Cada método implementa:
- Verificação de cache
- Chamada à API quando necessário
- Armazenamento em cache dos resultados
- Tratamento básico de erros
