
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from fastapi.testclient import TestClient
from api_incidentes import app

client = TestClient(app)

def test_status_cache():
    response = client.get("/api/status-cache")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "total_entidades_consolidadas" in data

def test_listar_entidades():
    response = client.get("/api/entidades")
    assert response.status_code == 200
    data = response.json()
    assert "entidades" in data
    assert "timestamp" in data
    assert "total" in data

def test_listar_incidentes():
    response = client.get("/api/incidentes")
    assert response.status_code == 200
    data = response.json()
    assert "incidentes" in data
    assert "timestamp" in data
    assert "resumo" in data

def test_chat_api_sem_mensagem():
    response = client.post("/api/chat", json={})
    assert response.status_code == 422 or response.status_code == 400

def test_chat_api_com_mensagem():
    response = client.post("/api/chat", json={"mensagem": "Quais entidades estão com maior número de erros?"})
    assert response.status_code == 200
    data = response.json()
    assert "resposta" in data
    assert "mensagem_recebida" in data
    assert "timestamp" in data

def test_correlacionar_incidentes():
    response = client.post("/api/correlacionar")
    assert response.status_code == 200
    data = response.json()
    assert "mensagem" in data
    assert "total_incidentes" in data
    assert "total_entidades_associadas" in data
    assert "timestamp" in data
