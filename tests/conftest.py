import os
import sys
from pathlib import Path
import tempfile
import shutil

# PRIMEIRA COISA: Definir ambiente de teste
os.environ["TESTING"] = "True"
os.environ["LOG_LEVEL"] = "ERROR"

# Criar diretório temporário para ChromaDB nos testes
test_chroma_dir = tempfile.mkdtemp(prefix="chroma_test_")
os.environ["CHROMA_PATH"] = test_chroma_dir

# Adicionar o diretório raiz ao Python path ANTES dos imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models.base import Base

# Banco de dados de testes dentro do diretório tests
test_db_path = Path(__file__).parent / "test.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{test_db_path}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override da função get_db para usar o banco de teste"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Fixture do cliente de teste FastAPI"""
    # Criar tabelas
    Base.metadata.create_all(bind=engine)

    # Override da dependência do banco
    app.dependency_overrides[get_db] = override_get_db

    # Cliente de teste
    with TestClient(app) as test_client:
        yield test_client

    # Limpar depois dos testes
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """Fixture para sessão do banco de dados"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def pytest_sessionfinish(session, exitstatus):
    """Cleanup após todos os testes"""
    # Limpar diretório temporário do ChromaDB
    if os.path.exists(test_chroma_dir):
        shutil.rmtree(test_chroma_dir, ignore_errors=True)
    
    # Limpar arquivo de banco de dados de teste
    if test_db_path.exists():
        test_db_path.unlink()
