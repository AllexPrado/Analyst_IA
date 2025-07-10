from fastapi import status

# Exemplo OpenAPI para o endpoint utilitário de adicionar dados de exemplo
adicionar_dados_exemplo_example = {
    "status": "success",
    "message": "Dados de exemplo adicionados com sucesso",
    "alertas_adicionados": 7,
    "incidentes_adicionados": 3,
    "explicacao": "Endpoint utilitário para inserir dados de exemplo e facilitar testes automatizados do frontend.",
    "sugestao": "Utilize este endpoint apenas em ambientes de desenvolvimento ou homologação.",
    "proximos_passos": "Após adicionar os dados, utilize os endpoints principais para validar as integrações e fluxos do frontend."
}

# Para documentação OpenAPI, pode ser usado assim:
# @router.post(
#     "/adicionar-dados-exemplo",
#     tags=["Util"],
#     summary="Adiciona dados de exemplo para testes",
#     include_in_schema=True,
#     responses={
#         status.HTTP_200_OK: {
#             "description": "Dados de exemplo adicionados com sucesso.",
#             "content": {
#                 "application/json": {
#                     "example": adicionar_dados_exemplo_example
#                 }
#             }
#         }
#     }
# )
