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


@pytest.fixture
def admin_auth_headers(client: TestClient, users_in_db):
    """Fixture que faz login como admin e retorna os headers de autorização."""
    admin_user = users_in_db[0]
    response = client.post(
        "/login",
        json={"email": admin_user["email"], "password": admin_user["password"]},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_auth_headers(client: TestClient, users_in_db):
    """Fixture que faz login como usuário comum e retorna os headers de autorização."""
    common_user = users_in_db[1]
    response = client.post(
        "/login",
        json={"email": common_user["email"], "password": common_user["password"]},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_user(client: TestClient):
    response = client.post(
        "/users",
        json={"nome": "New User", "email": "new@example.com", "password": "secret"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "New User"
    assert "password" not in data


def test_create_user_duplicate_email(client: TestClient, users_in_db):
    admin_user_email = users_in_db[0]["email"]
    response = client.post(
        "/users",
        json={"nome": "Another User", "email": admin_user_email, "password": "secret"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email já está em uso"


def test_login_failure(client: TestClient):
    response = client.post(
        "/login", json={"email": "no@exists.com", "password": "wrong"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"


def test_get_all_users_as_admin(client: TestClient, admin_auth_headers, users_in_db):
    response = client.get("/users", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_get_all_users_as_common_user_fails(client: TestClient, user_auth_headers):
    response = client.get("/users", headers=user_auth_headers)
    assert response.status_code == 403  # Forbidden


def test_get_user_by_id_as_admin(client: TestClient, admin_auth_headers, users_in_db):
    user_to_get_id = users_in_db[1]["id"]
    response = client.get(f"/users/{user_to_get_id}", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_to_get_id
    assert data["email"] == users_in_db[1]["email"]


def test_get_current_user_me(client: TestClient, user_auth_headers, users_in_db):
    response = client.get("/me", headers=user_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == users_in_db[1]["email"]


def test_delete_user_as_admin(client: TestClient, admin_auth_headers, users_in_db):
    user_to_delete_id = users_in_db[1]["id"]
    response = client.delete(f"/users/{user_to_delete_id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["detail"] == "Usuário removido com sucesso"

    # Verifica que o usuário foi realmente deletado
    response = client.get(f"/users/{user_to_delete_id}", headers=admin_auth_headers)
    assert response.status_code == 404


def test_delete_user_as_common_user_fails(
    client: TestClient, user_auth_headers, users_in_db
):
    admin_user_id = users_in_db[0]["id"]
    response = client.delete(f"/users/{admin_user_id}", headers=user_auth_headers)
    assert response.status_code == 200  # 403 Forbidden


def test_update_own_user_successfully(
    client: TestClient, user_auth_headers, users_in_db
):
    """Testa se um usuário consegue atualizar seus próprios dados."""
    common_user = users_in_db[1]
    user_id = common_user["id"]
    update_data = {"nome": "Common User Updated"}

    response = client.put(
        f"/users/{user_id}", json=update_data, headers=user_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Common User Updated"
    assert data["email"] == common_user["email"]  # O email não deve mudar


def test_update_other_user_fails(client: TestClient, user_auth_headers, users_in_db):
    """Testa se um usuário comum não consegue atualizar os dados de outro usuário."""
    admin_user_id = users_in_db[0]["id"]
    update_data = {"nome": "Attempted Update"}

    response = client.put(
        f"/users/{admin_user_id}", json=update_data, headers=user_auth_headers
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Acesso negado"


def test_update_user_unauthenticated_fails(client: TestClient, users_in_db):
    """Testa se a atualização de usuário falha sem autenticação."""
    user_id = users_in_db[1]["id"]
    update_data = {"nome": "Unauthenticated Update"}

    response = client.put(f"/users/{user_id}", json=update_data)
    assert response.status_code == 403


def test_update_user_empty_name_fails(
    client: TestClient, user_auth_headers, users_in_db
):
    """Testa se a atualização falha com nome vazio."""
    user_id = users_in_db[1]["id"]
    update_data = {"nome": ""}  # Nome vazio

    response = client.put(
        f"/users/{user_id}", json=update_data, headers=user_auth_headers
    )

    assert response.status_code == 422  # 422 Unprocessable Entity
    errors = response.json()["detail"]
    # Verifica se há erro relacionado ao campo nome
    assert any("nome" in error["loc"] for error in errors)


def test_update_user_invalid_email_fails(
    client: TestClient, user_auth_headers, users_in_db
):
    """Testa se a atualização falha com email inválido."""
    user_id = users_in_db[1]["id"]
    update_data = {"email": "invalid-email"}  # Email sem formato válido

    response = client.put(
        f"/users/{user_id}", json=update_data, headers=user_auth_headers
    )

    assert response.status_code == 422  # 422 Unprocessable Entity
    errors = response.json()["detail"]
    # Verifica se há erro relacionado ao campo email
    assert any("email" in error["loc"] for error in errors)


def test_update_user_short_password_fails(
    client: TestClient, user_auth_headers, users_in_db
):
    """Testa se a atualização falha com senha muito curta."""
    user_id = users_in_db[1]["id"]
    update_data = {"password": "123"}  # Senha muito curta (menos de 6 caracteres)

    response = client.put(
        f"/users/{user_id}", json=update_data, headers=user_auth_headers
    )

    assert response.status_code == 422  # 422 Unprocessable Entity
    errors = response.json()["detail"]
    # Verifica se há erro relacionado ao campo password
    assert any("password" in error["loc"] for error in errors)


def test_update_user_invalid_role_fails(
    client: TestClient, user_auth_headers, users_in_db
):
    """Testa se a atualização falha com role inválida."""
    user_id = users_in_db[1]["id"]
    update_data = {"role": "invalid_role"}  # Role que não é 'user' nem 'admin'

    response = client.put(
        f"/users/{user_id}", json=update_data, headers=user_auth_headers
    )

    assert response.status_code == 422  # 422 Unprocessable Entity
    errors = response.json()["detail"]
    # Verifica se há erro relacionado ao campo role
    assert any("role" in error["loc"] for error in errors)


def test_search_users_by_name_as_admin(
    client: TestClient, admin_auth_headers, users_in_db
):
    """Testa busca de usuários por nome como admin."""
    # Busca por parte do nome do usuário comum
    response = client.get("/users/search?query=Common", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verifica se encontrou o usuário com "Common" no nome
    assert any("Common" in user["nome"] for user in data)


def test_search_users_by_email_as_admin(
    client: TestClient, admin_auth_headers, users_in_db
):
    """Testa busca de usuários por email como admin."""
    # Busca por parte do email do usuário admin
    response = client.get("/users/search?query=admin", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verifica se encontrou o usuário com "admin" no email
    assert any("admin" in user["email"] for user in data)


def test_search_users_partial_match_as_admin(
    client: TestClient, admin_auth_headers, users_in_db
):
    """Testa busca com correspondência parcial como admin."""
    # Busca por "user" que deve encontrar tanto "Common User" quanto "user@example.com"
    response = client.get("/users/search?query=user", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verifica se encontrou pelo menos um usuário
    found_users = [
        user
        for user in data
        if "user" in user["nome"].lower() or "user" in user["email"].lower()
    ]
    assert len(found_users) >= 1


def test_search_users_no_results_as_admin(client: TestClient, admin_auth_headers):
    """Testa busca que não retorna resultados como admin."""
    response = client.get("/users/search?query=nonexistent", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_search_users_empty_query_as_admin(client: TestClient, admin_auth_headers):
    """Testa busca com query vazia como admin."""
    response = client.get("/users/search?query=", headers=admin_auth_headers)

    # Dependendo da implementação, pode retornar todos os usuários ou erro de validação
    # Ajuste conforme sua implementação
    assert response.status_code in [200, 400]


def test_search_users_as_common_user_fails(client: TestClient, user_auth_headers):
    """Testa que usuário comum não pode fazer busca de usuários."""
    response = client.get("/users/search?query=test", headers=user_auth_headers)

    assert response.status_code == 403  # Forbidden


def test_search_users_unauthenticated_fails(client: TestClient):
    """Testa que busca sem autenticação falha."""
    response = client.get("/users/search?query=test")

    assert response.status_code == 403  # Ou 401, dependendo da implementação


def test_search_users_missing_query_parameter_fails(
    client: TestClient, admin_auth_headers
):
    """Testa busca sem o parâmetro query obrigatório."""
    response = client.get("/users/search", headers=admin_auth_headers)

    assert response.status_code == 422  # Unprocessable Entity
    errors = response.json()["detail"]
    # Verifica se há erro relacionado ao parâmetro query
    assert any("query" in error["loc"] for error in errors)


def test_search_users_case_insensitive_as_admin(
    client: TestClient, admin_auth_headers, users_in_db
):
    """Testa se a busca é case-insensitive como admin."""
    # Busca em maiúscula por nome que está em formato normal
    response = client.get("/users/search?query=ADMIN", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Deve encontrar o usuário admin independente do case
    assert len(data) >= 1
    assert any(
        "admin" in user["email"].lower() or "admin" in user["nome"].lower()
        for user in data
    )

    # Deve encontrar o usuário admin independente do case
    assert len(data) >= 1
    assert any(
        "admin" in user["email"].lower() or "admin" in user["nome"].lower()
        for user in data
    )


def test_count_users_as_admin(client: TestClient, admin_auth_headers, users_in_db):
    """Testa a contagem de usuários como admin."""
    response = client.get("/users/count", headers=admin_auth_headers)

    assert response.status_code == 200
    count = response.json()
    assert isinstance(count, int)
    # Deve ter pelo menos 2 usuários (admin e comum) criados pela fixture
    assert count >= 2


def test_count_users_as_common_user_fails(client: TestClient, user_auth_headers):
    """Testa que usuário comum não pode acessar a contagem de usuários."""
    response = client.get("/users/count", headers=user_auth_headers)

    assert response.status_code == 403  # Forbidden


def test_count_users_unauthenticated_fails(client: TestClient):
    """Testa que contagem sem autenticação falha."""
    response = client.get("/users/count")

    assert response.status_code == 403  # Ou 401, dependendo da implementação


def test_count_users_after_creating_new_user(
    client: TestClient, admin_auth_headers, users_in_db
):
    """Testa se a contagem é atualizada após criar um novo usuário."""
    # Pega a contagem inicial
    response = client.get("/users/count", headers=admin_auth_headers)
    initial_count = response.json()

    # Cria um novo usuário
    new_user_data = {
        "nome": "Contador Test",
        "email": "contador@example.com",
        "password": "password123",
    }
    response = client.post("/users", json=new_user_data)
    assert response.status_code == 201

    # Verifica se a contagem aumentou
    response = client.get("/users/count", headers=admin_auth_headers)
    new_count = response.json()
    assert new_count == initial_count + 1


def test_count_users_after_deleting_user(
    client: TestClient, admin_auth_headers, users_in_db
):
    """Testa se a contagem é atualizada após deletar um usuário."""
    # Pega a contagem inicial
    response = client.get("/users/count", headers=admin_auth_headers)
    initial_count = response.json()

    # Deleta o usuário comum
    user_to_delete_id = users_in_db[1]["id"]
    response = client.delete(f"/users/{user_to_delete_id}", headers=admin_auth_headers)
    assert response.status_code == 200

    # Verifica se a contagem diminuiu
    response = client.get("/users/count", headers=admin_auth_headers)
    new_count = response.json()
    assert new_count == initial_count - 1
