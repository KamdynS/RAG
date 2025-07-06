from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
import logging

from app.models.document import (
    DocumentTag,
    DocumentTagCreateRequest,
    DocumentTagListResponse
)
from app.models.common import ErrorResponse
from app.services.document_tag_service import DocumentTagService

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get document tag service
def get_document_tag_service() -> DocumentTagService:
    return DocumentTagService()


@router.post("/", response_model=DocumentTag)
async def create_document_tag(
    request: DocumentTagCreateRequest,
    tag_service: DocumentTagService = Depends(get_document_tag_service)
):
    """
    Create a new document tag.
    
    - **name**: Tag name (required)
    - **color**: Tag color for UI (optional)
    """
    try:
        tag = await tag_service.create_tag(request)
        logger.info(f"Document tag created successfully: {tag.id}")
        return tag
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating document tag: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during tag creation")


@router.get("/", response_model=DocumentTagListResponse)
async def list_document_tags(
    include_unused: bool = Query(True, description="Include tags with no usage"),
    tag_service: DocumentTagService = Depends(get_document_tag_service)
):
    """
    List all document tags.
    
    - **include_unused**: Whether to include tags with no usage
    """
    try:
        tags_response = await tag_service.list_tags(include_unused=include_unused)
        return tags_response
        
    except Exception as e:
        logger.error(f"Error listing document tags: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while listing tags")


@router.get("/popular")
async def get_popular_tags(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of tags to return"),
    tag_service: DocumentTagService = Depends(get_document_tag_service)
):
    """
    Get the most popular tags.
    
    - **limit**: Maximum number of tags to return
    """
    try:
        popular_tags = await tag_service.get_popular_tags(limit=limit)
        return {"tags": popular_tags}
        
    except Exception as e:
        logger.error(f"Error getting popular tags: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while getting popular tags")


@router.get("/search")
async def search_tags(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    tag_service: DocumentTagService = Depends(get_document_tag_service)
):
    """
    Search for tags by name.
    
    - **query**: Search query
    - **limit**: Maximum number of results
    """
    try:
        matching_tags = await tag_service.search_tags(query=query, limit=limit)
        return {"tags": matching_tags, "query": query}
        
    except Exception as e:
        logger.error(f"Error searching tags: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while searching tags")


@router.get("/summary")
async def get_tags_summary(
    tag_service: DocumentTagService = Depends(get_document_tag_service)
):
    """
    Get a summary of document tags statistics.
    """
    try:
        summary = await tag_service.get_tags_summary()
        return summary
        
    except Exception as e:
        logger.error(f"Error getting tags summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while getting summary")


@router.get("/{tag_id}", response_model=DocumentTag)
async def get_document_tag(
    tag_id: str,
    tag_service: DocumentTagService = Depends(get_document_tag_service)
):
    """
    Get a specific document tag by ID.
    
    - **tag_id**: The tag ID
    """
    try:
        tag = await tag_service.get_tag(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        return tag
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document tag {tag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving tag")


@router.put("/{tag_id}", response_model=DocumentTag)
async def update_document_tag(
    tag_id: str,
    name: Optional[str] = Query(None, description="New tag name"),
    color: Optional[str] = Query(None, description="New tag color"),
    tag_service: DocumentTagService = Depends(get_document_tag_service)
):
    """
    Update a document tag.
    
    - **tag_id**: The tag ID to update
    - **name**: New tag name (optional)
    - **color**: New tag color (optional)
    """
    try:
        updated_tag = await tag_service.update_tag(tag_id, name=name, color=color)
        logger.info(f"Document tag updated successfully: {tag_id}")
        return updated_tag
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating document tag {tag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during tag update")


@router.delete("/{tag_id}")
async def delete_document_tag(
    tag_id: str,
    force: bool = Query(False, description="Force deletion even if tag is in use"),
    tag_service: DocumentTagService = Depends(get_document_tag_service)
):
    """
    Delete a document tag.
    
    - **tag_id**: The tag ID to delete
    - **force**: Whether to force deletion even if tag is in use
    """
    try:
        await tag_service.delete_tag(tag_id, force=force)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Tag deleted successfully",
                "deleted_tag_id": tag_id
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting document tag {tag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting tag") 