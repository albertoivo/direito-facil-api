from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configurações centralizadas da aplicação"""
    
    # API Keys
    openai_api_key: str
    
    # Database
    database_url: str = "sqlite:///./direito_facil.db"
    
    # ChromaDB
    chroma_path: str = "./chroma_db"
    chroma_collection_name: str = "legal_knowledge"
    
    # LLM Configuration
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 800
    llm_top_p: float = 0.9
    
    # Embedding Configuration
    embedding_model: str = "text-embedding-ada-002"
    
    # RAG Configuration
    top_k_documents: int = 5
    min_relevance_score: float = 0.7
    max_context_documents: int = 3  # Documentos enviados para o LLM
    
    # Validação de Respostas
    strict_source_validation: bool = True  # Validação rigorosa de uso de fontes
    enable_response_validation: bool = True  # Habilitar validação de respostas
    max_confidence_score: float = 95.0  # Score máximo de confiança
    
    # Cache Configuration
    enable_embedding_cache: bool = True
    embedding_cache_size: int = 1000
    
    # Rate Limiting
    rate_limit_per_minute: int = 10
    
    # Logging
    log_level: str = "INFO"
    log_dir: str = "./logs"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
settings = Settings()
