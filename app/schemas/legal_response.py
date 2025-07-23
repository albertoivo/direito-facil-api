from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


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
    question: str
    category: Optional[str] = None
    user_context: Optional[str] = None


class DocumentUpload(BaseModel):
    title: str
    content: str
    category: str
    source_url: Optional[str] = None
