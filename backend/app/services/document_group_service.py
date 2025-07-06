import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.models.document import (
    DocumentGroup,
    DocumentGroupCreateRequest,
    DocumentGroupUpdateRequest,
    DocumentGroupListResponse
)

logger = logging.getLogger(__name__)


class DocumentGroupService:
    """Service for managing document groups and collections."""
    
    def __init__(self):
        # In-memory storage for MVP (replace with database in production)
        self.groups: Dict[str, DocumentGroup] = {}
        self._initialize_default_groups()
    
    def _initialize_default_groups(self):
        """Initialize default document groups."""
        default_groups = [
            {
                "id": "group_financial",
                "name": "Financial Reports",
                "description": "Financial documents, reports, and statements",
                "color": "#3B82F6",
                "icon": "chart-bar"
            },
            {
                "id": "group_legal",
                "name": "Legal Documents",
                "description": "Contracts, agreements, and legal documents",
                "color": "#8B5CF6",
                "icon": "scale"
            },
            {
                "id": "group_hr",
                "name": "HR Documents",
                "description": "Human resources policies and procedures",
                "color": "#10B981",
                "icon": "users"
            },
            {
                "id": "group_technical",
                "name": "Technical Documentation",
                "description": "Technical specifications, manuals, and guides",
                "color": "#F59E0B",
                "icon": "cog"
            },
            {
                "id": "group_marketing",
                "name": "Marketing Materials",
                "description": "Marketing documents, presentations, and materials",
                "color": "#EF4444",
                "icon": "megaphone"
            }
        ]
        
        for group_data in default_groups:
            group = DocumentGroup(
                **group_data,
                created_at=datetime.utcnow(),
                document_count=0
            )
            self.groups[group.id] = group
    
    async def create_group(self, request: DocumentGroupCreateRequest) -> DocumentGroup:
        """
        Create a new document group.
        
        Args:
            request: Group creation request
            
        Returns:
            Created DocumentGroup
        """
        try:
            group_id = f"group_{uuid.uuid4().hex[:8]}"
            
            # Validate parent group exists if specified
            if request.parent_id and request.parent_id not in self.groups:
                raise ValueError(f"Parent group {request.parent_id} not found")
            
            # Check for name conflicts
            existing_names = [g.name.lower() for g in self.groups.values()]
            if request.name.lower() in existing_names:
                raise ValueError(f"Group with name '{request.name}' already exists")
            
            group = DocumentGroup(
                id=group_id,
                name=request.name,
                description=request.description,
                color=request.color,
                icon=request.icon,
                parent_id=request.parent_id,
                created_at=datetime.utcnow(),
                document_count=0
            )
            
            self.groups[group_id] = group
            
            logger.info(f"Created document group: {group_id}")
            return group
            
        except Exception as e:
            logger.error(f"Error creating document group: {str(e)}")
            raise
    
    async def get_group(self, group_id: str) -> Optional[DocumentGroup]:
        """
        Get a document group by ID.
        
        Args:
            group_id: Group ID
            
        Returns:
            DocumentGroup if found, None otherwise
        """
        return self.groups.get(group_id)
    
    async def list_groups(self, include_empty: bool = True) -> DocumentGroupListResponse:
        """
        List all document groups.
        
        Args:
            include_empty: Whether to include empty groups
            
        Returns:
            DocumentGroupListResponse
        """
        try:
            groups = list(self.groups.values())
            
            if not include_empty:
                groups = [g for g in groups if g.document_count > 0]
            
            # Sort by name
            groups.sort(key=lambda x: x.name)
            
            return DocumentGroupListResponse(
                groups=groups,
                total=len(groups)
            )
            
        except Exception as e:
            logger.error(f"Error listing document groups: {str(e)}")
            raise
    
    async def update_group(
        self, 
        group_id: str, 
        request: DocumentGroupUpdateRequest
    ) -> DocumentGroup:
        """
        Update a document group.
        
        Args:
            group_id: Group ID
            request: Group update request
            
        Returns:
            Updated DocumentGroup
        """
        try:
            group = self.groups.get(group_id)
            if not group:
                raise ValueError(f"Group {group_id} not found")
            
            # Validate parent group exists if specified
            if request.parent_id and request.parent_id not in self.groups:
                raise ValueError(f"Parent group {request.parent_id} not found")
            
            # Check for circular references
            if request.parent_id and self._would_create_cycle(group_id, request.parent_id):
                raise ValueError("Cannot create circular group hierarchy")
            
            # Update fields
            if request.name is not None:
                # Check for name conflicts
                existing_names = [g.name.lower() for g in self.groups.values() if g.id != group_id]
                if request.name.lower() in existing_names:
                    raise ValueError(f"Group with name '{request.name}' already exists")
                group.name = request.name
            
            if request.description is not None:
                group.description = request.description
            
            if request.color is not None:
                group.color = request.color
            
            if request.icon is not None:
                group.icon = request.icon
            
            if request.parent_id is not None:
                group.parent_id = request.parent_id
            
            group.updated_at = datetime.utcnow()
            
            logger.info(f"Updated document group: {group_id}")
            return group
            
        except Exception as e:
            logger.error(f"Error updating document group {group_id}: {str(e)}")
            raise
    
    async def delete_group(self, group_id: str, force: bool = False) -> bool:
        """
        Delete a document group.
        
        Args:
            group_id: Group ID
            force: Whether to force deletion even if group has documents
            
        Returns:
            True if deleted successfully
        """
        try:
            group = self.groups.get(group_id)
            if not group:
                raise ValueError(f"Group {group_id} not found")
            
            # Check if group has documents
            if group.document_count > 0 and not force:
                raise ValueError(f"Group {group_id} contains {group.document_count} documents. Use force=True to delete anyway")
            
            # Remove group
            del self.groups[group_id]
            
            logger.info(f"Deleted document group: {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document group {group_id}: {str(e)}")
            raise
    
    def _would_create_cycle(self, group_id: str, parent_id: str) -> bool:
        """
        Check if setting parent_id would create a circular reference.
        
        Args:
            group_id: Group ID
            parent_id: Proposed parent ID
            
        Returns:
            True if it would create a cycle
        """
        visited = set()
        current = parent_id
        
        while current and current not in visited:
            if current == group_id:
                return True
            visited.add(current)
            current = self.groups.get(current, {}).get("parent_id")
        
        return False
    
    async def get_group_hierarchy(self) -> Dict[str, Any]:
        """
        Get the complete group hierarchy.
        
        Returns:
            Hierarchical structure of groups
        """
        try:
            # Build hierarchy
            hierarchy = {}
            root_groups = []
            
            for group in self.groups.values():
                if group.parent_id is None:
                    root_groups.append(group)
                else:
                    # Add to parent's children
                    parent = hierarchy.get(group.parent_id, {"children": []})
                    parent["children"].append(group)
                    hierarchy[group.parent_id] = parent
            
            # Sort root groups
            root_groups.sort(key=lambda x: x.name)
            
            return {
                "root_groups": root_groups,
                "hierarchy": hierarchy
            }
            
        except Exception as e:
            logger.error(f"Error building group hierarchy: {str(e)}")
            raise
    
    async def increment_document_count(self, group_id: str) -> None:
        """
        Increment the document count for a group.
        
        Args:
            group_id: Group ID
        """
        if group_id in self.groups:
            self.groups[group_id].document_count += 1
    
    async def decrement_document_count(self, group_id: str) -> None:
        """
        Decrement the document count for a group.
        
        Args:
            group_id: Group ID
        """
        if group_id in self.groups and self.groups[group_id].document_count > 0:
            self.groups[group_id].document_count -= 1
    
    async def get_groups_summary(self) -> Dict[str, Any]:
        """
        Get a summary of document groups.
        
        Returns:
            Summary statistics
        """
        try:
            total_groups = len(self.groups)
            groups_with_documents = sum(1 for g in self.groups.values() if g.document_count > 0)
            total_documents = sum(g.document_count for g in self.groups.values())
            
            return {
                "total_groups": total_groups,
                "groups_with_documents": groups_with_documents,
                "empty_groups": total_groups - groups_with_documents,
                "total_documents": total_documents
            }
            
        except Exception as e:
            logger.error(f"Error getting groups summary: {str(e)}")
            raise 