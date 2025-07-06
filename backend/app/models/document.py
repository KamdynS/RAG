from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
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


class DocumentGroup(BaseModel):
    """Document group/collection model."""
    id: str = Field(..., description="Group ID")
    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    color: Optional[str] = Field(None, description="Group color for UI")
    icon: Optional[str] = Field(None, description="Group icon name")
    parent_id: Optional[str] = Field(None, description="Parent group ID for hierarchical grouping")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    document_count: int = Field(default=0, description="Number of documents in group")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "group_123",
                "name": "Financial Reports",
                "description": "Quarterly and annual financial reports",
                "color": "#3B82F6",
                "icon": "chart-bar",
                "parent_id": None,
                "created_at": "2023-01-01T00:00:00Z",
                "document_count": 15
            }
        }


class DocumentTag(BaseModel):
    """Document tag model."""
    id: str = Field(..., description="Tag ID")
    name: str = Field(..., description="Tag name")
    color: Optional[str] = Field(None, description="Tag color")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    usage_count: int = Field(default=0, description="Number of documents using this tag")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "tag_123",
                "name": "urgent",
                "color": "#EF4444",
                "created_at": "2023-01-01T00:00:00Z",
                "usage_count": 5
            }
        }


class DocumentMetadata(BaseModel):
    """Enhanced document metadata model."""
    # File-specific metadata
    pages: Optional[int] = Field(None, description="Number of pages")
    words: Optional[int] = Field(None, description="Number of words")
    language: Optional[str] = Field(None, description="Document language")
    
    # PDF-specific metadata
    title: Optional[str] = Field(None, description="Document title")
    author: Optional[str] = Field(None, description="Document author")
    subject: Optional[str] = Field(None, description="Document subject")
    creator: Optional[str] = Field(None, description="Document creator")
    producer: Optional[str] = Field(None, description="Document producer")
    creation_date: Optional[str] = Field(None, description="Document creation date")
    modification_date: Optional[str] = Field(None, description="Document modification date")
    
    # Processing metadata
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    extracted_entities: Optional[List[str]] = Field(None, description="Extracted entities")
    topics: Optional[List[str]] = Field(None, description="Identified topics")
    
    # Custom metadata
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata fields")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pages": 25,
                "words": 12500,
                "language": "en",
                "title": "Q3 2024 Financial Report",
                "author": "John Doe",
                "creation_date": "2024-01-15T10:30:00Z",
                "processing_time": 45.2,
                "extracted_entities": ["Q3", "2024", "revenue", "profit"],
                "topics": ["finance", "quarterly-report", "performance"],
                "custom_fields": {
                    "department": "finance",
                    "confidentiality": "internal"
                }
            }
        }


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    filename: str = Field(..., description="Original filename")
    file_type: FileType = Field(..., description="File type")
    knowledge_base_id: Optional[str] = Field(None, description="Knowledge base ID")
    group_id: Optional[str] = Field(None, description="Document group ID")
    tags: Optional[List[str]] = Field(default_factory=list, description="Document tags")
    custom_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata")


