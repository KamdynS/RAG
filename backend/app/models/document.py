from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, Enum):
    """Supported file types."""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    TXT = "txt"
    MD = "md"


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    filename: str = Field(..., description="Original filename")
    file_type: FileType = Field(..., description="File type")
    knowledge_base_id: Optional[str] = Field(None, description="Knowledge base ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class DocumentChunk(BaseModel):
    """Model for document chunks."""
    id: str = Field(..., description="Chunk ID")
    content: str = Field(..., description="Chunk content")
    chunk_index: int = Field(..., description="Chunk index in document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_123_chunk_1",
                "content": "This is the first chunk of the document...",
                "chunk_index": 1,
                "metadata": {"page": 1, "section": "Introduction"}
            }
        }


class DocumentResponse(BaseModel):
    """Response model for document operations."""
    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    file_type: FileType = Field(..., description="File type")
    status: DocumentStatus = Field(..., description="Processing status")
    size: int = Field(..., description="File size in bytes")
    chunks_count: Optional[int] = Field(None, description="Number of chunks")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_123",
                "filename": "example.pdf",
                "file_type": "pdf",
                "status": "completed",
                "size": 1024000,
                "chunks_count": 15,
                "metadata": {"pages": 10, "author": "John Doe"},
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:05:00Z"
            }
        }


class DocumentListResponse(BaseModel):
    """Response model for document listing."""
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "id": "doc_123",
                        "filename": "example.pdf",
                        "file_type": "pdf",
                        "status": "completed",
                        "size": 1024000,
                        "chunks_count": 15,
                        "metadata": {},
                        "created_at": "2023-01-01T00:00:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 10
            }
        }


class DocumentDeleteResponse(BaseModel):
    """Response model for document deletion."""
    message: str = Field(..., description="Deletion confirmation message")
    deleted_document_id: str = Field(..., description="ID of deleted document")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Document deleted successfully",
                "deleted_document_id": "doc_123"
            }
        } 