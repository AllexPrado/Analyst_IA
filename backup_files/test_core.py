from core_inteligente.context_storage import ContextStorage

def test_salvar_e_carregar_contexto():
    storage = ContextStorage()
    storage.salvar_contexto("sessao-teste", {"eventos": [{"entidade":"app","tipo":"erro"}]})
    c = storage.carregar_contexto("sessao-teste")
    assert c["eventos"][0]["entidade"] == "app"