class DocumentChunk(BaseModel):
    """Model for document chunks."""
    id: str = Field(..., description="Chunk ID")
    document_id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Chunk content")
    chunk_index: int = Field(..., description="Chunk index within document")
    start_offset: int = Field(..., description="Start character offset")
    end_offset: int = Field(..., description="End character offset")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "chunk_123",
                "document_id": "doc_123",
                "content": "This is a sample chunk content...",
                "chunk_index": 0,
                "start_offset": 0,
                "end_offset": 100,
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
    
    # Enhanced fields
    group_id: Optional[str] = Field(None, description="Document group ID")
    group_name: Optional[str] = Field(None, description="Document group name")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata, description="Document metadata")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Search relevance (when returned from search)
    relevance_score: Optional[float] = Field(None, description="Search relevance score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_123",
                "filename": "example.pdf",
                "file_type": "pdf",
                "status": "completed",
                "size": 1024000,
                "chunks_count": 15,
                "group_id": "group_123",
                "group_name": "Financial Reports",
                "tags": ["urgent", "q3-2024"],
                "metadata": {
                    "pages": 25,
                    "words": 12500,
                    "language": "en",
                    "title": "Q3 2024 Financial Report"
                },
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
    
    # Filtering metadata
    applied_filters: Optional[Dict[str, Any]] = Field(None, description="Applied filters")
    available_filters: Optional[Dict[str, Any]] = Field(None, description="Available filter options")
    
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
                        "group_id": "group_123",
                        "group_name": "Financial Reports",
                        "tags": ["urgent"],
                        "metadata": {},
                        "created_at": "2023-01-01T00:00:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 10,
                "applied_filters": {
                    "group_id": "group_123",
                    "tags": ["urgent"]
                }
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


class DocumentFilterRequest(BaseModel):
    """Request model for document filtering."""
    # Text search
    search_query: Optional[str] = Field(None, description="Search query")
    
    # Basic filters
    status: Optional[List[DocumentStatus]] = Field(None, description="Document status filter")
    file_type: Optional[List[FileType]] = Field(None, description="File type filter")
    group_id: Optional[List[str]] = Field(None, description="Document group filter")
    tags: Optional[List[str]] = Field(None, description="Tag filter")
    
    # Date filters
    created_after: Optional[datetime] = Field(None, description="Created after date")
    created_before: Optional[datetime] = Field(None, description="Created before date")
    updated_after: Optional[datetime] = Field(None, description="Updated after date")
    updated_before: Optional[datetime] = Field(None, description="Updated before date")
    
    # Size filters
    min_size: Optional[int] = Field(None, description="Minimum file size in bytes")
    max_size: Optional[int] = Field(None, description="Maximum file size in bytes")
    
    # Metadata filters
    min_pages: Optional[int] = Field(None, description="Minimum number of pages")
    max_pages: Optional[int] = Field(None, description="Maximum number of pages")
    language: Optional[List[str]] = Field(None, description="Language filter")
    author: Optional[List[str]] = Field(None, description="Author filter")
    
    # Custom metadata filters
    custom_filters: Optional[Dict[str, Any]] = Field(None, description="Custom metadata filters")
    
    # Sorting
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "search_query": "financial report",
                "status": ["completed"],
                "file_type": ["pdf"],
                "group_id": ["group_123"],
                "tags": ["urgent"],
                "created_after": "2023-01-01T00:00:00Z",
                "min_size": 1000000,
                "max_pages": 50,
                "language": ["en"],
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        }


class DocumentGroupCreateRequest(BaseModel):
    """Request model for creating document groups."""
    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    color: Optional[str] = Field(None, description="Group color")
    icon: Optional[str] = Field(None, description="Group icon")
    parent_id: Optional[str] = Field(None, description="Parent group ID")


class DocumentGroupUpdateRequest(BaseModel):
    """Request model for updating document groups."""
    name: Optional[str] = Field(None, description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    color: Optional[str] = Field(None, description="Group color")
    icon: Optional[str] = Field(None, description="Group icon")
    parent_id: Optional[str] = Field(None, description="Parent group ID")


class DocumentGroupListResponse(BaseModel):
    """Response model for document group listing."""
    groups: List[DocumentGroup] = Field(..., description="List of document groups")
    total: int = Field(..., description="Total number of groups")


class DocumentTagCreateRequest(BaseModel):
    """Request model for creating document tags."""
    name: str = Field(..., description="Tag name")
    color: Optional[str] = Field(None, description="Tag color")


class DocumentTagListResponse(BaseModel):
    """Response model for document tag listing."""
    tags: List[DocumentTag] = Field(..., description="List of document tags")
    total: int = Field(..., description="Total number of tags")


class BulkOperationRequest(BaseModel):
    """Request model for bulk document operations."""
    document_ids: List[str] = Field(..., description="List of document IDs")
    operation: str = Field(..., description="Operation type (tag, untag, group, delete)")
    
    # Operation-specific parameters
    tag_ids: Optional[List[str]] = Field(None, description="Tag IDs for tag operations")
    group_id: Optional[str] = Field(None, description="Group ID for group operations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_ids": ["doc_123", "doc_456"],
                "operation": "tag",
                "tag_ids": ["tag_123", "tag_456"]
            }
        }


class BulkOperationResponse(BaseModel):
    """Response model for bulk document operations."""
    message: str = Field(..., description="Operation result message")
    affected_count: int = Field(..., description="Number of documents affected")
    failed_documents: Optional[List[str]] = Field(None, description="Documents that failed the operation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Bulk operation completed successfully",
                "affected_count": 2,
                "failed_documents": []
            }
        } 