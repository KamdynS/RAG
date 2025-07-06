from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query, Body
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
    FileType,
    DocumentFilterRequest,
    BulkOperationRequest,
    BulkOperationResponse
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
    group_id: Optional[str] = Query(None, description="Document group ID"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
    custom_metadata: Optional[str] = Query(None, description="JSON string of custom metadata"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Upload a document for processing.
    
    - **file**: The document file to upload
    - **knowledge_base_id**: Optional knowledge base to associate with
    - **group_id**: Optional document group ID
    - **tags**: Comma-separated list of tags
    - **custom_metadata**: JSON string of custom metadata
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
        
        # Parse tags
        parsed_tags = []
        if tags:
            parsed_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Parse custom metadata
        parsed_metadata = {}
        if custom_metadata:
            try:
                import json
                parsed_metadata = json.loads(custom_metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in custom_metadata")
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Process the document
        document_response = await document_service.process_document(
            document_id=document_id,
            file=file,
            knowledge_base_id=knowledge_base_id,
            group_id=group_id,
            tags=parsed_tags,
            custom_metadata=parsed_metadata
        )
        
        logger.info(f"Document uploaded successfully: {document_id}")
        return document_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during document upload")


@router.post("/filter", response_model=DocumentListResponse)
async def filter_documents(
    filters: DocumentFilterRequest = Body(...),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Filter documents with advanced criteria.
    
    This endpoint provides comprehensive filtering capabilities including:
    - Text search across filename, title, author, and tags
    - Status, file type, group, and tag filtering
    - Date range filtering (created/updated)
    - Size and page count filtering
    - Metadata filtering (language, author)
    - Custom metadata filtering
    - Sorting options
    """
    try:
        documents_response = await document_service.list_documents(
            page=page,
            size=size,
            filters=filters
        )
        return documents_response
        
    except Exception as e:
        logger.error(f"Error filtering documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while filtering documents")


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    group_id: Optional[str] = Query(None, description="Filter by group"),
    file_type: Optional[FileType] = Query(None, description="Filter by file type"),
    search: Optional[str] = Query(None, description="Search query"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    List documents with basic filtering and pagination.
    
    - **page**: Page number (starting from 1)
    - **size**: Number of documents per page
    - **status**: Filter by document status
    - **group_id**: Filter by document group
    - **file_type**: Filter by file type
    - **search**: Search query
    """
    try:
        # Build filters from query parameters
        filters = None
        if any([status, group_id, file_type, search]):
            filters = DocumentFilterRequest(
                search_query=search,
                status=[status] if status else None,
                group_id=[group_id] if group_id else None,
                file_type=[file_type] if file_type else None
            )
        
        documents_response = await document_service.list_documents(
            page=page,
            size=size,
            filters=filters
        )
        return documents_response
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while listing documents")


@router.get("/filters/available")
async def get_available_filters(
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Get available filter options based on existing documents.
    
    Returns all unique values for various filter fields to help
    build dynamic filter UIs.
    """
    try:
        available_filters = await document_service._build_available_filters()
        return available_filters
        
    except Exception as e:
        logger.error(f"Error getting available filters: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while getting filters")


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


@router.put("/{document_id}/tags", response_model=DocumentResponse)
async def update_document_tags(
    document_id: str,
    tags: List[str] = Body(..., description="List of tags"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Update document tags.
    
    - **document_id**: The document ID
    - **tags**: New list of tags
    """
    try:
        updated_document = await document_service.update_document_tags(document_id, tags)
        logger.info(f"Document tags updated successfully: {document_id}")
        return updated_document
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating document tags {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while updating tags")


@router.put("/{document_id}/group", response_model=DocumentResponse)
async def update_document_group(
    document_id: str,
    group_id: Optional[str] = Body(None, description="Group ID (null to remove from group)"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Update document group.
    
    - **document_id**: The document ID
    - **group_id**: New group ID (null to remove from group)
    """
    try:
        updated_document = await document_service.update_document_group(document_id, group_id)
        logger.info(f"Document group updated successfully: {document_id}")
        return updated_document
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating document group {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while updating group")


@router.post("/bulk", response_model=BulkOperationResponse)
async def bulk_operation(
    request: BulkOperationRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Perform bulk operations on multiple documents.
    
    Supported operations:
    - **tag**: Add tags to documents
    - **untag**: Remove tags from documents  
    - **group**: Move documents to a group
    - **delete**: Delete multiple documents
    """
    try:
        affected_count = 0
        failed_documents = []
        
        if request.operation == "tag" and request.tag_ids:
            # Add tags to documents
            for doc_id in request.document_ids:
                try:
                    document = await document_service.get_document(doc_id)
                    if document:
                        # Get tag names from IDs
                        tag_names = []
                        for tag_id in request.tag_ids:
                            tag = await document_service.tag_service.get_tag(tag_id)
                            if tag:
                                tag_names.append(tag.name)
                        
                        # Merge with existing tags
                        new_tags = list(set(document.tags + tag_names))
                        await document_service.update_document_tags(doc_id, new_tags)
                        affected_count += 1
                    else:
                        failed_documents.append(doc_id)
                except Exception as e:
                    logger.error(f"Error tagging document {doc_id}: {str(e)}")
                    failed_documents.append(doc_id)
        
        elif request.operation == "untag" and request.tag_ids:
            # Remove tags from documents
            for doc_id in request.document_ids:
                try:
                    document = await document_service.get_document(doc_id)
                    if document:
                        # Get tag names from IDs
                        tag_names_to_remove = []
                        for tag_id in request.tag_ids:
                            tag = await document_service.tag_service.get_tag(tag_id)
                            if tag:
                                tag_names_to_remove.append(tag.name)
                        
                        # Remove tags
                        new_tags = [tag for tag in document.tags if tag not in tag_names_to_remove]
                        await document_service.update_document_tags(doc_id, new_tags)
                        affected_count += 1
                    else:
                        failed_documents.append(doc_id)
                except Exception as e:
                    logger.error(f"Error untagging document {doc_id}: {str(e)}")
                    failed_documents.append(doc_id)
        
        elif request.operation == "group" and request.group_id:
            # Move documents to group
            for doc_id in request.document_ids:
                try:
                    document = await document_service.get_document(doc_id)
                    if document:
                        await document_service.update_document_group(doc_id, request.group_id)
                        affected_count += 1
                    else:
                        failed_documents.append(doc_id)
                except Exception as e:
                    logger.error(f"Error grouping document {doc_id}: {str(e)}")
                    failed_documents.append(doc_id)
        
        elif request.operation == "delete":
            # Delete documents
            for doc_id in request.document_ids:
                try:
                    success = await document_service.delete_document(doc_id)
                    if success:
                        affected_count += 1
                    else:
                        failed_documents.append(doc_id)
                except Exception as e:
                    logger.error(f"Error deleting document {doc_id}: {str(e)}")
                    failed_documents.append(doc_id)
        
        else:
            raise HTTPException(status_code=400, detail="Invalid operation or missing required parameters")
        
        message = f"Bulk {request.operation} operation completed successfully"
        if failed_documents:
            message += f" ({len(failed_documents)} failed)"
        
        return BulkOperationResponse(
            message=message,
            affected_count=affected_count,
            failed_documents=failed_documents if failed_documents else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk operation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during bulk operation")


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
            "updated_at": document.updated_at,
            "group": {
                "id": document.group_id,
                "name": document.group_name
            } if document.group_id else None,
            "tags": document.tags,
            "metadata": document.metadata
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