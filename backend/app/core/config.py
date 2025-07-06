from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Configuration
    app_name: str = Field(default="RAG Production System", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # API Configuration
    api_prefix: str = Field(default="/api", description="API prefix")
    allowed_hosts: List[str] = Field(default=["*"], description="Allowed hosts")
    
    # Database Configuration
    database_url: str = Field(..., description="PostgreSQL database URL")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model")
    openai_embedding_model: str = Field(default="text-embedding-3-small", description="OpenAI embedding model")
    
    # Vector Database Configuration
    vector_db_type: str = Field(default="chroma", description="Vector database type (chroma or pinecone)")
    
    # ChromaDB Configuration (default)
    chroma_host: str = Field(default="localhost", description="ChromaDB host")
    chroma_port: int = Field(default=8001, description="ChromaDB port")
    chroma_collection_name: str = Field(default="rag_documents", description="ChromaDB collection name")
    
    # Pinecone Configuration (optional)
    pinecone_api_key: Optional[str] = Field(default=None, description="Pinecone API key")
    pinecone_environment: Optional[str] = Field(default=None, description="Pinecone environment")
    pinecone_index_name: str = Field(default="rag-documents", description="Pinecone index name")
    
    # Document Processing
    max_file_size: int = Field(default=50 * 1024 * 1024, description="Maximum file size in bytes (50MB)")
    allowed_file_types: List[str] = Field(
        default=["pdf", "docx", "pptx", "txt", "md"],
        description="Allowed file types"
    )
    chunk_size: int = Field(default=1000, description="Default chunk size for text splitting")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    
    # Authentication
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration time")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="CORS allowed origins"
    )
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    
    # AWS Configuration (for S3 storage)
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    aws_region: str = Field(default="us-east-1", description="AWS region")
    s3_bucket_name: Optional[str] = Field(default=None, description="S3 bucket name for file storage")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 