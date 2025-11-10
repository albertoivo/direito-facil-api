import logging
import uuid
from datetime import datetime
from typing import Optional, List

from .rag_service import RAGService
from .web_scraper import WebScraperService

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self):
        self.rag_service = RAGService()
        self.scraper = WebScraperService()
        # Limite de caracteres por chunk (aproximadamente 2000 tokens)
        self.chunk_size = 6000
        self.chunk_overlap = 200

    def _split_into_chunks(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Divide texto em chunks menores com sobreposição
        
        Args:
            text: Texto completo
            chunk_size: Tamanho máximo de cada chunk em caracteres
            overlap: Número de caracteres sobrepostos entre chunks
            
        Returns:
            Lista de chunks de texto
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Se não é o último chunk, tenta quebrar em um ponto natural (newline ou período)
            if end < len(text):
                # Procura por quebra de linha
                last_newline = text.rfind('\n', start, end)
                if last_newline > start + chunk_size // 2:
                    end = last_newline + 1
                else:
                    # Senão, procura por ponto final
                    last_period = text.rfind('. ', start, end)
                    if last_period > start + chunk_size // 2:
                        end = last_period + 2
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap if end < len(text) else end
        
        return chunks

    async def add_document(
        self, title: str, source_url: str, category: str, content: Optional[str] = None
    ) -> str:
        """
        Adicionar documento à base de conhecimento.
        Se content não for fornecido, extrai automaticamente da source_url.
        Documentos grandes são divididos em chunks automaticamente.
        
        Args:
            title: Título do documento
            source_url: URL da fonte (obrigatório)
            category: Categoria jurídica
            content: Conteúdo opcional (se não fornecido, será extraído da URL)
            
        Returns:
            ID do documento principal criado
            
        Raises:
            ValueError: Se não conseguir extrair conteúdo da URL
        """
        try:
            # Se content não foi fornecido, extrai da URL
            if not content:
                logger.info(f"Extraindo conteúdo de {source_url}")
                content = await self.scraper.extract_content(source_url)
                logger.info(f"Conteúdo extraído: {len(content)} caracteres")
            
            # Divide em chunks se necessário
            chunks = self._split_into_chunks(content, self.chunk_size, self.chunk_overlap)
            logger.info(f"Documento dividido em {len(chunks)} chunks")
            
            doc_id = str(uuid.uuid4())
            
            # Adiciona cada chunk ao ChromaDB
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                
                # Gerar embedding usando o RAGService
                embedding = self.rag_service._get_embedding(chunk)

                # Adicionar ao ChromaDB
                self.rag_service.collection.add(
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[
                        {
                            "title": f"{title} (parte {i+1}/{len(chunks)})" if len(chunks) > 1 else title,
                            "category": category,
                            "source": source_url,
                            "doc_id": doc_id,
                            "chunk_id": chunk_id,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "created_at": datetime.now().isoformat(),
                        }
                    ],
                    ids=[chunk_id],
                )
            
            logger.info(f"Documento {doc_id} adicionado com sucesso ({len(chunks)} chunks)")
            return doc_id

        except Exception as e:
            logger.error(f"Erro ao adicionar documento: {e}")
            raise
