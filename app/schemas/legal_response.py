from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class ComplexityLevel(str, Enum):
    """Níveis de complexidade para respostas"""
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    DETAILED = "detailed"
    TECHNICAL = "technical"


class SourceInfo(BaseModel):
    """Informações sobre uma fonte jurídica utilizada"""

    title: str = Field(..., description="Título do documento/fonte")
    source: str = Field(
        ..., description="Identificação da fonte (lei, jurisprudência, etc.)"
    )
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Score de relevância (0-1)"
    )


class LegalResponse(BaseModel):
    """Resposta jurídica gerada pelo sistema"""

    answer: str = Field(..., description="Resposta gerada pelo LLM")
    sources: List[SourceInfo] = Field(
        ..., description="Lista de fontes utilizadas na resposta"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=100.0, description="Score de confiança (0-100)"
    )
    category: str = Field(..., description="Categoria jurídica predominante")
    disclaimer: str = Field(
        default="Esta informação tem caráter orientativo. Para questões específicas, consulte um advogado.",
        description="Disclaimer legal obrigatório",
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp da resposta"
    )


class LegalQuery(BaseModel):
    question: str = Field(..., min_length=10, max_length=1000, description="Pergunta do usuário")
    category: Optional[str] = Field(None, description="Categoria jurídica específica")
    user_context: Optional[str] = Field(None, max_length=500, description="Contexto adicional do usuário")
    complexity: ComplexityLevel = Field(
        default=ComplexityLevel.SIMPLE,
        description="Nível de complexidade desejado para a resposta"
    )


class DocumentUpload(BaseModel):
    title: str
    content: str
    category: str
    source_url: Optional[str] = None
