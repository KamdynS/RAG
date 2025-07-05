from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid file format",
                "details": {"allowed_formats": ["pdf", "docx", "txt"]},
                "timestamp": "2023-01-01T00:00:00Z"
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response model."""
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"id": "123", "status": "completed"},
                "timestamp": "2023-01-01T00:00:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="Application version")
    services: Dict[str, str] = Field(..., description="Service statuses")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2023-01-01T00:00:00Z",
                "version": "1.0.0",
                "services": {
                    "database": "healthy",
                    "redis": "healthy",
                    "openai": "healthy",
                    "pinecone": "healthy"
                }
            }
        }


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Page size")
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "size": 10
            }
        } 