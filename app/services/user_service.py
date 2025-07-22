import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth_service import AuthService

# Cria logger para este módulo
logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthService(db)
        logger.debug("UserService inicializado")

    def get_users(self) -> List[User]:
        return self.db.query(User).all()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, user_data: UserCreate) -> User:
        logger.info(f"Tentativa de criar usuário: {user_data.email}")

        if self.get_user_by_email(user_data.email):
            logger.warning(f"Email já em uso: {user_data.email}")
            raise ValueError("Email já está em uso")

        hashed_password = self.auth_service.get_password_hash(user_data.password)

        db_user = User(
            nome=user_data.nome,
            email=user_data.email,
            hashed_password=hashed_password,
            role=user_data.role or "user",
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        logger.info(
            f"Usuário criado com sucesso: ID={db_user.id}, Email={db_user.email}"
        )
        return db_user

    def delete_user(self, user_id: int) -> bool:
        logger.info(f"Tentativa de deletar usuário: ID={user_id}")

        user = self.get_user_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            logger.info(f"Usuário deletado: ID={user_id}, Email={user.email}")
            return True

        logger.warning(f"Tentativa de deletar usuário inexistente: ID={user_id}")
        return False

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        # Validar role
        if user_data.role and user_data.role not in ["user", "admin"]:
            raise ValueError("Role inválida. Deve ser 'user' ou 'admin'.")

        # Verificar se está tentando atualizar email para um já existente
        if user_data.email and user_data.email != user.email:
            existing_user = self.get_user_by_email(user_data.email)
            if existing_user:
                raise ValueError("Email já está em uso")

        # Pegar apenas campos que foram fornecidos (não None)
        update_data = user_data.model_dump(exclude_unset=True)

        # Atualizar campos fornecidos
        for field, value in update_data.items():
            if field == "password":
                # Hash da senha se fornecida
                user.hashed_password = self.auth_service.get_password_hash(value)
            elif hasattr(user, field):
                # Atualizar outros campos diretamente
                setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def search_users(self, query: str) -> List[User]:
        """
        Busca usuários pelo nome ou email.
        """
        if not query or query.strip() == "":
            return []

        search_term = f"%{query.strip().lower()}%"

        return (
            self.db.query(User)
            .filter((User.nome.ilike(search_term)) | (User.email.ilike(search_term)))
            .all()
        )

    def count_users(self) -> int:
        """
        Conta o número total de usuários.
        """
        return self.db.query(User).count()
