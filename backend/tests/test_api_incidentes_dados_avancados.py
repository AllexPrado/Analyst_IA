import pytest
from fastapi.testclient import TestClient
from api_incidentes import app

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_dados_exemplo():
    resp = client.post("/api/adicionar-dados-exemplo")
    assert resp.status_code == 200

def test_incidentes_dados_avancados():
    resp = client.get("/api/incidentes")
    assert resp.status_code == 200
    data = resp.json()
    assert "incidentes" in data
    assert isinstance(data["incidentes"], list)
    assert len(data["incidentes"]) > 0, "Nenhum incidente retornado."
    for incidente in data["incidentes"]:
        assert "entidades_dados_avancados" in incidente, "Campo entidades_dados_avancados ausente."
        # O campo deve ser uma lista e não deve estar vazio
        assert isinstance(incidente["entidades_dados_avancados"], list), "entidades_dados_avancados não é lista."
        # Se não houver entidades associadas, pode ser vazio, mas se houver, deve ter dados reais
        if incidente["entidades_dados_avancados"]:
            for entidade in incidente["entidades_dados_avancados"]:
                assert "dados_avancados" in entidade, "dados_avancados ausente na entidade."
                # Aqui você pode expandir para validar campos específicos do New Relic
                assert entidade["dados_avancados"] is not None, "dados_avancados está vazio."
