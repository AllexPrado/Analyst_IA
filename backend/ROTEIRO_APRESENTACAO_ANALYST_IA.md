# Roteiro de Apresentação Analyst_IA

## 1. Prova de Vida do Backend
- Acesse o endpoint `/health` para mostrar que o backend está operacional.
- Exemplo de resposta esperada:
  ```json
  {"status": "ok"}
  ```

## 2. Demonstração dos Endpoints Principais
### a) Incidentes
- Acesse `/api/incidentes`:
  - Mostre resposta amigável quando não há eventos:
    ```json
    {"erro": true, "mensagem": "Nenhum evento válido de incidente encontrado na conta New Relic.", "eventos_disponiveis": [], "timestamp": "<data>"}
    ```
  - Se possível, mostre cenário com eventos reais.

### b) Outros Endpoints
- Demonstre endpoints de análise de causa raiz, chat IA, status-cache, etc.
- Mostre exemplos de respostas humanizadas e tratamento de erros.

## 3. Integração com Frontend
- Navegue pelos dashboards executivo e operacional.
- Mostre o Chat IA funcionando e consumo de dados reais.

## 4. Integração com New Relic e OpenAI
- Mostre logs de integração ativa (consultas NRQL, respostas, tratamento de ausência de dados).
- Explique como o sistema lida com respostas vazias e falhas externas.

## 5. Testes Automatizados
- Mostre que todos os testes passaram (16/16), validando fluxos críticos.
- Explique a cobertura dos testes: incidentes, análise, chat, correlação, status-cache, integração New Relic/OpenAI.

---

# Checklist de Deploy Seguro
- [ ] Variáveis sensíveis (.env, chaves, tokens) protegidas e fora do código.
- [ ] Logs de produção sem dados sensíveis.
- [ ] Dependências atualizadas e requirements.txt consistente.
- [ ] Documentação dos endpoints e exemplos de uso.
- [ ] Prints/GIFs do frontend anexados à documentação.
- [ ] Instruções de uso e endpoints principais documentados.
- [ ] Testes automatizados executados e validados.
- [ ] Monitoramento ativo (New Relic) e alertas configurados.

---

# Sugestões de Evolução
- Automatizar alertas para ausência de eventos críticos.
- Adicionar testes de performance e monitoramento contínuo.
- Integrar com outros sistemas ou fontes de dados.
- Implementar relatórios automáticos e exportação de dados.

---

Pronto para apresentação! Se precisar de roteiro para fala, exemplos de respostas ou revisão de código/documentação, só pedir.
