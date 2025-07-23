from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.legal_response import (DocumentUpload, LegalQuery,
                                        LegalResponse)
from app.services.knowledge_base import KnowledgeBaseService
from app.services.rag_service import RAGService

router = APIRouter(tags=["Doubts"])

rag_service = RAGService()
knowledge_service = KnowledgeBaseService()


@router.post("/ask", response_model=LegalResponse)
async def ask_legal_question(query: LegalQuery, db: Session = Depends(get_db)):
    """
    Endpoint principal para perguntas jurídicas
    """
    try:
        # 1. Buscar documentos relevantes
        relevant_docs = await rag_service.search_relevant_documents(
            query.question, category=query.category, top_k=5
        )

        if not relevant_docs:
            raise HTTPException(
                status_code=404,
                detail="Não encontrei informações relevantes para sua pergunta",
            )

        # 2. Gerar resposta usando LLM
        response = await rag_service.generate_legal_response(
            question=query.question,
            relevant_docs=relevant_docs,
            user_context=query.user_context,
        )

        # 3. Log da consulta para análise
        await rag_service.log_query(query, response, db)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/knowledge/add")
async def add_knowledge_document(doc: DocumentUpload):
    """
    Adicionar documento à base de conhecimento
    """
    try:
        result = await knowledge_service.add_document(
            title=doc.title,
            content=doc.content,
            category=doc.category,
            source_url=doc.source_url,
        )
        return {"message": "Documento adicionado com sucesso", "doc_id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_legal_categories():
    """
    Listar categorias jurídicas disponíveis
    """
    return await rag_service.get_available_categories()


@router.get("/health-ai")
async def health_check():
    """
    Verificar saúde dos serviços
    """
    return {
        "database": "ok",
        "vector_store": await rag_service.health_check(),
        "llm_service": "ok",
    }
