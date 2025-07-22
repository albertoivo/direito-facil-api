import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.models.user import User

security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    def get_password_hash(self, password: str) -> str:
        hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed_bytes.decode("utf-8")

    def authenticate_user(self, email: str, password: str) -> Optional[str]:
        user = self.db.query(User).filter(User.email == email).first()

        if not user:
            return None

        if not self.verify_password(password, user.hashed_password):
            return None

        return self.create_access_token(
            {
                "sub": str(user.id),
                "id": user.id,
                "email": user.email,
                "nome": user.nome,
                "role": user.role,
            }
        )

    def create_access_token(
        self, data: dict, expires_delta: timedelta | None = None
    ) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        iat = datetime.now(timezone.utc)
        to_encode.update({"exp": expire})
        to_encode.update({"iat": iat})

        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """
        Verifica e decodifica o JWT token
        """
        try:
            # O token já vem sem "Bearer " quando usa HTTPBearer
            payload = jwt.decode(
                credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
            )
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def get_current_user(token_data: dict = Depends(verify_token)):
        """
        Retorna dados do usuário atual baseado no token
        """
        return token_data

    def verify_admin(token_data: dict = Depends(verify_token)):
        """
        Verifica se o usuário tem role de admin
        """
        if token_data.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: privilégios de admin necessários",
            )
        return token_data
