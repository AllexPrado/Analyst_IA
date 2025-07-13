# MUDANÇA PARA O PLANO GRATUITO DO NEW RELIC

## Contexto

A empresa recebeu uma cobrança de mais de R$ 7 mil do New Relic, devido principalmente ao alto volume de dados gerados pelo monitoramento de Browser. Em resposta, a gestão decidiu cancelar o plano pago e mudar para o plano gratuito.

## Limitações do Plano Gratuito

O plano gratuito do New Relic possui as seguintes limitações:

1. **Ingestão de dados limitada a 100 GB/mês**
   - Depois disso, a API retorna erros 402 (Payment Required)
   
2. **Apenas 1 usuário de plataforma completo**
   - Acesso limitado às ferramentas administrativas
   
3. **500 verificações sintéticas gratuitas/mês**
   - Limitação nas verificações de disponibilidade e performance

4. **Sem suporte técnico oficial**
   - Apenas recursos de autoajuda e comunidade

5. **Retenção de dados reduzida**
   - Dados históricos limitados

## Alterações Implementadas

Para adaptar o sistema ao plano gratuito, foram implementadas as seguintes modificações:

### 1. Sistema de Verificação de Plano (utils/newrelic_plan_checker.py)

- Detecta automaticamente se estamos no plano gratuito
- Adapta o comportamento do sistema para respeitar limites
- Usa cache mais agressivo para reduzir chamadas de API

### 2. Otimização de Coleta (otimizar_coleta_newrelic.py)

- Monitora o uso de dados em relação ao limite
- Aplica diferentes níveis de otimização (baixo, médio, alto)
- Reduz automaticamente a quantidade de dados coletados
- Limita entidades monitoradas quando próximo ao limite

### 3. Status do Sistema Atualizado (verificar_status_sistema.py)

- Inclui informações sobre o plano atual
- Mostra uso de dados e limites
- Fornece alertas quando o uso se aproxima dos limites

## Como Reduzir o Consumo de Dados

Para manter o sistema funcionando sem exceder os limites do plano gratuito, considere:

1. **Desativar monitoramento de Browser**
   - Esta foi a principal fonte do alto custo anterior
   
2. **Monitorar apenas entidades críticas**
   - Priorize APIs e serviços essenciais

3. **Aumentar o uso de cache**
   - Reduzir a frequência de consultas ao New Relic

4. **Armazenar dados históricos localmente**
   - Usar bancos de dados locais para análises de longo prazo

5. **Filtrar logs antes do envio**
   - Enviar apenas logs de erros e eventos críticos

## Verificando o Status do Sistema

Para verificar o status atual do sistema e o uso de dados:

```powershell
# Verificar status geral (inclui informações de plano)
python verificar_status_sistema.py

# Verificar e otimizar coleta de dados
python otimizar_coleta_newrelic.py

# Forçar nova verificação de uso (ignorar cache)
python otimizar_coleta_newrelic.py --force
```

## Impacto nas Funcionalidades

A mudança para o plano gratuito pode afetar:

1. **Alertas em tempo real** - Podem ser atrasados devido ao cache
2. **Análises históricas** - Dados históricos limitados
3. **Dashboard** - Algumas métricas podem não estar disponíveis
4. **Verificações automáticas** - Redução na frequência

O sistema foi adaptado para continuar funcionando com estas limitações, priorizando o monitoramento de componentes críticos.

## Monitoramento de Custos

O script `otimizar_coleta_newrelic.py` ajudará a monitorar o consumo de dados e evitar custos inesperados. Execute-o regularmente (pelo menos semanalmente) para garantir que o sistema está dentro dos limites gratuitos.
