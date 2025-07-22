import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.logging import setup_logging
from app.database import get_db
from app.routers import auth, users

from .middleware.rate_limit import _rate_limit_exceeded_handler, limiter

# Ativa o sistema de logging antes de qualquer outra coisa
logger = setup_logging()

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(
    title="CRUD OAuth API",
    description="API para templates de CRUD com autenticação OAuth2",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Auth", "description": "Operações de autenticação"},
        {"name": "Users", "description": "Gerenciamento de usuários"},
        {"name": "Home", "description": "Página inicial da API"},
        {"name": "Health Check", "description": "Verificação de saúde da API"},
    ],
)

# Incluir routers
app.include_router(users.router)
app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver", "*"]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/", tags=["Home"])
def home():
    """
    Rota de boas-vindas da API.

    Returns:
        dict: Mensagem de confirmação que a API está funcionando
    """
    return {"message": "API rodando com sucesso!"}


@app.get("/health", tags=["Health Check"])
def health_check(db: Session = Depends(get_db)):
    """
    Verifica o status de saúde da aplicação e conexão com o banco de dados.

    Args:
        db (Session): Sessão do banco de dados injetada via dependency injection

    Returns:
        dict: Status da aplicação - "healthy" se tudo estiver funcionando,
              "unhealthy" com detalhes do erro se houver problemas

    Raises:
        Não levanta exceções, retorna status de erro no JSON
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "health": True}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
