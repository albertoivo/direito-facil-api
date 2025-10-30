"""
Testes para o serviço RAG (Retrieval-Augmented Generation)
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict

from app.services.rag_service import RAGService
from app.services.prompt_builder import ComplexityLevel
from app.schemas.legal_response import LegalResponse


class TestRAGService:
    """Testes para a classe RAGService"""

    @pytest.fixture
    def rag_service(self):
        """Fixture para criar instância do RAGService"""
        with patch('app.services.rag_service.chromadb.PersistentClient'):
            service = RAGService()
            return service

    @pytest.fixture
    def sample_docs(self) -> List[Dict]:
        """Fixture com documentos de exemplo"""
        return [
            {
                "content": "O Código de Defesa do Consumidor garante o direito à troca de produtos com defeito.",
                "title": "CDC - Artigo 18",
                "source": "Lei 8.078/90",
                "category": "Direito do Consumidor",
                "relevance_score": 0.95
            },
            {
                "content": "O prazo para troca de produtos com defeito é de 30 dias para produtos não duráveis.",
                "title": "CDC - Artigo 26",
                "source": "Lei 8.078/90",
                "category": "Direito do Consumidor",
                "relevance_score": 0.87
            },
            {
                "content": "O consumidor pode exigir a substituição do produto por outro da mesma espécie.",
                "title": "CDC - Artigo 18, § 1º",
                "source": "Lei 8.078/90",
                "category": "Direito do Consumidor",
                "relevance_score": 0.82
            }
        ]

    def test_cache_key_generation(self, rag_service):
        """Testa se a geração de chave de cache é consistente"""
        text = "Teste de embedding"
        key1 = rag_service._get_cache_key(text)
        key2 = rag_service._get_cache_key(text)
        
        assert key1 == key2, "Cache keys devem ser iguais para o mesmo texto"
        assert len(key1) == 32, "Cache key deve ser um hash MD5 (32 caracteres)"

    def test_cache_key_different_texts(self, rag_service):
        """Testa se textos diferentes geram chaves diferentes"""
        key1 = rag_service._get_cache_key("Texto 1")
        key2 = rag_service._get_cache_key("Texto 2")
        
        assert key1 != key2, "Textos diferentes devem gerar chaves diferentes"

    @patch('app.services.rag_service.client.embeddings.create')
    def test_get_embedding_caching(self, mock_create, rag_service):
        """Testa se o cache de embeddings funciona corretamente"""
        # Configurar mock
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_create.return_value = mock_response
        
        # Habilitar cache
        rag_service._cache_enabled = True
        
        # Primeira chamada - deve usar a API
        text = "Teste de cache"
        embedding1 = rag_service._get_embedding(text)
        assert mock_create.call_count == 1
        
        # Segunda chamada - deve usar o cache
        embedding2 = rag_service._get_embedding(text)
        assert mock_create.call_count == 1, "Não deve chamar a API novamente"
        
        # Embeddings devem ser iguais
        assert embedding1 == embedding2

    @patch('app.services.rag_service.client.embeddings.create')
    def test_get_embedding_cache_disabled(self, mock_create, rag_service):
        """Testa comportamento quando o cache está desabilitado"""
        # Configurar mock
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_create.return_value = mock_response
        
        # Desabilitar cache
        rag_service._cache_enabled = False
        
        # Fazer duas chamadas
        text = "Teste sem cache"
        rag_service._get_embedding(text)
        rag_service._get_embedding(text)
        
        # Deve chamar a API duas vezes
        assert mock_create.call_count == 2

    @patch('app.services.rag_service.client.embeddings.create')
    def test_cache_size_limit(self, mock_create, rag_service):
        """Testa se o cache respeita o limite de tamanho"""
        # Configurar mock
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_create.return_value = mock_response
        
        # Configurar cache pequeno
        rag_service._cache_enabled = True
        rag_service._cache_max_size = 2
        
        # Adicionar 3 itens ao cache
        rag_service._get_embedding("texto1")
        rag_service._get_embedding("texto2")
        rag_service._get_embedding("texto3")
        
        # Cache não deve exceder o tamanho máximo
        assert len(rag_service._embedding_cache) <= 2

    def test_clear_embedding_cache(self, rag_service):
        """Testa a limpeza do cache"""
        # Adicionar itens ao cache
        rag_service._embedding_cache = {
            "key1": [0.1, 0.2],
            "key2": [0.3, 0.4]
        }
        
        # Limpar cache
        rag_service.clear_embedding_cache()
        
        # Cache deve estar vazio
        assert len(rag_service._embedding_cache) == 0

    def test_get_cache_stats(self, rag_service):
        """Testa a obtenção de estatísticas do cache"""
        rag_service._cache_enabled = True
        rag_service._cache_max_size = 100
        rag_service._embedding_cache = {"key1": [0.1], "key2": [0.2]}
        
        stats = rag_service.get_cache_stats()
        
        assert stats["enabled"] == True
        assert stats["current_size"] == 2
        assert stats["max_size"] == 100
        assert stats["usage_percent"] == 2.0

    @pytest.mark.asyncio
    @patch('app.services.rag_service.client.embeddings.create')
    async def test_search_relevant_documents(self, mock_create, rag_service):
        """Testa a busca de documentos relevantes"""
        # Configurar mock para embeddings
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_create.return_value = mock_response
        
        # Configurar mock para ChromaDB
        mock_results = {
            "documents": [["Documento 1", "Documento 2"]],
            "metadatas": [[
                {"title": "Doc 1", "source": "Fonte 1", "category": "Cat 1"},
                {"title": "Doc 2", "source": "Fonte 2", "category": "Cat 2"}
            ]],
            "distances": [[0.1, 0.2]]
        }
        rag_service.collection.query = Mock(return_value=mock_results)
        
        # Executar busca
        results = await rag_service.search_relevant_documents("teste", top_k=5)
        
        # Validações
        assert len(results) == 2
        assert all('content' in doc for doc in results)
        assert all('relevance_score' in doc for doc in results)
        assert results[0]['relevance_score'] == 0.9  # 1 - 0.1
        assert results[1]['relevance_score'] == 0.8  # 1 - 0.2

    @pytest.mark.asyncio
    @patch('app.services.rag_service.client.chat.completions.create')
    async def test_generate_legal_response(self, mock_create, rag_service, sample_docs):
        """Testa a geração de resposta jurídica"""
        # Configurar mock
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Resposta gerada pelo LLM"))]
        mock_create.return_value = mock_response
        
        # Gerar resposta
        question = "Quais são meus direitos ao comprar um produto com defeito?"
        response = await rag_service.generate_legal_response(
            question=question,
            relevant_docs=sample_docs,
            user_context="Comprei um celular que veio com defeito",
            complexity=ComplexityLevel.SIMPLE
        )
        
        # Validações
        assert isinstance(response, LegalResponse)
        assert response.answer == "Resposta gerada pelo LLM"
        assert len(response.sources) > 0
        assert 0 <= response.confidence_score <= 100
        assert response.category == "Direito do Consumidor"
        assert len(response.disclaimer) > 0

    @pytest.mark.asyncio
    @patch('app.services.rag_service.client.chat.completions.create')
    async def test_generate_legal_response_different_complexities(self, mock_create, rag_service, sample_docs):
        """Testa geração de resposta com diferentes níveis de complexidade"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Resposta"))]
        mock_create.return_value = mock_response
        
        # Testar cada nível de complexidade
        for complexity in ComplexityLevel:
            response = await rag_service.generate_legal_response(
                question="Teste",
                relevant_docs=sample_docs,
                complexity=complexity
            )
            assert isinstance(response, LegalResponse)

    @pytest.mark.asyncio
    async def test_search_relevant_documents_empty_results(self, rag_service):
        """Testa comportamento quando não há resultados"""
        # Configurar mock para retornar vazio
        mock_results = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
        rag_service.collection.query = Mock(return_value=mock_results)
        
        with patch('app.services.rag_service.client.embeddings.create') as mock_create:
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1, 0.2])]
            mock_create.return_value = mock_response
            
            results = await rag_service.search_relevant_documents("teste")
            assert results == []

    @pytest.mark.asyncio
    async def test_get_knowledge_base_size(self, rag_service):
        """Testa obtenção do tamanho da base de conhecimento"""
        rag_service.collection.count = Mock(return_value=42)
        
        size = await rag_service.get_knowledge_base_size()
        assert size == 42

    @pytest.mark.asyncio
    async def test_get_available_categories(self, rag_service):
        """Testa obtenção de categorias disponíveis"""
        categories = await rag_service.get_available_categories()
        
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "Direito do Consumidor" in categories
        assert "Direito Trabalhista" in categories

    @pytest.mark.asyncio
    async def test_health_check_success(self, rag_service):
        """Testa health check quando o serviço está saudável"""
        rag_service.collection.count = Mock(return_value=10)
        
        status = await rag_service.health_check()
        assert status == "ok"

    @pytest.mark.asyncio
    async def test_health_check_failure(self, rag_service):
        """Testa health check quando o serviço falha"""
        rag_service.collection.count = Mock(side_effect=Exception("Erro"))
        
        status = await rag_service.health_check()
        assert status == "error"

    @pytest.mark.asyncio
    @patch('app.services.rag_service.client.chat.completions.create')
    async def test_check_llm_status_success(self, mock_create, rag_service):
        """Testa verificação de status do LLM quando está disponível"""
        mock_response = Mock()
        mock_create.return_value = mock_response
        
        status = await rag_service.check_llm_status()
        assert status == True

    @pytest.mark.asyncio
    @patch('app.services.rag_service.client.chat.completions.create')
    async def test_check_llm_status_failure(self, mock_create, rag_service):
        """Testa verificação de status do LLM quando falha"""
        mock_create.side_effect = Exception("API Error")
        
        status = await rag_service.check_llm_status()
        assert status == False
