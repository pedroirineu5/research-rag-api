from fastapi.testclient import TestClient

from main import app 

def test_healty_retorna_status_ok():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status":"ok"}

def test_healty_retorna_status_error():
    client = TestClient(app)

    response = client.get("/dados/intervalo?faces=2")

    assert response.status_code == 422 