import logging
from typing import Dict, List, Optional
import hashlib

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

from app.schemas.legal_response import LegalQuery, LegalResponse
from app.config.settings import settings
from app.services.prompt_builder import PromptBuilder, ComplexityLevel
from app.services.response_validator import ResponseValidator

load_dotenv()  # carrega o .env
logger = logging.getLogger(__name__)

# Configure the OpenAI client
# The API key is loaded from environment variables.
client = OpenAI()


class RAGService:
    def __init__(self):
        # Configurar ChromaDB para armazenar vetores
        self.chroma_client = chromadb.PersistentClient(path=settings.chroma_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.chroma_collection_name, 
            metadata={"hnsw:space": "cosine"}
        )

        # Cache de embeddings
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_enabled = settings.enable_embedding_cache
        self._cache_max_size = settings.embedding_cache_size
        
        # Prompt builder
        self.prompt_builder = PromptBuilder()
    
    def _get_cache_key(self, text: str) -> str:
        """
        Gerar chave única para cache de embeddings
        
        Args:
            text: Texto para gerar a chave
            
        Returns:
            Hash MD5 do texto
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Gerar embedding usando OpenAI com cache
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Lista de floats representando o embedding
        """
        # Verificar cache
        if self._cache_enabled:
            cache_key = self._get_cache_key(text)
            
            if cache_key in self._embedding_cache:
                logger.info(f"Cache hit para embedding: {text[:50]}...")
                return self._embedding_cache[cache_key]
        
        try:
            # Gerar embedding via OpenAI
            response = client.embeddings.create(
                model=settings.embedding_model,
                input=text
            )
            embedding = response.data[0].embedding
            
            # Armazenar no cache
            if self._cache_enabled:
                # Limitar tamanho do cache (FIFO simples)
                if len(self._embedding_cache) >= self._cache_max_size:
                    # Remove o primeiro item
                    first_key = next(iter(self._embedding_cache))
                    del self._embedding_cache[first_key]
                    logger.debug(f"Cache cheio, removendo entrada antiga")
                
                self._embedding_cache[cache_key] = embedding
                logger.debug(f"Embedding armazenado no cache. Tamanho: {len(self._embedding_cache)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            raise
    
    def clear_embedding_cache(self):
        """Limpar cache de embeddings"""
        self._embedding_cache.clear()
        logger.info("Cache de embeddings limpo")
    
    def get_cache_stats(self) -> Dict:
        """Obter estatísticas do cache"""
        return {
            "enabled": self._cache_enabled,
            "current_size": len(self._embedding_cache),
            "max_size": self._cache_max_size,
            "usage_percent": (len(self._embedding_cache) / self._cache_max_size * 100) if self._cache_max_size > 0 else 0
        }

    async def search_relevant_documents(
        self, query: str, category: str = None, top_k: int = 5
    ) -> List[Dict]:
        """
        Buscar documentos mais relevantes para a query
        """
        try:
            # Gerar embedding da pergunta usando cache
            query_embedding = self._get_embedding(query)

            # Filtros opcionais
            where_filter = {}
            if category:
                where_filter["category"] = category

            # Buscar no ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"],
            )

            # Processar resultados
            relevant_docs = []
            for i, (doc, metadata, distance) in enumerate(
                zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ):
                relevant_docs.append(
                    {
                        "content": doc,
                        "source": metadata.get("source", "Fonte não especificada"),
                        "category": metadata.get("category", "Geral"),
                        "relevance_score": 1 - distance,  # Converter distância em score
                        "title": metadata.get("title", f"Documento {i+1}"),
                    }
                )

            return relevant_docs

        except Exception as e:
            logger.error(f"Erro na busca de documentos: {e}")
            return []

    async def generate_legal_response(
        self, 
        question: str, 
        relevant_docs: List[Dict], 
        user_context: Optional[str] = None,
        complexity: ComplexityLevel = ComplexityLevel.SIMPLE
    ) -> LegalResponse:
        """
        Gerar resposta usando LLM baseado nos documentos encontrados
        
        Args:
            question: Pergunta do usuário
            relevant_docs: Documentos relevantes encontrados
            user_context: Contexto adicional do usuário
            complexity: Nível de complexidade da resposta
        """
        try:
            # Construir contexto com documentos relevantes
            context_parts = []
            sources = []

            # Número de documentos enviados para o LLM (configurável via settings)
            max_docs = settings.max_context_documents
            for doc in relevant_docs[:max_docs]:
                context_parts.append(
                    f"FONTE: {doc['title']}\nCONTEÚDO: {doc['content']}\n"
                )
                sources.append(
                    {
                        "title": doc["title"],
                        "source": doc["source"],
                        "relevance_score": doc["relevance_score"],
                    }
                )

            context = "\n---\n".join(context_parts)

            # Usar o prompt builder para gerar prompts dinâmicos
            system_prompt = self.prompt_builder.build_system_prompt(complexity)
            user_prompt = self.prompt_builder.build_user_prompt(
                question=question,
                context=context,
                user_context=user_context
            )

            # Chamar OpenAI
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=settings.llm_temperature,
                top_p=settings.llm_top_p,
                max_tokens=settings.llm_max_tokens,
            )

            answer = response.choices[0].message.content

            # Calcular confidence score baseado na relevância dos documentos
            avg_relevance = sum(doc["relevance_score"] for doc in relevant_docs) / len(
                relevant_docs
            )
            initial_confidence = min(avg_relevance * 100, 95)
            
            # ✅ VALIDAR se a resposta usa as fontes fornecidas
            adjusted_confidence, validation_details = ResponseValidator.validate_and_score(
                response=answer,
                sources=sources,
                original_confidence=initial_confidence
            )
            
            # Log de validação
            logger.info(f"Validação da resposta: {validation_details['validation_message']}")
            logger.info(f"Fontes citadas: {validation_details['cited_sources_count']}")
            logger.info(f"Confiança ajustada: {initial_confidence:.2f} → {adjusted_confidence:.2f}")
            
            if validation_details['hallucination_indicators']:
                logger.warning(f"Indicadores de alucinação: {validation_details['hallucination_indicators']}")

            # Determinar categoria predominante
            categories = [doc["category"] for doc in relevant_docs]
            main_category = max(set(categories), key=categories.count)
            
            # Usar disclaimer apropriado baseado na categoria
            category_map = {
                "Direito do Consumidor": "consumidor",
                "Direito Trabalhista": "trabalhista",
                "Direito de Família": "familia",
                "Direito Previdenciário": "previdenciario"
            }
            disclaimer_type = category_map.get(main_category, "geral")
            disclaimer = self.prompt_builder.get_disclaimer(disclaimer_type)

            return LegalResponse(
                answer=answer,
                sources=sources,
                confidence_score=adjusted_confidence,
                category=main_category,
                disclaimer=disclaimer,
            )

        except Exception as e:
            logger.error(f"Erro na geração de resposta: {e}")
            raise

    async def get_knowledge_base_size(self) -> int:
        """
        Retornar quantidade de documentos na base
        """
        try:
            return self.collection.count()
        except:
            return 0

    async def get_available_categories(self) -> List[str]:
        """
        Retornar categorias disponíveis
        """
        return [
            "Direito do Consumidor",
            "Direito Civil - Contratos",
            "Direito Trabalhista",
            "Direito de Família",
            "Registros Civís",
            "Pequenas Causas",
            "Direito Previdenciário",
        ]

    async def health_check(self) -> str:
        """
        Verificar saúde do serviço de vetores
        """
        try:
            self.collection.count()
            return "ok"
        except:
            return "error"

    async def log_query(self, query: LegalQuery, response: LegalResponse, db):
        """
        Log das consultas para análise posterior
        """
        # Implementar logging

    async def check_llm_status(self) -> bool:
        """
        Verificar se o serviço LLM está disponível
        """
        try:
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "system", "content": "Teste de disponibilidade"}],
                max_tokens=1
            )
            return response is not None
        except Exception as e:
            logger.error(f"Erro ao verificar status do LLM: {e}")
            return False
            return response is not None
        except Exception as e:
            logger.error(f"Erro ao verificar status do LLM: {e}")
            return False