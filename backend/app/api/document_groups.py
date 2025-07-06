from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
import logging

from app.models.document import (
    DocumentGroup,
    DocumentGroupCreateRequest,
    DocumentGroupUpdateRequest,
    DocumentGroupListResponse
)
from app.models.common import ErrorResponse
from app.services.document_group_service import DocumentGroupService

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get document group service
def get_document_group_service() -> DocumentGroupService:
    return DocumentGroupService()


@router.post("/", response_model=DocumentGroup)
async def create_document_group(
    request: DocumentGroupCreateRequest,
    group_service: DocumentGroupService = Depends(get_document_group_service)
):
    """
    Create a new document group.
    
    - **name**: Group name (required)
    - **description**: Group description (optional)
    - **color**: Group color for UI (optional)
    - **icon**: Group icon name (optional)
    - **parent_id**: Parent group ID for hierarchical grouping (optional)
    """
    try:
        group = await group_service.create_group(request)
        logger.info(f"Document group created successfully: {group.id}")
        return group
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating document group: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during group creation")


@router.get("/", response_model=DocumentGroupListResponse)
async def list_document_groups(
    include_empty: bool = Query(True, description="Include groups with no documents"),
    group_service: DocumentGroupService = Depends(get_document_group_service)
):
    """
    List all document groups.
    
    - **include_empty**: Whether to include groups with no documents
    """
    try:
        groups_response = await group_service.list_groups(include_empty=include_empty)
        return groups_response
        
    except Exception as e:
        logger.error(f"Error listing document groups: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while listing groups")


@router.get("/hierarchy")
async def get_group_hierarchy(
    group_service: DocumentGroupService = Depends(get_document_group_service)
):
    """
    Get the complete group hierarchy.
    """
    try:
        hierarchy = await group_service.get_group_hierarchy()
        return hierarchy
        
    except Exception as e:
        logger.error(f"Error getting group hierarchy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while getting hierarchy")


@router.get("/summary")
async def get_groups_summary(
    group_service: DocumentGroupService = Depends(get_document_group_service)
):
    """
    Get a summary of document groups statistics.
    """
    try:
        summary = await group_service.get_groups_summary()
        return summary
        
    except Exception as e:
        logger.error(f"Error getting groups summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while getting summary")


@router.get("/{group_id}", response_model=DocumentGroup)
async def get_document_group(
    group_id: str,
    group_service: DocumentGroupService = Depends(get_document_group_service)
):
    """
    Get a specific document group by ID.
    
    - **group_id**: The group ID
    """
    try:
        group = await group_service.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return group
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document group {group_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving group")


@router.put("/{group_id}", response_model=DocumentGroup)
async def update_document_group(
    group_id: str,
    request: DocumentGroupUpdateRequest,
    group_service: DocumentGroupService = Depends(get_document_group_service)
):
    """
    Update a document group.
    
    - **group_id**: The group ID to update
    - **name**: New group name (optional)
    - **description**: New group description (optional)
    - **color**: New group color (optional)
    - **icon**: New group icon (optional)
    - **parent_id**: New parent group ID (optional)
    """
    try:
        updated_group = await group_service.update_group(group_id, request)
        logger.info(f"Document group updated successfully: {group_id}")
        return updated_group
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating document group {group_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during group update")


@router.delete("/{group_id}")
async def delete_document_group(
    group_id: str,
    force: bool = Query(False, description="Force deletion even if group has documents"),
    group_service: DocumentGroupService = Depends(get_document_group_service)
):
    """
    Delete a document group.
    
    - **group_id**: The group ID to delete
    - **force**: Whether to force deletion even if group contains documents
    """
    try:
        await group_service.delete_group(group_id, force=force)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Group deleted successfully",
                "deleted_group_id": group_id
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting document group {group_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting group") 