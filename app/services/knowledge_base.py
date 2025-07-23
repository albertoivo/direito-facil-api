from datetime import datetime
import uuid
from typing import Optional
import logging
from .rag_service import RAGService


logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self):
        self.rag_service = RAGService()

    async def add_document(
        self, title: str, content: str, category: str, source_url: Optional[str] = None
    ) -> str:
        """
        Adicionar documento à base de conhecimento
        """
        try:
            doc_id = str(uuid.uuid4())
            
            # Gerar embedding
            embedding = self.rag_service.embedding_model.encode([content])[0].tolist()

            # Adicionar ao ChromaDB
            self.rag_service.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[
                    {
                        "title": title,
                        "category": category,
                        "source": source_url or "Manual",
                        "doc_id": doc_id,
                        "created_at": datetime.now().isoformat(),
                    }
                ],
                ids=[doc_id],
            )

            return doc_id

        except Exception as e:
            logger.error(f"Erro ao adicionar documento: {e}")
            raise
