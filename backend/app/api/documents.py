from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
import os
from datetime import datetime
import logging

from app.models.document import (
    DocumentResponse, 
    DocumentListResponse, 
    DocumentDeleteResponse,
    DocumentStatus,
    FileType
)
from app.models.common import ErrorResponse, PaginationParams
from app.core.config import settings
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get document service
def get_document_service() -> DocumentService:
    return DocumentService()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    knowledge_base_id: Optional[str] = Query(None, description="Knowledge base ID"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Upload a document for processing.
    
    - **file**: The document file to upload
    - **knowledge_base_id**: Optional knowledge base to associate with
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type '{file_extension}' not supported. Allowed types: {settings.allowed_file_types}"
            )
        
        # Validate file size
        if file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
            )
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Process the document
        document_response = await document_service.process_document(
            document_id=document_id,
            file=file,
            knowledge_base_id=knowledge_base_id
        )
        
        logger.info(f"Document uploaded successfully: {document_id}")
        return document_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during document upload")


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    knowledge_base_id: Optional[str] = Query(None, description="Filter by knowledge base"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    List documents with optional filtering and pagination.
    
    - **page**: Page number (starting from 1)
    - **size**: Number of documents per page
    - **status**: Filter by document status
    - **knowledge_base_id**: Filter by knowledge base
    """
    try:
        documents_response = await document_service.list_documents(
            page=page,
            size=size,
            status=status,
            knowledge_base_id=knowledge_base_id
        )
        return documents_response
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while listing documents")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Get a specific document by ID.
    
    - **document_id**: The document ID
    """
    try:
        document_response = await document_service.get_document(document_id)
        if not document_response:
            raise HTTPException(status_code=404, detail="Document not found")
        return document_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving document")


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Delete a document and its associated data.
    
    - **document_id**: The document ID to delete
    """
    try:
        # Check if document exists
        document = await document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete the document
        await document_service.delete_document(document_id)
        
        return DocumentDeleteResponse(
            message="Document deleted successfully",
            deleted_document_id=document_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting document")


@router.get("/{document_id}/status", response_model=dict)
async def get_document_status(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Get the processing status of a specific document.
    
    - **document_id**: The document ID
    """
    try:
        document = await document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "document_id": document_id,
            "status": document.status,
            "chunks_count": document.chunks_count,
            "updated_at": document.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while getting document status")


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Reprocess a document (useful for failed documents or when updating processing logic).
    
    - **document_id**: The document ID to reprocess
    """
    try:
        document = await document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Reprocess the document
        reprocessed_document = await document_service.reprocess_document(document_id)
        
        logger.info(f"Document reprocessed successfully: {document_id}")
        return reprocessed_document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reprocessing document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while reprocessing document") 