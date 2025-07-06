import os
import asyncio
from typing import List, Dict, Any, Optional
import logging
import numpy as np
from datetime import datetime
import uuid

# OpenAI for embeddings
from openai import AsyncOpenAI

# ChromaDB for vector storage (default)
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logging.warning("ChromaDB not installed. Falling back to alternative vector storage.")

# Pinecone for vector storage (optional)
try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

from app.models.document import DocumentChunk
from app.models.chat import SourceCitation
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    """Service for vector embeddings and similarity search."""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.vector_db_type = settings.vector_db_type.lower()
        
        # ChromaDB client and collection
        self.chroma_client = None
        self.chroma_collection = None
        
        # Pinecone client and index
        self.pinecone_client = None
        self.pinecone_index = None
        
        # In-memory storage as last resort
        self.in_memory_vectors: Dict[str, Dict[str, Any]] = {}
        
        # Initialize the appropriate vector database
        self._initialize_vector_db()
    
    def _initialize_vector_db(self):
        """Initialize the appropriate vector database based on configuration."""
        if self.vector_db_type == "chroma" and CHROMA_AVAILABLE:
            self._initialize_chroma()
        elif self.vector_db_type == "pinecone" and PINECONE_AVAILABLE:
            self._initialize_pinecone()
        else:
            logger.warning(f"Vector DB type '{self.vector_db_type}' not available. Using in-memory storage.")
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Connect to ChromaDB
            self.chroma_client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                settings=ChromaSettings(
                    chroma_client_auth_provider="chromadb.auth.token.TokenAuthClientProvider",
                    chroma_client_auth_credentials="test-token"
                ) if settings.chroma_host != "localhost" else ChromaSettings()
            )
            
            # Get or create collection
            try:
                self.chroma_collection = self.chroma_client.get_collection(
                    name=settings.chroma_collection_name
                )
                logger.info(f"Connected to existing ChromaDB collection: {settings.chroma_collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                self.chroma_collection = self.chroma_client.create_collection(
                    name=settings.chroma_collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created new ChromaDB collection: {settings.chroma_collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            logger.warning("Falling back to in-memory vector storage")
            self.chroma_client = None
            self.chroma_collection = None
    
    def _initialize_pinecone(self):
        """Initialize Pinecone client and index."""
        try:
            if not settings.pinecone_api_key or not settings.pinecone_environment:
                raise ValueError("Pinecone API key and environment are required")
            
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
            
            # Store in appropriate vector database
            if self.chroma_collection:
                await self._store_in_chroma(document_id, chunks, embeddings)
            elif self.pinecone_index:
                await self._store_in_pinecone(document_id, chunks, embeddings)
            else:
                await self._store_in_memory(document_id, chunks, embeddings)
            
            logger.info(f"Stored {len(chunks)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing document chunks: {str(e)}")
            raise
    
    async def _store_in_chroma(
        self,
        document_id: str,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ):
        """Store chunks in ChromaDB."""
        try:
            ids = []
            documents = []
            metadatas = []
            embeddings_list = []
            
            for chunk, embedding in zip(chunks, embeddings):
                chunk_id = chunk.id or str(uuid.uuid4())
                
                ids.append(chunk_id)
                documents.append(chunk.content)
                embeddings_list.append(embedding)
                metadatas.append({
                    "document_id": document_id,
                    "chunk_index": chunk.chunk_index if hasattr(chunk, 'chunk_index') else 0,
                    "created_at": datetime.utcnow().isoformat(),
                    **chunk.metadata
                })
            
            # Add to ChromaDB collection
            self.chroma_collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings_list,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully stored {len(chunks)} chunks in ChromaDB")
            
        except Exception as e:
            logger.error(f"Error storing chunks in ChromaDB: {str(e)}")
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
                "id": chunk.id or str(uuid.uuid4()),
                "values": embedding,
                "metadata": {
                    "document_id": document_id,
                    "chunk_index": getattr(chunk, 'chunk_index', i),
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
        """Store chunks in memory as fallback."""
        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = chunk.id or str(uuid.uuid4())
            self.in_memory_vectors[chunk_id] = {
                "id": chunk_id,
                "values": embedding,
                "metadata": {
                    "document_id": document_id,
                    "chunk_index": getattr(chunk, 'chunk_index', 0),
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
            List of similar DocumentChunk objects
        """
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Search in appropriate vector database
            if self.chroma_collection:
                results = await self._search_in_chroma(query_embedding, knowledge_base_id, limit)
            elif self.pinecone_index:
                results = await self._search_in_pinecone(query_embedding, knowledge_base_id, limit)
            else:
                results = await self._search_in_memory(query_embedding, knowledge_base_id, limit)
            
            # Convert results to DocumentChunk objects
            chunks = []
            for result in results:
                chunk = DocumentChunk(
                    id=result["id"],
                    content=result["metadata"]["content"],
                    metadata=result["metadata"]
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            raise
    
    async def _search_in_chroma(
        self,
        query_embedding: List[float],
        knowledge_base_id: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in ChromaDB."""
        try:
            where_filter = {}
            if knowledge_base_id:
                where_filter["document_id"] = knowledge_base_id
            
            results = self.chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert ChromaDB results to standard format
            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i, chunk_id in enumerate(results["ids"][0]):
                    formatted_results.append({
                        "id": chunk_id,
                        "score": 1 - results["distances"][0][i],  # Convert distance to similarity
                        "metadata": {
                            **results["metadatas"][0][i],
                            "content": results["documents"][0][i]
                        }
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching in ChromaDB: {str(e)}")
            return []
    
    async def _search_in_pinecone(
        self,
        query_embedding: List[float],
        knowledge_base_id: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in Pinecone."""
        try:
            filter_dict = {}
            if knowledge_base_id:
                filter_dict["document_id"] = knowledge_base_id
            
            results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=limit,
                filter=filter_dict if filter_dict else None,
                include_metadata=True
            )
            
            formatted_results = []
            for match in results["matches"]:
                formatted_results.append({
                    "id": match["id"],
                    "score": match["score"],
                    "metadata": match["metadata"]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching in Pinecone: {str(e)}")
            return []
    
    async def _search_in_memory(
        self,
        query_embedding: List[float],
        knowledge_base_id: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in memory."""
        results = []
        
        for vector_id, vector_data in self.in_memory_vectors.items():
            if knowledge_base_id and vector_data["metadata"].get("document_id") != knowledge_base_id:
                continue
            
            similarity = self._cosine_similarity(query_embedding, vector_data["values"])
            results.append({
                "id": vector_id,
                "score": similarity,
                "metadata": vector_data["metadata"]
            })
        
        # Sort by similarity and return top results
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
            return 0
        
        return dot_product / (norm1 * norm2)
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks for a document from vector database.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if successful
        """
        try:
            if self.chroma_collection:
                # Delete from ChromaDB
                results = self.chroma_collection.get(
                    where={"document_id": document_id}
                )
                if results["ids"]:
                    self.chroma_collection.delete(ids=results["ids"])
                    
            elif self.pinecone_index:
                # Delete from Pinecone (requires fetching IDs first)
                query_results = self.pinecone_index.query(
                    vector=[0] * 1536,  # Dummy vector
                    filter={"document_id": document_id},
                    top_k=10000,  # Large number to get all
                    include_metadata=False
                )
                
                chunk_ids = [match["id"] for match in query_results["matches"]]
                if chunk_ids:
                    self.pinecone_index.delete(ids=chunk_ids)
                    
            else:
                # Delete from memory
                to_delete = [
                    vector_id for vector_id, vector_data in self.in_memory_vectors.items()
                    if vector_data["metadata"].get("document_id") == document_id
                ]
                for vector_id in to_delete:
                    del self.in_memory_vectors[vector_id]
            
            logger.info(f"Deleted document {document_id} from vector database")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Returns:
            Dictionary with index statistics
        """
        try:
            if self.chroma_collection:
                count = self.chroma_collection.count()
                return {
                    "type": "chromadb",
                    "total_vectors": count,
                    "collection_name": settings.chroma_collection_name
                }
                
            elif self.pinecone_index:
                stats = self.pinecone_index.describe_index_stats()
                return {
                    "type": "pinecone",
                    "total_vectors": stats.get("total_vector_count", 0),
                    "index_name": settings.pinecone_index_name
                }
                
            else:
                return {
                    "type": "memory",
                    "total_vectors": len(self.in_memory_vectors)
                }
                
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            return {"type": "unknown", "total_vectors": 0} 