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
    DocumentChunk
)
from app.core.config import settings
from app.services.vector_service import VectorService
from app.utils.document_parser import DocumentParser
from app.utils.chunking import TextChunker

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document processing and management."""
    
    def __init__(self):
        self.vector_service = VectorService()
        self.document_parser = DocumentParser()
        self.text_chunker = TextChunker()
        
        # In-memory storage for MVP (replace with database in production)
        self.documents: Dict[str, DocumentResponse] = {}
        self.document_chunks: Dict[str, List[DocumentChunk]] = {}
    
    async def process_document(
        self,
        document_id: str,
        file: UploadFile,
        knowledge_base_id: Optional[str] = None
    ) -> DocumentResponse:
        """
        Process a document: parse, chunk, embed, and store.
        
        Args:
            document_id: Unique document identifier
            file: Uploaded file
            knowledge_base_id: Optional knowledge base ID
            
        Returns:
            DocumentResponse with processing status
        """
        try:
            # Create initial document record
            document = DocumentResponse(
                id=document_id,
                filename=file.filename,
                file_type=FileType(file.filename.split('.')[-1].lower()),
                status=DocumentStatus.PENDING,
                size=file.size or 0,
                metadata={"knowledge_base_id": knowledge_base_id} if knowledge_base_id else {},
                created_at=datetime.utcnow()
            )
            
            # Store document record
            self.documents[document_id] = document
            
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
                metadata = parsed_content.get("metadata", {})
                
                # Update document metadata
                self.documents[document_id].metadata.update(metadata)
                
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
        status: Optional[DocumentStatus] = None,
        knowledge_base_id: Optional[str] = None
    ) -> DocumentListResponse:
        """
        List documents with optional filtering and pagination.
        
        Args:
            page: Page number (1-based)
            size: Page size
            status: Optional status filter
            knowledge_base_id: Optional knowledge base filter
            
        Returns:
            DocumentListResponse with paginated results
        """
        try:
            # Filter documents
            filtered_docs = []
            for doc in self.documents.values():
                if status and doc.status != status:
                    continue
                if knowledge_base_id and doc.metadata.get("knowledge_base_id") != knowledge_base_id:
                    continue
                filtered_docs.append(doc)
            
            # Sort by creation date (newest first)
            filtered_docs.sort(key=lambda x: x.created_at, reverse=True)
            
            # Paginate
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_docs = filtered_docs[start_idx:end_idx]
            
            return DocumentListResponse(
                documents=paginated_docs,
                total=len(filtered_docs),
                page=page,
                size=size
            )
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its associated data.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if deleted successfully
        """
        try:
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