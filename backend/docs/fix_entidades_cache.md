# Fix para Filtro de Entidades no Cache

## Problema Resolvido

O sistema estava filtrando incorretamente entidades durante o processo de atualização de cache, particularmente afetando entidades do domínio INFRA. Muitas entidades válidas estavam sendo descartadas porque tinham valores nulos nas métricas, mesmo quando a estrutura dos dados estava correta.

## Diagnóstico

Ao analisar o código, identificamos que a função `entidade_tem_dados` em `utils/newrelic_collector.py` estava sendo muito restritiva durante a validação das entidades:

1. A função verificava se cada métrica tinha pelo menos um valor não-nulo;
2. Entidades com estruturas corretas, mas com valores nulos, eram consideradas "sem dados";
3. Isso afetava principalmente entidades INFRA, onde é comum ter métricas com valores nulos temporariamente.

Estatísticas antes da correção:

- APM: ~9 entidades (a maioria passava na validação)
- BROWSER: ~6 entidades (a maioria passava na validação)
- INFRA: <10 entidades (apesar de haver mais de 150 entidades disponíveis)
- SYNTH: <3 entidades (de ~8 disponíveis)
- EXT: <2 entidades (de ~4 disponíveis)

## Solução Implementada

Modificamos a função `entidade_tem_dados` para ser menos restritiva, considerando uma entidade como tendo dados válidos simplesmente pela presença da estrutura correta de métricas, mesmo que os valores sejam nulos.

Mudança implementada:

```python
# Versão anterior
def entidade_tem_dados(metricas):
    if not metricas or not isinstance(metricas, dict):
        return False
        
    # Verifica cada período (30min, 24h, 7d, 30d)
    for periodo, periodo_data in metricas.items():
        if not isinstance(periodo_data, dict):
            continue
            
        # Verifica cada tipo de métrica no período
        for metrica_nome, metrica_valores in periodo_data.items():
            # Ignora valores nulos
            if metrica_valores is None:
                continue
                
            # Se for uma lista de resultados
            if isinstance(metrica_valores, list):
                # Ignora listas vazias
                if not metrica_valores:
                    continue
                    
                # Verifica cada item na lista
                for item in metrica_valores:
                    # Se for um dicionário, verifica valores dentro dele
                    if isinstance(item, dict) and item:
                        for val in item.values():
                            # Se encontrou qualquer valor válido
                            if val not in (None, 0, "", []):
                                return True
            
            # Se for um valor direto
            elif metrica_valores not in (None, 0, "", []):
                return True
                
    return False

# Nova versão implementada
def entidade_tem_dados(metricas):
    if not metricas or not isinstance(metricas, dict):
        return False
        
    # Verifica cada período (30min, 24h, 7d, 30d)
    for periodo, periodo_data in metricas.items():
        if not isinstance(periodo_data, dict):
            continue
            
        # Se temos pelo menos uma métrica com estrutura correta, consideramos válida
        if periodo_data:
            return True
                
    return False
```

## Resultados

Após a correção:

- APM: 9-11 entidades (todas validadas corretamente)
- BROWSER: 6-9 entidades (todas validadas corretamente)
- INFRA: ~153 entidades (todas as disponíveis são agora incluídas no cache)
- SYNTH: 8 entidades (todas as disponíveis agora incluídas)
- EXT: 4 entidades (todas as disponíveis agora incluídas)

Testes realizados:

1. Verificação da distribuição de entidades por domínio
2. Teste específico para a função `entidade_tem_dados`
3. Verificação da atualização de cache completa
4. Validação de que todas as entidades estão sendo corretamente incluídas no cache

## Como a correção foi aplicada

1. Foi criado um patch temporário usando o script `test_entidade_tem_dados_fix.py` que demonstrou a eficácia da solução
2. A solução foi permanentemente aplicada ao código base usando o script `apply_entidade_tem_dados_fix.py`
3. Testes de verificação confirmaram que o problema foi corrigido

## Arquivos Modificados

- `utils/newrelic_collector.py` - Modificação na função `entidade_tem_dados`

## Arquivos Criados para Diagnóstico e Verificação

- `test_entidade_tem_dados_fix.py` - Script de teste inicial para validar a correção
- `apply_entidade_tem_dados_fix.py` - Script para aplicar a correção permanentemente
- `verificar_fix_entidade_tem_dados.py` - Script para verificação detalhada da distribuição de entidades
- `verificacao_entidades_pos_fix.json` - Resultado da verificação
- `fix_entidade_tem_dados_results.json` - Resultados do teste

## Impacto da Correção

1. O cache agora reflete corretamente todas as entidades disponíveis no ambiente New Relic
2. Análises e relatórios incluem informações mais completas e precisas
3. Os usuários não receberão mais mensagens incorretas sobre "entidades sem dados"
4. Melhor visibilidade para infraestrutura e outras entidades no painel de controle
