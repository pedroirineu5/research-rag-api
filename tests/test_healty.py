from fastapi.testclient import TestClient

from main import app 

def test_healty_retorna_status_ok():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status":"ok"}

def test_intervalo_face_2():
    client = TestClient(app)

    response = client.get("/dados/intervalo?faces=2")

    assert not response.status_code == 422

def test_intervalo_face_error():
    client = TestClient(app)
    response = client.get('/dados/intervalo?faces=1')

    assert response.status_code == 422

def test_teste_com_query_com_parametro():
    client = TestClient(app)

    response = client.get("/teste?quantifa=3")

    assert not response.status_code == 422
    assert response.json() == {"mensagem": 3}

def test_field_com_basemodel_do_pydantic():
    client = TestClient(app)

    response = client.post("/dados/intervalo", json={
        "face": 6,
        "quantidade": 2
    })

    assert response.status_code == 200
    assert response.json == {
        "minimo": 2,
        "máximo": 12,
    }