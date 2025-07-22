from fastapi import APIRouter, Depends

from app.services.auth_service import AuthService
from app.schemas.question import Question

router = APIRouter(tags=["Doubts"])


@router.post("/duvida")
async def ask_legal_question(
    question: Question, current_user: dict = Depends(AuthService.get_current_user)
):
    return {"answer": "resposta", "sources": []}
