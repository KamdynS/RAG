import os
import asyncio
from typing import List, Dict, Any, Optional
import logging
import numpy as np
from datetime import datetime

# OpenAI for embeddings
from openai import AsyncOpenAI

# Pinecone for vector storage
try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger.warning("Pinecone not installed. Using in-memory vector storage.")

from app.models.document import DocumentChunk
from app.models.chat import SourceCitation
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    """Service for vector embeddings and similarity search."""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.pinecone_client = None
        self.pinecone_index = None
        
        # In-memory storage for MVP when Pinecone is not available
        self.in_memory_vectors: Dict[str, Dict[str, Any]] = {}
        
        # Initialize Pinecone if available
        if PINECONE_AVAILABLE:
            self._initialize_pinecone()
        else:
            logger.warning("Using in-memory vector storage. For production, install Pinecone.")
    
    def _initialize_pinecone(self):
        """Initialize Pinecone client and index."""
        try:
            # Initialize Pinecone client
            self.pinecone_client = Pinecone(
                api_key=settings.pinecone_api_key,
                environment=settings.pinecone_environment
            )
            
            # Check if index exists, create if not
            existing_indexes = self.pinecone_client.list_indexes()
            index_names = [index.name for index in existing_indexes]
            
            if settings.pinecone_index_name not in index_names:
                logger.info(f"Creating Pinecone index: {settings.pinecone_index_name}")
                self.pinecone_client.create_index(
                    name=settings.pinecone_index_name,
                    dimension=1536,  # OpenAI text-embedding-3-small dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
            
            # Connect to index
            self.pinecone_index = self.pinecone_client.Index(settings.pinecone_index_name)
            logger.info(f"Connected to Pinecone index: {settings.pinecone_index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {str(e)}")
            logger.warning("Falling back to in-memory vector storage")
            self.pinecone_client = None
            self.pinecone_index = None
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        try:
            response = await self.openai_client.embeddings.create(
                model=settings.openai_embedding_model,
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    async def store_document_chunks(
        self,
        document_id: str,
        chunks: List[DocumentChunk]
    ) -> bool:
        """
        Store document chunks with embeddings in vector database.
        
        Args:
            document_id: Document ID
            chunks: List of DocumentChunk objects
            
        Returns:
            True if successful
        """
        try:
            # Generate embeddings for all chunks
            embeddings = []
            for chunk in chunks:
                embedding = await self.generate_embedding(chunk.content)
                embeddings.append(embedding)
                
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.1)
            
            # Store in vector database
            if self.pinecone_index:
                await self._store_in_pinecone(document_id, chunks, embeddings)
            else:
                await self._store_in_memory(document_id, chunks, embeddings)
            
            logger.info(f"Stored {len(chunks)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing document chunks: {str(e)}")
            raise
    
    async def _store_in_pinecone(
        self,
        document_id: str,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ):
        """Store chunks in Pinecone vector database."""
        vectors = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector = {
                "id": chunk.id,
                "values": embedding,
                "metadata": {
                    "document_id": document_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "created_at": datetime.utcnow().isoformat(),
                    **chunk.metadata
                }
            }
            vectors.append(vector)
        
        # Upsert vectors in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.pinecone_index.upsert(vectors=batch)
            
            # Small delay between batches
            await asyncio.sleep(0.5)
    
    async def _store_in_memory(
        self,
        document_id: str,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ):
        """Store chunks in memory for MVP."""
        for chunk, embedding in zip(chunks, embeddings):
            self.in_memory_vectors[chunk.id] = {
                "id": chunk.id,
                "values": embedding,
                "metadata": {
                    "document_id": document_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "created_at": datetime.utcnow().isoformat(),
                    **chunk.metadata
                }
            }
    
    async def search_similar_chunks(
        self,
        query: str,
        knowledge_base_id: Optional[str] = None,
        limit: int = 10
    ) -> List[DocumentChunk]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query: Search query
            knowledge_base_id: Optional knowledge base filter
            limit: Maximum number of results
            
        Returns:
            List of relevant DocumentChunk objects with similarity scores
        """
        try:
            # Generate embedding for query
            query_embedding = await self.generate_embedding(query)
            
            # Search in vector database
            if self.pinecone_index:
                results = await self._search_in_pinecone(
                    query_embedding,
                    knowledge_base_id,
                    limit
                )
            else:
                results = await self._search_in_memory(
                    query_embedding,
                    knowledge_base_id,
                    limit
                )
            
            # Convert results to DocumentChunk objects
            chunks = []
            for result in results:
                metadata = result.get("metadata", {})
                chunk = DocumentChunk(
                    id=result["id"],
                    content=metadata.get("content", ""),
                    chunk_index=metadata.get("chunk_index", 0),
                    metadata={
                        **metadata,
                        "similarity_score": result.get("score", 0.0)
                    }
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            raise
    
    async def _search_in_pinecone(
        self,
        query_embedding: List[float],
        knowledge_base_id: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search in Pinecone vector database."""
        filter_dict = {}
        if knowledge_base_id:
            filter_dict["knowledge_base_id"] = knowledge_base_id
        
        response = self.pinecone_index.query(
            vector=query_embedding,
            top_k=limit,
            include_metadata=True,
            filter=filter_dict if filter_dict else None
        )
        
        results = []
        for match in response["matches"]:
            results.append({
                "id": match["id"],
                "score": match["score"],
                "metadata": match["metadata"]
            })
        
        return results
    
    async def _search_in_memory(
        self,
        query_embedding: List[float],
        knowledge_base_id: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search in memory using cosine similarity."""
        results = []
        
        for vector_id, vector_data in self.in_memory_vectors.items():
            metadata = vector_data["metadata"]
            
            # Apply knowledge base filter
            if knowledge_base_id and metadata.get("knowledge_base_id") != knowledge_base_id:
                continue
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, vector_data["values"])
            
            results.append({
                "id": vector_id,
                "score": similarity,
                "metadata": metadata
            })
        
        # Sort by similarity score (descending) and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks for a document from vector database.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if successful
        """
        try:
            if self.pinecone_index:
                # Delete from Pinecone using metadata filter
                self.pinecone_index.delete(
                    filter={"document_id": document_id}
                )
            else:
                # Delete from memory
                to_delete = []
                for vector_id, vector_data in self.in_memory_vectors.items():
                    if vector_data["metadata"].get("document_id") == document_id:
                        to_delete.append(vector_id)
                
                for vector_id in to_delete:
                    del self.in_memory_vectors[vector_id]
            
            logger.info(f"Deleted vectors for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document vectors: {str(e)}")
            raise
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector index.
        
        Returns:
            Dictionary with index statistics
        """
        try:
            if self.pinecone_index:
                stats = self.pinecone_index.describe_index_stats()
                return {
                    "total_vectors": stats.get("total_vector_count", 0),
                    "dimension": stats.get("dimension", 0),
                    "index_fullness": stats.get("index_fullness", 0.0)
                }
            else:
                return {
                    "total_vectors": len(self.in_memory_vectors),
                    "dimension": 1536,
                    "index_fullness": 0.0
                }
                
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            return {
                "total_vectors": 0,
                "dimension": 0,
                "index_fullness": 0.0
            } 