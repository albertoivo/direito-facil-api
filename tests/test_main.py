from fastapi.testclient import TestClient


def test_read_root(client: TestClient):
    """Testa a rota raiz da API"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API rodando com sucesso!"}


def test_health_check(client: TestClient):
    """Testa o health check da API"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy"]


def test_docs_accessible(client: TestClient):
    """Testa se a documentação está acessível"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema(client: TestClient):
    """Testa se o schema OpenAPI está disponível"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "info" in data
    assert data["info"]["title"] == "CRUD OAuth API"
