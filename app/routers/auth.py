import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.rate_limit import conditional_limit
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import User
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=Token, summary="Realizar login")
@conditional_limit("5/minute")  # Usa rate limiting condicional
def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)):
    logger.info(f"Tentativa de login para: {credentials.email}")

    auth_service = AuthService(db)
    token = auth_service.authenticate_user(credentials.email, credentials.password)

    if not token:
        logger.warning(f"Login falhou para: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas"
        )

    logger.info(f"Login bem-sucedido para: {credentials.email}")
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout", summary="Realizar logout do usuário")
@conditional_limit("10/minute")  # Usa rate limiting condicional
def logout(
    request: Request, current_user: User = Depends(AuthService.get_current_user)
):
    logger.info(f"Logout realizado para usuário: {current_user.email}")
    return {"message": "Logout realizado com sucesso."}


@router.get(
    "/me", response_model=User, summary="Obter informações do usuário autenticado"
)
def get_current_user(current_user: User = Depends(AuthService.get_current_user)):
    """
    Obtém as informações do usuário autenticado.

    Este endpoint retorna os detalhes do usuário que está atualmente autenticado,
    utilizando o token JWT fornecido no cabeçalho da requisição.
    """
    return current_user
