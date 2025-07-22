from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import User, UserCreate, UserUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[User], summary="Listar Usuários")
def get_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.verify_admin),
):
    """
    Retorna a lista de todos os usuários cadastrados.

    Args:
        db (Session): Sessão do banco de dados injetada via dependency injection
        current_user (dict): Dados do usuário atual (injetado automaticamente)

    Returns:
        List[User]: Lista com todos os usuários encontrados no banco de dados

    Raises:
        HTTPException: Em caso de erro interno do servidor
    """
    user_service = UserService(db)
    return user_service.get_users()


@router.post("/", response_model=User, status_code=201, summary="Criar Usuário")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Cria um novo usuário no sistema.

    Args:
        user_data (UserCreate): Dados do usuário a ser criado (nome, email, etc.)
        db (Session): Sessão do banco de dados injetada via dependency injection

    Returns:
        User: Dados do usuário criado, incluindo o ID gerado

    Raises:
        HTTPException: 400 - Se houver erro na validação dos dados ou
                            se o email já estiver em uso
    """
    user_service = UserService(db)
    try:
        return user_service.create_user(user_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/search", response_model=List[User], summary="Buscar Usuários por Nome ou Email"
)
def search_users(
    query: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.verify_admin),
):
    """
    Busca usuários pelo nome ou email.

    Args:
        query (str): Termo de busca (nome ou email)
        db (Session): Sessão do banco de dados injetada via dependency injection
        current_user (dict): Dados do usuário atual (injetado automaticamente)

    Returns:
        List[User]: Lista de usuários que correspondem ao termo de busca

    Raises:
        HTTPException: 400 - Se o termo de busca for inválido
    """
    user_service = UserService(db)
    return user_service.search_users(query)


@router.get("/count", summary="Contar Usuários")
def count_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.verify_admin),
):
    """
    Conta o número total de usuários cadastrados.

    Args:
        db (Session): Sessão do banco de dados injetada via dependency injection
        current_user (dict): Dados do usuário atual (injetado automaticamente)

    Returns:
        int: Número total de usuários cadastrados

    Raises:
        HTTPException: 500 - Se ocorrer um erro interno ao contar os usuários
    """
    user_service = UserService(db)
    return user_service.count_users()


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Remove um usuário do sistema pelo ID.

    Args:
        user_id (int): ID único do usuário a ser removido
        db (Session): Sessão do banco de dados injetada via dependency injection

    Returns:
        dict: Mensagem de confirmação se o usuário foi removido com sucesso

    Raises:
        HTTPException: 404 - Se o usuário com o ID fornecido não for encontrado
    """
    user_service = UserService(db)
    if user_service.delete_user(user_id):
        return {"detail": "Usuário removido com sucesso"}
    else:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")


@router.put("/{user_id}", response_model=User, summary="Atualizar Usuário")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user),
):
    """
    Atualiza os dados de um usuário existente.

    Args:
        user_id (int): ID único do usuário a ser atualizado
        user_data (UserUpdate): Dados atualizados do usuário
        db (Session): Sessão do banco de dados injetada via dependency injection

    Returns:
        User: Dados do usuário atualizado

    Raises:
        HTTPException: 404 - Se o usuário não for encontrado
                       400 - Se houver erro na validação dos dados
                       403 - Se o usuário atual não tiver permissão para atualizar
    """
    user_service = UserService(db)
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    updated_user = user_service.update_user(user_id, user_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return updated_user


@router.get("/{user_id}", response_model=User, summary="Buscar Usuário por ID")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Busca um usuário específico pelo ID.

    Args:
        user_id (int): ID único do usuário
        db (Session): Sessão do banco de dados injetada via dependency injection

    Returns:
        User: Dados do usuário encontrado

    Raises:
        HTTPException: 404 - Se o usuário não for encontrado
    """
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user
