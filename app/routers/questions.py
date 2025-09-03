from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

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
async def health_check(db: Session = Depends(get_db)):
    """
    Verificar saúde dos serviços de IA e banco de dados.
    """
    health_status = {
        "database": {"status": "ok", "details": "Conexão bem-sucedida"},
        "vector_store": {"status": "ok", "details": "Serviço disponível"},
        "llm_service": {"status": "ok", "details": "Serviço disponível"},
    }

    # 1. Verificar a conexão com o banco de dados
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        health_status["database"]["status"] = "error"
        health_status["database"]["details"] = f"Falha na conexão: {str(e)}"

    # 2. Verificar o Vector Store
    try:
        vector_store_status = await rag_service.health_check()
        if vector_store_status != "ok":
             health_status["vector_store"]["status"] = "degraded"
             health_status["vector_store"]["details"] = vector_store_status
    except Exception as e:
        health_status["vector_store"]["status"] = "error"
        health_status["vector_store"]["details"] = f"Serviço indisponível: {str(e)}"

    # 3. Verificar o serviço de LLM
    try:
        llm_status = await rag_service.check_llm_status()
        if not llm_status:
            health_status["llm_service"]["status"] = "error"
            health_status["llm_service"]["details"] = "LLM não respondeu corretamente."

    except Exception as e:
        health_status["llm_service"]["status"] = "error"
        health_status["llm_service"]["details"] = f"Serviço indisponível: {str(e)}"

    # Verifica se algum serviço falhou para retornar o status code apropriado
    if any(service["status"] == "error" for service in health_status.values()):
        raise HTTPException(
            status_code=503,
            detail=health_status
        )

    return health_status
