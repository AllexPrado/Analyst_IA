# Checklist de Deploy Seguro – Analyst_IA Backend

## 1. Endpoints Utilitários
- [ ] Certifique-se de que endpoints como `/adicionar-dados-exemplo` NÃO estejam acessíveis em produção.
- [ ] Utilize variáveis de ambiente para condicionar a inclusão desses endpoints apenas em dev/homologação.
- [ ] Documente endpoints utilitários como "apenas para testes" na OpenAPI.

## 2. Dados Reais
- [ ] Garanta que endpoints principais (ex: `/incidentes`, `/entidades`, `/chat`, `/correlacionar`, `/status-cache`) retornem sempre dados reais do New Relic.
- [ ] Valide que o frontend consome apenas esses endpoints em produção.

## 3. Documentação
- [ ] Atualize exemplos OpenAPI para todos os endpoints, destacando campos humanizados.
- [ ] Marque claramente endpoints de teste/utilitários na documentação.

## 4. Testes e Monitoramento
- [ ] Execute todos os testes automatizados antes do deploy.
- [ ] Implemente testes que garantam que endpoints utilitários não estejam acessíveis em produção.
- [ ] Monitore logs e respostas dos endpoints após o deploy.

## 5. Segurança
- [ ] Proteja endpoints sensíveis com autenticação/autorização adequada.
- [ ] Revise permissões e variáveis de ambiente antes do deploy.

---

> Siga este checklist a cada release para garantir que o backend está seguro, padronizado e pronto para integração com frontend e IA.
