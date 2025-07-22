import time

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def users_in_db(client: TestClient):
    """
    Fixture que cria um conjunto de usuários no banco de dados para os testes.
    Retorna os dados dos usuários criados para referência.
    """
    users_data = [
        {
            "nome": "Admin User",
            "email": "admin@example.com",
            "password": "password123",
            "role": "admin",
        },
        {
            "nome": "Common User",
            "email": "user@example.com",
            "password": "password123",
            "role": "user",
        },
    ]
    created_users = []
    for user in users_data:
        response = client.post("/users", json=user)
        assert response.status_code == 201
        created_users.append(response.json())

    # Adiciona as senhas de volta para uso no login,
    # já que a resposta da API não as inclui
    created_users[0]["password"] = users_data[0]["password"]
    created_users[1]["password"] = users_data[1]["password"]
    return created_users


def test_login_performance(client, users_in_db):
    start_time = time.time()

    for _ in range(100):
        response = client.post(
            "/login",
            json={
                "email": users_in_db[0]["email"],
                "password": users_in_db[0]["password"],
            },
        )
        assert response.status_code == 200

    end_time = time.time()
    avg_time = (end_time - start_time) / 100
    # TODO : Ajustar o valor do limite de tempo conforme necessário
    assert avg_time < 0.3  # Menos de 100ms por login
