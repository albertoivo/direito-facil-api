import os
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from typing import List, Dict, Any
import uuid
import logging
from datetime import datetime
from app.schemas.legal_response import LegalResponse, LegalQuery
from dotenv import load_dotenv

load_dotenv()  # carrega o .env
logger = logging.getLogger(__name__)

# Configure the OpenAI client
# The API key is loaded from environment variables.
client = OpenAI()


class RAGService:
    def __init__(self):
        # Configurar ChromaDB para armazenar vetores
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(
            name="legal_knowledge", metadata={"hnsw:space": "cosine"}
        )

        # Modelo de embedding em português
        self.embedding_model = SentenceTransformer(
            "neuralmind/bert-base-portuguese-cased"
        )

    async def search_relevant_documents(
        self, query: str, category: str = None, top_k: int = 5
    ) -> List[Dict]:
        """
        Buscar documentos mais relevantes para a query
        """
        try:
            # Gerar embedding da pergunta
            query_embedding = self.embedding_model.encode([query])[0].tolist()

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
        self, question: str, relevant_docs: List[Dict], user_context: str = None
    ) -> LegalResponse:
        """
        Gerar resposta usando LLM baseado nos documentos encontrados
        """
        try:
            # Construir contexto com documentos relevantes
            context_parts = []
            sources = []

            for doc in relevant_docs:
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

            # Prompt especializado para questões jurídicas
            system_prompt = """
            Você é um assistente jurídico especializado em direito brasileiro. 
            Sua função é fornecer informações claras e acessíveis sobre questões legais básicas.
            
            DIRETRIZES IMPORTANTES:
            1. Use linguagem simples e acessível
            2. Base suas respostas APENAS nas fontes fornecidas
            3. Sempre inclua um disclaimer sobre buscar ajuda profissional
            4. Se não souber ou as fontes não forem suficientes, seja honesto
            5. Organize a resposta de forma didática
            6. Cite as leis/artigos relevantes quando aplicável
            """

            user_prompt = f"""
            PERGUNTA DO USUÁRIO: {question}
            
            {f"CONTEXTO DO USUÁRIO: {user_context}" if user_context else ""}
            
            FONTES JURÍDICAS DISPONÍVEIS:
            {context}
            
            Por favor, forneça uma resposta clara e objetiva baseada nas fontes acima.
            """

            # Chamar OpenAI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # Baixa criatividade para precisão
                max_tokens=800,
            )

            answer = response.choices[0].message.content

            # Calcular confidence score baseado na relevância dos documentos
            avg_relevance = sum(doc["relevance_score"] for doc in relevant_docs) / len(
                relevant_docs
            )
            confidence_score = min(
                avg_relevance * 100, 95
            )  # Max 95% para questões legais

            # Determinar categoria predominante
            categories = [doc["category"] for doc in relevant_docs]
            main_category = max(set(categories), key=categories.count)

            return LegalResponse(
                answer=answer,
                sources=sources,
                confidence_score=confidence_score,
                category=main_category,
                disclaimer="Esta informação tem caráter orientativo. Para questões específicas, consulte um advogado.",
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
        # Implementar logging no banco se necessário
        pass
