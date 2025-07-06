import os
import uuid
import tempfile
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from fastapi import UploadFile
import asyncio

from app.models.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentStatus,
    FileType,
    DocumentChunk,
    DocumentMetadata,
    DocumentFilterRequest
)
from app.core.config import settings
from app.services.vector_service import VectorService
from app.services.document_group_service import DocumentGroupService
from app.services.document_tag_service import DocumentTagService
from app.utils.document_parser import DocumentParser
from app.utils.chunking import TextChunker

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document processing and management."""
    
    def __init__(self):
        self.vector_service = VectorService()
        self.document_parser = DocumentParser()
        self.text_chunker = TextChunker()
        self.group_service = DocumentGroupService()
        self.tag_service = DocumentTagService()
        
        # In-memory storage for MVP (replace with database in production)
        self.documents: Dict[str, DocumentResponse] = {}
        self.document_chunks: Dict[str, List[DocumentChunk]] = {}
        self.document_tags: Dict[str, List[str]] = {}  # document_id -> list of tag_ids
    
    async def process_document(
        self,
        document_id: str,
        file: UploadFile,
        knowledge_base_id: Optional[str] = None,
        group_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentResponse:
        """
        Process a document: parse, chunk, embed, and store.
        
        Args:
            document_id: Unique document identifier
            file: Uploaded file
            knowledge_base_id: Optional knowledge base ID
            group_id: Optional document group ID
            tags: Optional list of tags
            custom_metadata: Optional custom metadata
            
        Returns:
            DocumentResponse with processing status
        """
        try:
            # Validate group exists if specified
            if group_id:
                group = await self.group_service.get_group(group_id)
                if not group:
                    raise ValueError(f"Group {group_id} not found")
            
            # Process tags
            tag_ids = []
            if tags:
                for tag_name in tags:
                    tag = await self.tag_service.get_or_create_tag(tag_name)
                    tag_ids.append(tag.id)
                    await self.tag_service.increment_usage(tag.id)
            
            # Create initial document record
            document = DocumentResponse(
                id=document_id,
                filename=file.filename,
                file_type=FileType(file.filename.split('.')[-1].lower()),
                status=DocumentStatus.PENDING,
                size=file.size or 0,
                group_id=group_id,
                group_name=None,  # Will be set later
                tags=[tag.name for tag in [await self.tag_service.get_tag(tid) for tid in tag_ids] if tag],
                metadata=DocumentMetadata(
                    custom_fields=custom_metadata or {}
                ),
                created_at=datetime.utcnow()
            )
            
            # Set group name if group_id is provided
            if group_id:
                group = await self.group_service.get_group(group_id)
                if group:
                    document.group_name = group.name
            
            # Store document record
            self.documents[document_id] = document
            self.document_tags[document_id] = tag_ids
            
            # Update group document count
            if group_id:
                await self.group_service.increment_document_count(group_id)
            
            # Process document asynchronously
            asyncio.create_task(self._process_document_async(document_id, file))
            
            return document
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            # Update document status to failed
            if document_id in self.documents:
                self.documents[document_id].status = DocumentStatus.FAILED
                self.documents[document_id].updated_at = datetime.utcnow()
            raise
    
    async def _process_document_async(self, document_id: str, file: UploadFile):
        """
        Asynchronously process the document in the background.
        
        Args:
            document_id: Document ID
            file: Uploaded file
        """
        try:
            start_time = datetime.utcnow()
            
            # Update status to processing
            self.documents[document_id].status = DocumentStatus.PROCESSING
            self.documents[document_id].updated_at = datetime.utcnow()
            
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Parse document content
                logger.info(f"Parsing document {document_id}")
                parsed_content = await self.document_parser.parse_document(
                    temp_file_path,
                    self.documents[document_id].file_type
                )
                
                # Extract text and metadata
                text_content = parsed_content.get("text", "")
                extracted_metadata = parsed_content.get("metadata", {})
                
                # Update document metadata
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                enhanced_metadata = DocumentMetadata(
                    pages=extracted_metadata.get("pages"),
                    words=extracted_metadata.get("words"),
                    language=extracted_metadata.get("language"),
                    title=extracted_metadata.get("title"),
                    author=extracted_metadata.get("author"),
                    subject=extracted_metadata.get("subject"),
                    creator=extracted_metadata.get("creator"),
                    producer=extracted_metadata.get("producer"),
                    creation_date=extracted_metadata.get("creation_date"),
                    modification_date=extracted_metadata.get("modification_date"),
                    processing_time=processing_time,
                    custom_fields=self.documents[document_id].metadata.custom_fields
                )
                
                self.documents[document_id].metadata = enhanced_metadata
                
                # Chunk the text
                logger.info(f"Chunking document {document_id}")
                chunks = await self.text_chunker.chunk_text(
                    text_content,
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap,
                    document_id=document_id
                )
                
                # Store chunks
                self.document_chunks[document_id] = chunks
                
                # Generate embeddings and store in vector database
                logger.info(f"Generating embeddings for document {document_id}")
                await self.vector_service.store_document_chunks(
                    document_id=document_id,
                    chunks=chunks
                )
                
                # Update document status to completed
                self.documents[document_id].status = DocumentStatus.COMPLETED
                self.documents[document_id].chunks_count = len(chunks)
                self.documents[document_id].updated_at = datetime.utcnow()
                
                logger.info(f"Document {document_id} processed successfully with {len(chunks)} chunks")
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Error in async processing for document {document_id}: {str(e)}")
            # Update document status to failed
            self.documents[document_id].status = DocumentStatus.FAILED
            self.documents[document_id].updated_at = datetime.utcnow()
    
    async def get_document(self, document_id: str) -> Optional[DocumentResponse]:
        """
        Get a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            DocumentResponse if found, None otherwise
        """
        return self.documents.get(document_id)
    
    async def list_documents(
        self,
        page: int = 1,
        size: int = 10,
        filters: Optional[DocumentFilterRequest] = None
    ) -> DocumentListResponse:
        """
        List documents with advanced filtering and pagination.
        
        Args:
            page: Page number (1-based)
            size: Page size
            filters: Advanced filtering options
            
        Returns:
            DocumentListResponse with paginated results
        """
        try:
            # Start with all documents
            filtered_docs = list(self.documents.values())
            
            # Apply filters if provided
            if filters:
                filtered_docs = await self._apply_filters(filtered_docs, filters)
            
            # Sort documents
            sort_by = filters.sort_by if filters else "created_at"
            sort_order = filters.sort_order if filters else "desc"
            
            filtered_docs = self._sort_documents(filtered_docs, sort_by, sort_order)
            
            # Paginate
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_docs = filtered_docs[start_idx:end_idx]
            
            # Build available filters
            available_filters = await self._build_available_filters()
            
            # Build applied filters
            applied_filters = filters.dict(exclude_none=True) if filters else {}
            
            return DocumentListResponse(
                documents=paginated_docs,
                total=len(filtered_docs),
                page=page,
                size=size,
                applied_filters=applied_filters,
                available_filters=available_filters
            )
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            raise
    
    async def _apply_filters(
        self, 
        documents: List[DocumentResponse], 
        filters: DocumentFilterRequest
    ) -> List[DocumentResponse]:
        """
        Apply filters to document list.
        
        Args:
            documents: List of documents to filter
            filters: Filter criteria
            
        Returns:
            Filtered list of documents
        """
        filtered_docs = documents
        
        # Text search
        if filters.search_query:
            query_lower = filters.search_query.lower()
            filtered_docs = [
                doc for doc in filtered_docs
                if (query_lower in doc.filename.lower() or
                    query_lower in (doc.metadata.title or "").lower() or
                    query_lower in (doc.metadata.author or "").lower() or
                    any(query_lower in tag.lower() for tag in doc.tags))
            ]
        
        # Status filter
        if filters.status:
            filtered_docs = [doc for doc in filtered_docs if doc.status in filters.status]
        
        # File type filter
        if filters.file_type:
            filtered_docs = [doc for doc in filtered_docs if doc.file_type in filters.file_type]
        
        # Group filter
        if filters.group_id:
            filtered_docs = [doc for doc in filtered_docs if doc.group_id in filters.group_id]
        
        # Tag filter
        if filters.tags:
            filtered_docs = [
                doc for doc in filtered_docs 
                if any(tag in doc.tags for tag in filters.tags)
            ]
        
        # Date filters
        if filters.created_after:
            filtered_docs = [doc for doc in filtered_docs if doc.created_at >= filters.created_after]
        
        if filters.created_before:
            filtered_docs = [doc for doc in filtered_docs if doc.created_at <= filters.created_before]
        
        if filters.updated_after:
            filtered_docs = [doc for doc in filtered_docs if doc.updated_at and doc.updated_at >= filters.updated_after]
        
        if filters.updated_before:
            filtered_docs = [doc for doc in filtered_docs if doc.updated_at and doc.updated_at <= filters.updated_before]
        
        # Size filters
        if filters.min_size is not None:
            filtered_docs = [doc for doc in filtered_docs if doc.size >= filters.min_size]
        
        if filters.max_size is not None:
            filtered_docs = [doc for doc in filtered_docs if doc.size <= filters.max_size]
        
        # Metadata filters
        if filters.min_pages is not None:
            filtered_docs = [doc for doc in filtered_docs if doc.metadata.pages and doc.metadata.pages >= filters.min_pages]
        
        if filters.max_pages is not None:
            filtered_docs = [doc for doc in filtered_docs if doc.metadata.pages and doc.metadata.pages <= filters.max_pages]
        
        if filters.language:
            filtered_docs = [doc for doc in filtered_docs if doc.metadata.language in filters.language]
        
        if filters.author:
            filtered_docs = [doc for doc in filtered_docs if doc.metadata.author in filters.author]
        
        # Custom metadata filters
        if filters.custom_filters:
            for key, value in filters.custom_filters.items():
                filtered_docs = [
                    doc for doc in filtered_docs 
                    if doc.metadata.custom_fields.get(key) == value
                ]
        
        return filtered_docs
    
    def _sort_documents(
        self, 
        documents: List[DocumentResponse], 
        sort_by: str, 
        sort_order: str
    ) -> List[DocumentResponse]:
        """
        Sort documents by specified criteria.
        
        Args:
            documents: List of documents to sort
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            Sorted list of documents
        """
        reverse = sort_order.lower() == "desc"
        
        if sort_by == "created_at":
            documents.sort(key=lambda x: x.created_at, reverse=reverse)
        elif sort_by == "updated_at":
            documents.sort(key=lambda x: x.updated_at or x.created_at, reverse=reverse)
        elif sort_by == "filename":
            documents.sort(key=lambda x: x.filename.lower(), reverse=reverse)
        elif sort_by == "size":
            documents.sort(key=lambda x: x.size, reverse=reverse)
        elif sort_by == "pages":
            documents.sort(key=lambda x: x.metadata.pages or 0, reverse=reverse)
        elif sort_by == "status":
            documents.sort(key=lambda x: x.status.value, reverse=reverse)
        
        return documents
    
    async def _build_available_filters(self) -> Dict[str, Any]:
        """
        Build available filter options based on existing documents.
        
        Returns:
            Dictionary of available filter options
        """
        try:
            # Get all unique values for filtering
            file_types = list(set(doc.file_type for doc in self.documents.values()))
            statuses = list(set(doc.status for doc in self.documents.values()))
            languages = list(set(doc.metadata.language for doc in self.documents.values() if doc.metadata.language))
            authors = list(set(doc.metadata.author for doc in self.documents.values() if doc.metadata.author))
            
            # Get groups and tags from services
            groups_response = await self.group_service.list_groups(include_empty=False)
            tags_response = await self.tag_service.list_tags(include_unused=False)
            
            return {
                "file_types": file_types,
                "statuses": statuses,
                "groups": [{"id": g.id, "name": g.name, "color": g.color} for g in groups_response.groups],
                "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in tags_response.tags],
                "languages": languages,
                "authors": authors,
                "date_range": {
                    "earliest": min(doc.created_at for doc in self.documents.values()) if self.documents else None,
                    "latest": max(doc.created_at for doc in self.documents.values()) if self.documents else None
                },
                "size_range": {
                    "min": min(doc.size for doc in self.documents.values()) if self.documents else None,
                    "max": max(doc.size for doc in self.documents.values()) if self.documents else None
                }
            }
        except Exception as e:
            logger.error(f"Error building available filters: {str(e)}")
            return {}
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its associated data.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            document = self.documents.get(document_id)
            if not document:
                return False
            
            # Update group document count
            if document.group_id:
                await self.group_service.decrement_document_count(document.group_id)
            
            # Update tag usage counts
            if document_id in self.document_tags:
                for tag_id in self.document_tags[document_id]:
                    await self.tag_service.decrement_usage(tag_id)
                del self.document_tags[document_id]
            
            # Remove from vector database
            await self.vector_service.delete_document(document_id)
            
            # Remove from local storage
            if document_id in self.documents:
                del self.documents[document_id]
            
            if document_id in self.document_chunks:
                del self.document_chunks[document_id]
            
            logger.info(f"Document {document_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            raise
    
    async def update_document_tags(self, document_id: str, tags: List[str]) -> DocumentResponse:
        """
        Update document tags.
        
        Args:
            document_id: Document ID
            tags: New list of tags
            
        Returns:
            Updated DocumentResponse
        """
        try:
            document = self.documents.get(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Remove old tags
            old_tag_ids = self.document_tags.get(document_id, [])
            for tag_id in old_tag_ids:
                await self.tag_service.decrement_usage(tag_id)
            
            # Add new tags
            new_tag_ids = []
            for tag_name in tags:
                tag = await self.tag_service.get_or_create_tag(tag_name)
                new_tag_ids.append(tag.id)
                await self.tag_service.increment_usage(tag.id)
            
            # Update document
            document.tags = tags
            document.updated_at = datetime.utcnow()
            self.document_tags[document_id] = new_tag_ids
            
            return document
            
        except Exception as e:
            logger.error(f"Error updating document tags {document_id}: {str(e)}")
            raise
    
    async def update_document_group(self, document_id: str, group_id: Optional[str]) -> DocumentResponse:
        """
        Update document group.
        
        Args:
            document_id: Document ID
            group_id: New group ID (None to remove from group)
            
        Returns:
            Updated DocumentResponse
        """
        try:
            document = self.documents.get(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Validate new group exists if specified
            if group_id:
                group = await self.group_service.get_group(group_id)
                if not group:
                    raise ValueError(f"Group {group_id} not found")
            
            # Update old group count
            if document.group_id:
                await self.group_service.decrement_document_count(document.group_id)
            
            # Update new group count
            if group_id:
                await self.group_service.increment_document_count(group_id)
                group = await self.group_service.get_group(group_id)
                document.group_name = group.name if group else None
            else:
                document.group_name = None
            
            # Update document
            document.group_id = group_id
            document.updated_at = datetime.utcnow()
            
            return document
            
        except Exception as e:
            logger.error(f"Error updating document group {document_id}: {str(e)}")
            raise
    
    async def reprocess_document(self, document_id: str) -> DocumentResponse:
        """
        Reprocess an existing document.
        
        Args:
            document_id: Document ID to reprocess
            
        Returns:
            Updated DocumentResponse
        """
        try:
            document = self.documents.get(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Reset status and clear existing chunks
            document.status = DocumentStatus.PENDING
            document.chunks_count = None
            document.updated_at = datetime.utcnow()
            
            # Clear existing chunks from vector database
            await self.vector_service.delete_document(document_id)
            
            # Clear local chunks
            if document_id in self.document_chunks:
                del self.document_chunks[document_id]
            
            # Note: This is a simplified reprocessing - in a real implementation,
            # you'd need to re-access the original file
            logger.info(f"Document {document_id} queued for reprocessing")
            
            return document
            
        except Exception as e:
            logger.error(f"Error reprocessing document {document_id}: {str(e)}")
            raise
    
    async def get_document_chunks(self, document_id: str) -> List[DocumentChunk]:
        """
        Get all chunks for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of DocumentChunk objects
        """
        return self.document_chunks.get(document_id, [])
    
    async def search_documents(
        self,
        query: str,
        knowledge_base_id: Optional[str] = None,
        limit: int = 10
    ) -> List[DocumentChunk]:
        """
        Search for relevant document chunks.
        
        Args:
            query: Search query
            knowledge_base_id: Optional knowledge base filter
            limit: Maximum number of results
            
        Returns:
            List of relevant DocumentChunk objects
        """
        try:
            # Use vector service to search
            results = await self.vector_service.search_similar_chunks(
                query=query,
                knowledge_base_id=knowledge_base_id,
                limit=limit
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise 