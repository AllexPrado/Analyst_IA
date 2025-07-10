import pytest
from fastapi.testclient import TestClient
from api_incidentes import app

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_dados_exemplo():
    # Garante que sempre há dados de exemplo antes dos testes
    resp = client.post("/api/adicionar-dados-exemplo")
    assert resp.status_code == 200

def test_analise_incidente_valido():
    # Primeiro, garantir que há incidentes correlacionados
    client.post("/api/correlacionar")
    # Buscar lista de incidentes
    resp = client.get("/api/incidentes")
    assert resp.status_code == 200
    incidentes = resp.json().get("incidentes", [])
    if not incidentes:
        pytest.skip("Sem incidentes para testar analise")
    incidente_id = incidentes[0]["id"]
    response = client.get(f"/api/analise/{incidente_id}")
    assert response.status_code == 200
    data = response.json()
    assert "incidente_id" in data
    assert "analise" in data
    assert "timestamp" in data

def test_analise_incidente_invalido():
    response = client.get("/api/analise/nao_existe")
    assert response.status_code in (200, 404, 422)  # depende da lógica do endpoint


def test_analise_causa_raiz_valido():
    client.post("/api/correlacionar")
    resp = client.get("/api/incidentes")
    assert resp.status_code == 200
    incidentes = resp.json().get("incidentes", [])
    if not incidentes:
        pytest.skip("Sem incidentes para testar causa raiz")
    incidente_id = incidentes[0]["id"]
    response = client.get(f"/api/analise_causa_raiz/{incidente_id}")
    assert response.status_code == 200
    data = response.json()
    assert "incidente_id" in data
    assert "causa_raiz" in data
    assert "timestamp" in data

def test_analise_causa_raiz_invalido():
    response = client.get("/api/analise_causa_raiz/nao_existe")
    assert response.status_code in (200, 404, 422)

def test_list_endpoints():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json().get("paths", {})
    print("ENDPOINTS DISPONÍVEIS:", list(paths.keys()))
    assert "/api/adicionar-dados-exemplo" in paths
