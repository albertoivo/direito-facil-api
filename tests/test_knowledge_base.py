"""
Testes para o KnowledgeBaseService
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.services.knowledge_base import KnowledgeBaseService


@pytest.fixture
def knowledge_service():
    """Fixture para instanciar o KnowledgeBaseService"""
    with patch('app.services.knowledge_base.RAGService'):
        with patch('app.services.knowledge_base.WebScraperService'):
            service = KnowledgeBaseService()
            return service


@pytest.mark.asyncio
class TestKnowledgeBaseService:
    """Testes para o KnowledgeBaseService"""

    async def test_add_document_with_content(self, knowledge_service):
        """Testa adição de documento quando o conteúdo é fornecido"""
        # Mock do RAGService
        knowledge_service.rag_service._get_embedding = Mock(
            return_value=[0.1, 0.2, 0.3]
        )
        knowledge_service.rag_service.collection.add = Mock()
        
        # Não deve chamar o scraper se content for fornecido
        knowledge_service.scraper.extract_content = AsyncMock()
        
        doc_id = await knowledge_service.add_document(
            title="CDC - Artigo 18",
            source_url="http://planalto.gov.br/lei",
            category="Direito do Consumidor",
            content="Os fornecedores de produtos respondem solidariamente..."
        )
        
        # Verifica que o documento foi adicionado
        assert doc_id is not None
        assert len(doc_id) == 36  # UUID formato
        
        # Verifica que o scraper NÃO foi chamado
        knowledge_service.scraper.extract_content.assert_not_called()
        
        # Verifica que o embedding foi gerado
        knowledge_service.rag_service._get_embedding.assert_called_once()
        
        # Verifica que foi adicionado ao ChromaDB
        knowledge_service.rag_service.collection.add.assert_called_once()

    async def test_add_document_without_content_extracts_from_url(self, knowledge_service):
        """Testa que o conteúdo é extraído da URL quando não fornecido"""
        extracted_content = "Conteúdo extraído da URL sobre legislação..."
        
        # Mock do scraper
        knowledge_service.scraper.extract_content = AsyncMock(
            return_value=extracted_content
        )
        
        # Mock do RAGService
        knowledge_service.rag_service._get_embedding = Mock(
            return_value=[0.1, 0.2, 0.3]
        )
        knowledge_service.rag_service.collection.add = Mock()
        
        doc_id = await knowledge_service.add_document(
            title="CLT - Artigo 7º",
            source_url="http://planalto.gov.br/clt",
            category="Direito Trabalhista"
            # content não fornecido
        )
        
        # Verifica que o scraper foi chamado
        knowledge_service.scraper.extract_content.assert_called_once_with(
            "http://planalto.gov.br/clt"
        )
        
        # Verifica que o documento foi adicionado com conteúdo extraído
        assert doc_id is not None
        
        # Verifica que o embedding foi gerado com o conteúdo extraído
        knowledge_service.rag_service._get_embedding.assert_called_once_with(extracted_content)

    async def test_add_document_scraper_error_propagates(self, knowledge_service):
        """Testa que erros do scraper são propagados corretamente"""
        # Mock do scraper que levanta erro
        knowledge_service.scraper.extract_content = AsyncMock(
            side_effect=ValueError("Erro HTTP 404 ao acessar URL")
        )
        
        with pytest.raises(ValueError) as exc_info:
            await knowledge_service.add_document(
                title="Documento Inexistente",
                source_url="http://example.com/notfound",
                category="Teste"
            )
        
        assert "Erro HTTP 404" in str(exc_info.value)

    async def test_add_document_stores_correct_metadata(self, knowledge_service):
        """Testa que os metadados são armazenados corretamente"""
        # Mock do RAGService
        knowledge_service.rag_service._get_embedding = Mock(
            return_value=[0.1, 0.2, 0.3]
        )
        knowledge_service.rag_service.collection.add = Mock()
        
        title = "Lei 8.078/90"
        source_url = "http://planalto.gov.br/lei8078"
        category = "Direito do Consumidor"
        content = "Código de Defesa do Consumidor..."
        
        await knowledge_service.add_document(
            title=title,
            source_url=source_url,
            category=category,
            content=content
        )
        
        # Verifica os metadados passados para o ChromaDB
        call_args = knowledge_service.rag_service.collection.add.call_args
        metadata = call_args.kwargs['metadatas'][0]
        
        assert metadata['title'] == title
        assert metadata['source'] == source_url
        assert metadata['category'] == category
        assert 'doc_id' in metadata
        assert 'created_at' in metadata

    async def test_add_document_generates_embedding(self, knowledge_service):
        """Testa que o embedding é gerado corretamente"""
        content = "Conteúdo do documento legal para gerar embedding"
        
        # Mock do RAGService
        mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        knowledge_service.rag_service._get_embedding = Mock(
            return_value=mock_embedding
        )
        knowledge_service.rag_service.collection.add = Mock()
        
        await knowledge_service.add_document(
            title="Teste",
            source_url="http://example.com",
            category="Teste",
            content=content
        )
        
        # Verifica que o embedding foi gerado com o conteúdo correto
        knowledge_service.rag_service._get_embedding.assert_called_once_with(content)
        
        # Verifica que o embedding foi passado para o ChromaDB
        call_args = knowledge_service.rag_service.collection.add.call_args
        embeddings = call_args.kwargs['embeddings']
        assert embeddings[0] == mock_embedding

    async def test_add_document_with_special_characters(self, knowledge_service):
        """Testa adição de documento com caracteres especiais"""
        # Mock do RAGService
        knowledge_service.rag_service._get_embedding = Mock(
            return_value=[0.1, 0.2, 0.3]
        )
        knowledge_service.rag_service.collection.add = Mock()
        
        title = "Lei com Ç, Ã, É - Artigo 1º"
        content = "Conteúdo com acentuação e caracteres especiais: § 1º, Art. 2º..."
        
        doc_id = await knowledge_service.add_document(
            title=title,
            source_url="http://example.com/lei",
            category="Teste",
            content=content
        )
        
        assert doc_id is not None
        # Verifica que não houve erro com caracteres especiais
        knowledge_service.rag_service.collection.add.assert_called_once()
