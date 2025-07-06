# Como usar o endpoint de eventos disponíveis

## Endpoint auxiliar

Agora existe o endpoint `/api/eventos_disponiveis` que retorna todos os eventos detectados na sua conta New Relic via NRQL.

### Exemplo de uso

- Acesse: `http://localhost:8000/api/eventos_disponiveis` (ajuste porta se necessário)
- O retorno será:

```json
{
  "eventos_disponiveis": ["NrConsumption"],
  "total": 1,
  "timestamp": "2025-07-04T16:50:00.000Z"
}
```

## Como usar
- Use este endpoint para descobrir quais eventos estão realmente disponíveis na sua conta New Relic.
- Se não houver eventos de log/incidente, será necessário configurar a ingestão desses dados no New Relic.
- Você pode informar o nome do evento ao time de desenvolvimento para ajustar queries customizadas, se necessário.

## Observação
- Os endpoints `/logs` e `/incidentes` agora sempre tentam usar qualquer evento disponível, mesmo que não seja um dos candidatos padrão.
- Se ainda assim não houver dados, o sistema retorna o nome do evento utilizado e a lista de eventos disponíveis para facilitar o diagnóstico.
