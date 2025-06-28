# Resolução de Problemas do Analyst IA

Este documento contém informações sobre como resolver problemas comuns encontrados no sistema Analyst IA.

## 1. Erros de Timeout (90000ms exceeded)

O erro "timeout of 90000ms exceeded" geralmente ocorre quando o backend está demorando muito para responder devido a:

1. **Consultas lentas ao New Relic**: A API do New Relic pode ocasionalmente ser lenta, especialmente com consultas complexas.
2. **Processamento pesado no backend**: Análise de muitas entidades e métricas pode sobrecarregar o processamento.
3. **Limitação de recursos**: Servidor com poucos recursos disponíveis para processar as solicitações.

### Soluções Implementadas

- **Timeout ajustável**: O sistema agora utiliza um timeout padrão de 30 segundos para requisições ao New Relic.
- **Mecanismo de retry**: Implementado sistema de retry para lidar com falhas temporárias.
- **Circuit breaker**: Evita sobrecarga de requisições quando o sistema está instável.

### Ajustes Adicionais Possíveis

1. **Reduzir a complexidade das consultas**:

```python
# Arquivo: utils/newrelic_collector.py
DEFAULT_TIMEOUT = 15.0  # Diminua o timeout para consultas mais rápidas
```

1. **Aumentar o número de retentativas com espera exponencial**:

```python
# Arquivo: utils/newrelic_collector.py
MAX_RETRIES = 3  # Aumente para mais tentativas
RETRY_DELAY = 2.0  # Aumente o tempo entre tentativas
```

1. **Adicionar cache de consultas frequentes**:
   - As consultas mais frequentes já são armazenadas em cache
   - O período de cache pode ser ajustado em `utils/cache.py`

## 2. Problemas com Limite de Tokens

O sistema utiliza um limite diário de tokens para evitar custos excessivos com a API da OpenAI.

### Melhorias Implementadas

- **Aumento do limite diário**: O limite foi aumentado para 50.000 tokens (anteriormente 10.000).
- **Reset automático**: O contador agora é automaticamente resetado para 50% quando atinge o limite, permitindo uso contínuo.
- **Comando para reset manual**: Adicionado comando "resetar limite" que pode ser enviado via chat.

### Ajustes Adicionais

1. **Modificar limite diário**:

```python
# Arquivo: utils/openai_connector.py
daily_limit = 100000  # Aumente para permitir mais consultas
```

1. **Desabilitar completamente o limite em ambientes de desenvolvimento**:

```python
# Arquivo: utils/openai_connector.py
if os.getenv("ENVIRONMENT") == "development":
    # Ignorar verificação de limite em ambiente de desenvolvimento
    pass
else:
    # Verificar limite apenas em produção
    if usage_data.get("tokens", 0) > daily_limit * 0.95:
        # resto do código
```

## 3. Problemas com o Sistema de Aprendizado (cara_cinteligente)

O sistema de aprendizado pode apresentar problemas devido a incompatibilidades na interface do módulo.

### Correções Aplicadas

- **Detecção automática de assinatura**: O sistema agora detecta automaticamente a assinatura correta do construtor `LearningEngine`.
- **Tratamento de exceções**: Melhor tratamento de erros para evitar falhas no carregamento.

### Métodos de Diagnóstico

Para verificar se o sistema de aprendizado está funcionando corretamente:

1. Verifique os logs do sistema:

```bash
grep "learning" logs/analyst_ia.log
```

. Verifique se o módulo está sendo inicializado corretamente:

```python
# No terminal interativo:
from utils.learning_integration import learning_integration
print(learning_integration.is_enabled())
```

## 4. Comandos Úteis

### Reset de Limite de Tokens

Envie uma das seguintes mensagens no chat:

- `resetar limite`
- `reset`
- `reset limit`
- `reset token`

### Verificar Status do Sistema

- Acesse a interface web em `http://localhost:5173/`
- Navegue até o painel "Status" para verificar a saúde do sistema

### Logs

Os logs são armazenados em:

- `logs/analyst_ia.log` - Log principal do sistema
- `logs/token_usage.json` - Uso de tokens da API OpenAI

---

## Contato para Suporte

Em caso de problemas persistentes, entre em contato com a equipe de desenvolvimento.

## Documento atualizado em: 27 de junho de 2025
