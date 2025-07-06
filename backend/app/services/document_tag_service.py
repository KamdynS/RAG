import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.models.document import (
    DocumentTag,
    DocumentTagCreateRequest,
    DocumentTagListResponse
)

logger = logging.getLogger(__name__)


class DocumentTagService:
    """Service for managing document tags."""
    
    def __init__(self):
        # In-memory storage for MVP (replace with database in production)
        self.tags: Dict[str, DocumentTag] = {}
        self._initialize_default_tags()
    
    def _initialize_default_tags(self):
        """Initialize default document tags."""
        default_tags = [
            {
                "id": "tag_urgent",
                "name": "urgent",
                "color": "#EF4444"
            },
            {
                "id": "tag_important",
                "name": "important",
                "color": "#F59E0B"
            },
            {
                "id": "tag_draft",
                "name": "draft",
                "color": "#6B7280"
            },
            {
                "id": "tag_reviewed",
                "name": "reviewed",
                "color": "#10B981"
            },
            {
                "id": "tag_confidential",
                "name": "confidential",
                "color": "#8B5CF6"
            },
            {
                "id": "tag_archived",
                "name": "archived",
                "color": "#64748B"
            },
            {
                "id": "tag_public",
                "name": "public",
                "color": "#06B6D4"
            },
            {
                "id": "tag_internal",
                "name": "internal",
                "color": "#3B82F6"
            }
        ]
        
        for tag_data in default_tags:
            tag = DocumentTag(
                **tag_data,
                created_at=datetime.utcnow(),
                usage_count=0
            )
            self.tags[tag.id] = tag
    
    async def create_tag(self, request: DocumentTagCreateRequest) -> DocumentTag:
        """
        Create a new document tag.
        
        Args:
            request: Tag creation request
            
        Returns:
            Created DocumentTag
        """
        try:
            tag_id = f"tag_{uuid.uuid4().hex[:8]}"
            
            # Check for name conflicts (case-insensitive)
            existing_names = [t.name.lower() for t in self.tags.values()]
            if request.name.lower() in existing_names:
                raise ValueError(f"Tag with name '{request.name}' already exists")
            
            tag = DocumentTag(
                id=tag_id,
                name=request.name.lower().strip(),  # Normalize tag names
                color=request.color,
                created_at=datetime.utcnow(),
                usage_count=0
            )
            
            self.tags[tag_id] = tag
            
            logger.info(f"Created document tag: {tag_id}")
            return tag
            
        except Exception as e:
            logger.error(f"Error creating document tag: {str(e)}")
            raise
    
    async def get_tag(self, tag_id: str) -> Optional[DocumentTag]:
        """
        Get a document tag by ID.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            DocumentTag if found, None otherwise
        """
        return self.tags.get(tag_id)
    
    async def get_tag_by_name(self, tag_name: str) -> Optional[DocumentTag]:
        """
        Get a document tag by name.
        
        Args:
            tag_name: Tag name
            
        Returns:
            DocumentTag if found, None otherwise
        """
        normalized_name = tag_name.lower().strip()
        for tag in self.tags.values():
            if tag.name == normalized_name:
                return tag
        return None
    
    async def list_tags(self, include_unused: bool = True) -> DocumentTagListResponse:
        """
        List all document tags.
        
        Args:
            include_unused: Whether to include unused tags
            
        Returns:
            DocumentTagListResponse
        """
        try:
            tags = list(self.tags.values())
            
            if not include_unused:
                tags = [t for t in tags if t.usage_count > 0]
            
            # Sort by usage count (descending) then by name
            tags.sort(key=lambda x: (-x.usage_count, x.name))
            
            return DocumentTagListResponse(
                tags=tags,
                total=len(tags)
            )
            
        except Exception as e:
            logger.error(f"Error listing document tags: {str(e)}")
            raise
    
    async def update_tag(
        self, 
        tag_id: str, 
        name: Optional[str] = None,
        color: Optional[str] = None
    ) -> DocumentTag:
        """
        Update a document tag.
        
        Args:
            tag_id: Tag ID
            name: New tag name
            color: New tag color
            
        Returns:
            Updated DocumentTag
        """
        try:
            tag = self.tags.get(tag_id)
            if not tag:
                raise ValueError(f"Tag {tag_id} not found")
            
            # Update name if provided
            if name is not None:
                normalized_name = name.lower().strip()
                # Check for name conflicts
                existing_names = [t.name.lower() for t in self.tags.values() if t.id != tag_id]
                if normalized_name in existing_names:
                    raise ValueError(f"Tag with name '{name}' already exists")
                tag.name = normalized_name
            
            # Update color if provided
            if color is not None:
                tag.color = color
            
            logger.info(f"Updated document tag: {tag_id}")
            return tag
            
        except Exception as e:
            logger.error(f"Error updating document tag {tag_id}: {str(e)}")
            raise
    
    async def delete_tag(self, tag_id: str, force: bool = False) -> bool:
        """
        Delete a document tag.
        
        Args:
            tag_id: Tag ID
            force: Whether to force deletion even if tag is in use
            
        Returns:
            True if deleted successfully
        """
        try:
            tag = self.tags.get(tag_id)
            if not tag:
                raise ValueError(f"Tag {tag_id} not found")
            
            # Check if tag is in use
            if tag.usage_count > 0 and not force:
                raise ValueError(f"Tag {tag_id} is used by {tag.usage_count} documents. Use force=True to delete anyway")
            
            # Remove tag
            del self.tags[tag_id]
            
            logger.info(f"Deleted document tag: {tag_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document tag {tag_id}: {str(e)}")
            raise
    
    async def increment_usage(self, tag_id: str) -> None:
        """
        Increment the usage count for a tag.
        
        Args:
            tag_id: Tag ID
        """
        if tag_id in self.tags:
            self.tags[tag_id].usage_count += 1
    
    async def decrement_usage(self, tag_id: str) -> None:
        """
        Decrement the usage count for a tag.
        
        Args:
            tag_id: Tag ID
        """
        if tag_id in self.tags and self.tags[tag_id].usage_count > 0:
            self.tags[tag_id].usage_count -= 1
    
    async def get_or_create_tag(self, tag_name: str, color: Optional[str] = None) -> DocumentTag:
        """
        Get an existing tag or create a new one.
        
        Args:
            tag_name: Tag name
            color: Tag color (for new tags)
            
        Returns:
            DocumentTag (existing or newly created)
        """
        try:
            # Try to get existing tag
            existing_tag = await self.get_tag_by_name(tag_name)
            if existing_tag:
                return existing_tag
            
            # Create new tag
            request = DocumentTagCreateRequest(
                name=tag_name,
                color=color
            )
            return await self.create_tag(request)
            
        except Exception as e:
            logger.error(f"Error getting or creating tag '{tag_name}': {str(e)}")
            raise
    
    async def get_popular_tags(self, limit: int = 10) -> List[DocumentTag]:
        """
        Get the most popular tags.
        
        Args:
            limit: Maximum number of tags to return
            
        Returns:
            List of popular DocumentTag objects
        """
        try:
            # Get tags with usage count > 0
            used_tags = [t for t in self.tags.values() if t.usage_count > 0]
            
            # Sort by usage count (descending)
            used_tags.sort(key=lambda x: x.usage_count, reverse=True)
            
            return used_tags[:limit]
            
        except Exception as e:
            logger.error(f"Error getting popular tags: {str(e)}")
            raise
    
    async def search_tags(self, query: str, limit: int = 10) -> List[DocumentTag]:
        """
        Search for tags by name.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching DocumentTag objects
        """
        try:
            query_lower = query.lower().strip()
            matching_tags = []
            
            for tag in self.tags.values():
                if query_lower in tag.name:
                    matching_tags.append(tag)
            
            # Sort by usage count (descending) then by name
            matching_tags.sort(key=lambda x: (-x.usage_count, x.name))
            
            return matching_tags[:limit]
            
        except Exception as e:
            logger.error(f"Error searching tags: {str(e)}")
            raise
    
    async def get_tags_summary(self) -> Dict[str, Any]:
        """
        Get a summary of document tags.
        
        Returns:
            Summary statistics
        """
        try:
            total_tags = len(self.tags)
            used_tags = sum(1 for t in self.tags.values() if t.usage_count > 0)
            total_usage = sum(t.usage_count for t in self.tags.values())
            
            return {
                "total_tags": total_tags,
                "used_tags": used_tags,
                "unused_tags": total_tags - used_tags,
                "total_usage": total_usage,
                "average_usage": total_usage / used_tags if used_tags > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting tags summary: {str(e)}")
            raise 