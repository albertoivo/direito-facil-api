# CRUD OAuth API Backend

Este é um projeto de backend robusto construído com FastAPI, projetado para servir como um template para aplicações que necessitam de operações CRUD (Criar, Ler, Atualizar, Deletar) com autenticação de usuário via JWT (JSON Web Tokens).

## ✨ Features

- **Framework Moderno:** Construído com [FastAPI](https://fastapi.tiangolo.com/) para alta performance.
- **Banco de Dados:** Utiliza [SQLAlchemy](https://www.sqlalchemy.org/) como ORM para interagir com o banco de dados PostgreSQL.
- **Autenticação Segura:** Implementa autenticação e autorização usando JWT.
- **Containerização:** Configuração completa com [Docker](https://www.docker.com/) e [Docker Compose](https://docs.docker.com/compose/) para um ambiente de desenvolvimento e produção consistente.
- **Testes:** Suíte de testes configurada com [Pytest](https://pytest.org/).
- **Qualidade de Código:** Formatador [Black](https://github.com/psf/black) e linter [Flake8](https://flake8.pycqa.org/en/latest/) para garantir um código limpo e padronizado.
- **Documentação Automática:** Documentação interativa da API gerada automaticamente pelo FastAPI, disponível em `/docs` e `/redoc`.

---

## 🚀 Começando

Você pode rodar o projeto de duas maneiras: manualmente com um ambiente virtual Python ou de forma mais simples e recomendada, usando Docker.

### Pré-requisitos

Antes de começar, garanta que você tenha os seguintes softwares instalados:
- [Git](https://git-scm.com/)
- [Python](https://www.python.org/downloads/) (versão 3.10 ou superior)
- [Docker](https://www.docker.com/products/docker-desktop/) e [Docker Compose](https://docs.docker.com/compose/install/)

---

### 🐳 Método 1: Rodando com Docker (Recomendado)

Esta é a forma mais fácil de subir todo o ambiente, incluindo o banco de dados PostgreSQL.

1.  **Clone o repositório:**
    ```sh
    git clone https://github.com/albertoivo/crud-oauth_api.git
    cd crud-oauth_api
    ```

2.  **Inicie os containers:**
    Use o Docker Compose para construir as imagens e iniciar os serviços da aplicação e do banco de dados.
    ```sh
    docker-compose up --build
    ```

A API estará disponível em `http://localhost:8000`.

---

### 🐍 Método 2: Configuração Manual

Siga estes passos se preferir configurar o ambiente localmente sem o Docker.

1.  **Clone o repositório:**
    ```sh
    git clone https://github.com/albertoivo/crud-oauth_api.git
    cd crud-oauth_api
    ```

2.  **Crie e ative um ambiente virtual:**
    - No macOS/Linux:
      ```sh
      python3 -m venv venv
      source venv/bin/activate
      ```
    - No Windows:
      ```sh
      python -m venv venv
      .\venv\Scripts\activate
      ```

3.  **Instale as dependências:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    Crie um arquivo chamado `.env` na raiz do projeto, copiando o exemplo do `docker-compose.yml`. Você precisará de uma instância do PostgreSQL rodando e acessível.

    ```env
    # Conteúdo para o arquivo .env
    DATABASE_URL="postgresql://postgres:postgres@localhost:5432/crud-oauth"
    SECRET_KEY="uma-chave-secreta-muito-forte"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=60
    ```

5.  **Inicie a aplicação:**
    Use o Uvicorn para rodar o servidor FastAPI. A flag `--reload` reinicia o servidor automaticamente a cada alteração no código.
    ```sh
    uvicorn app.main:app --reload
    ```

A API estará disponível em `http://localhost:8000`.

---

## 🧪 Rodando os Testes

Para garantir que tudo está funcionando como esperado, você pode rodar a suíte de testes automatizados.

Com o ambiente virtual ativado:
```sh
pytest
```

---

## 📚 Documentação da API

Com a aplicação rodando, você pode acessar a documentação interativa da API gerada pelo Swagger UI e ReDoc nos seguintes endereços:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
