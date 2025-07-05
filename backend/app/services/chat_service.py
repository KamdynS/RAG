import uuid
import asyncio
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
from datetime import datetime

# OpenAI for chat completion
from openai import AsyncOpenAI

from app.models.chat import (
    ChatResponse,
    ConversationHistory,
    ConversationListResponse,
    ChatMessage,
    MessageRole,
    SourceCitation,
    AnnotatedText,
    BlockQuote
)
from app.models.document import DocumentChunk
from app.core.config import settings
from app.services.document_service import DocumentService
from app.utils.citation_parser import CitationParser

logger = logging.getLogger(__name__)


class ChatService:
    """Service for chat completion and conversation management."""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.document_service = DocumentService()
        self.citation_parser = CitationParser()
        
        # In-memory storage for MVP (replace with database in production)
        self.conversations: Dict[str, ConversationHistory] = {}
        self.feedback_data: Dict[str, List[Dict[str, Any]]] = {}
    
    async def generate_response(
        self,
        message: str,
        conversation_id: str,
        knowledge_base_id: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        include_sources: bool = True,
        use_annotations: bool = True
    ) -> ChatResponse:
        """
        Generate a chat response using RAG.
        
        Args:
            message: User message
            conversation_id: Conversation ID
            knowledge_base_id: Optional knowledge base filter
            max_tokens: Maximum tokens in response
            temperature: Response temperature
            include_sources: Whether to include source citations
            
        Returns:
            ChatResponse with generated response and sources
        """
        start_time = datetime.utcnow()
        
        try:
            # Get or create conversation
            conversation = self.conversations.get(conversation_id)
            if not conversation:
                conversation = ConversationHistory(
                    conversation_id=conversation_id,
                    messages=[],
                    created_at=start_time,
                    updated_at=start_time
                )
                self.conversations[conversation_id] = conversation
            
            # Add user message to conversation
            user_message = ChatMessage(
                role=MessageRole.USER,
                content=message,
                timestamp=start_time
            )
            conversation.messages.append(user_message)
            
            # Search for relevant document chunks
            relevant_chunks = await self.document_service.search_documents(
                query=message,
                knowledge_base_id=knowledge_base_id,
                limit=5
            )
            
            # Build context from relevant chunks
            context = self._build_context(relevant_chunks)
            
            # Generate response using OpenAI
            response_content = await self._generate_openai_response(
                message=message,
                context=context,
                conversation_history=conversation.messages[:-1],  # Exclude current user message
                max_tokens=max_tokens,
                temperature=temperature,
                use_annotations=use_annotations
            )
            
            # Add assistant message to conversation
            assistant_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=response_content,
                timestamp=datetime.utcnow()
            )
            conversation.messages.append(assistant_message)
            conversation.updated_at = datetime.utcnow()
            
            # Build source citations if requested
            sources = []
            if include_sources and relevant_chunks:
                sources = self._build_source_citations(relevant_chunks)
            
            # Process annotations and citations if requested
            annotated_response = None
            block_quotes = []
            has_annotations = False
            
            if use_annotations and relevant_chunks:
                annotated_response = self.citation_parser.parse_response(
                    response_content, 
                    relevant_chunks
                )
                block_quotes = self.citation_parser.extract_block_quotes(
                    response_content, 
                    relevant_chunks
                )
                has_annotations = len(annotated_response.annotations) > 0
                
                # Update sources with citation information
                sources = self._build_enhanced_source_citations(
                    relevant_chunks, 
                    annotated_response.annotations
                )
            
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ChatResponse(
                response=response_content,
                annotated_response=annotated_response,
                conversation_id=conversation_id,
                sources=sources,
                block_quotes=block_quotes,
                tokens_used=len(response_content.split()),  # Rough estimate
                response_time=response_time,
                has_annotations=has_annotations,
                citation_style="numbered"
            )
            
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            raise
    
    def _build_context(self, chunks: List[DocumentChunk]) -> str:
        """Build context string from relevant chunks with citation numbers."""
        if not chunks:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            # Add citation number and document info
            document_id = chunk.metadata.get('document_id', 'Unknown')
            document_name = chunk.metadata.get('document_name', f'Document_{document_id}')
            page_number = chunk.metadata.get('page_number', 'Unknown')
            
            context_parts.append(f"[{i}] Document: {document_name} (ID: {document_id}, Page: {page_number})")
            context_parts.append(f"Content: {chunk.content}")
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def _build_source_citations(self, chunks: List[DocumentChunk]) -> List[SourceCitation]:
        """Build source citations from relevant chunks."""
        citations = []
        
        for chunk in chunks:
            # Get document info (in a real implementation, this would come from the database)
            document_id = chunk.metadata.get("document_id", "unknown")
            similarity_score = chunk.metadata.get("similarity_score", 0.0)
            
            citation = SourceCitation(
                document_id=document_id,
                document_name=f"Document_{document_id}",  # Placeholder
                chunk_id=chunk.id,
                content=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                relevance_score=similarity_score,
                page_number=chunk.metadata.get("page_number")
            )
            citations.append(citation)
        
        return citations
    
    def _build_enhanced_source_citations(
        self, 
        chunks: List[DocumentChunk], 
        annotations: List
    ) -> List[SourceCitation]:
        """Build enhanced source citations with annotation information."""
        citations = []
        
        # Create citation count mapping
        citation_counts = {}
        annotation_mappings = {}
        
        for annotation in annotations:
            citation_num = annotation.citation_number
            if citation_num not in citation_counts:
                citation_counts[citation_num] = 0
                annotation_mappings[citation_num] = []
            
            citation_counts[citation_num] += 1
            annotation_mappings[citation_num].append(annotation.id)
        
        for i, chunk in enumerate(chunks, 1):
            # Get document info
            document_id = chunk.metadata.get("document_id", "unknown")
            document_name = chunk.metadata.get("document_name", f"Document_{document_id}")
            similarity_score = chunk.metadata.get("similarity_score", 0.0)
            
            citation = SourceCitation(
                document_id=document_id,
                document_name=document_name,
                chunk_id=chunk.id,
                content=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                relevance_score=similarity_score,
                page_number=chunk.metadata.get("page_number"),
                section=chunk.metadata.get("section"),
                citation_count=citation_counts.get(i, 0),
                used_in_annotations=annotation_mappings.get(i, [])
            )
            citations.append(citation)
        
        return citations
    
    async def _generate_openai_response(
        self,
        message: str,
        context: str,
        conversation_history: List[ChatMessage],
        max_tokens: int,
        temperature: float,
        use_annotations: bool = True
    ) -> str:
        """Generate response using OpenAI."""
        try:
            # Build messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt(context, use_annotations)
                }
            ]
            
            # Add conversation history
            for msg in conversation_history[-6:]:  # Keep last 6 messages for context
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Generate response
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise
    
    def _get_system_prompt(self, context: str, use_citations: bool = True) -> str:
        """Get system prompt with context and citation instructions."""
        base_prompt = """You are a helpful AI assistant that answers questions based on the provided context from uploaded documents. 

Instructions:
1. Use the context provided to answer questions accurately
2. If the context doesn't contain relevant information, say so clearly
3. Provide specific, detailed answers when possible
4. If you're unsure about something, express uncertainty
5. Be concise but comprehensive in your responses"""

        if use_citations:
            citation_prompt = """
6. CITATION REQUIREMENTS:
   - Use numbered citations [1], [2], [3], etc. for ALL information from the provided context
   - Place citations immediately after the relevant information, not at the end of sentences
   - Every fact, quote, or piece of information from the context MUST be cited
   - Use block quotes for direct excerpts: > "exact text from document" [1]
   - For paraphrased information, still include the citation number
   - Multiple citations for the same source should use the same number
   - If referencing multiple sources for one point, use [1,2] or [1][2]

Citation Examples:
- Revenue increased by 15% [1] in the last quarter.
- The study found that > "customer satisfaction improved significantly" [2] after the implementation.
- Market analysis shows strong growth [1] and competitive positioning [3].
- According to the research [2], three key factors were identified.

Context from documents:
"""
        else:
            citation_prompt = """

Context from documents:
"""
        
        if context:
            return base_prompt + citation_prompt + f"\n{context}"
        else:
            return base_prompt + citation_prompt + "\nNo relevant context found in the documents."
    
    async def generate_streaming_response(
        self,
        message: str,
        conversation_id: str,
        knowledge_base_id: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        include_sources: bool = True,
        use_annotations: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming chat response.
        
        Args:
            message: User message
            conversation_id: Conversation ID
            knowledge_base_id: Optional knowledge base filter
            max_tokens: Maximum tokens in response
            temperature: Response temperature
            include_sources: Whether to include source citations
            
        Yields:
            Streaming response chunks
        """
        try:
            # This is a simplified streaming implementation
            # In a real implementation, you'd use OpenAI's streaming API
            
            response = await self.generate_response(
                message=message,
                conversation_id=conversation_id,
                knowledge_base_id=knowledge_base_id,
                max_tokens=max_tokens,
                temperature=temperature,
                include_sources=include_sources,
                use_annotations=use_annotations
            )
            
            # Simulate streaming by yielding chunks
            words = response.response.split()
            for i, word in enumerate(words):
                chunk_data = {
                    "type": "content",
                    "content": word + " "
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
                await asyncio.sleep(0.05)  # Small delay to simulate streaming
            
            # Send sources at the end
            if response.sources:
                sources_data = {
                    "type": "sources",
                    "sources": [source.model_dump() for source in response.sources]
                }
                yield f"data: {json.dumps(sources_data)}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            error_data = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Get conversation by ID."""
        return self.conversations.get(conversation_id)
    
    async def list_conversations(
        self,
        page: int = 1,
        size: int = 10
    ) -> ConversationListResponse:
        """List conversations with pagination."""
        try:
            # Sort conversations by update time (newest first)
            sorted_conversations = sorted(
                self.conversations.values(),
                key=lambda x: x.updated_at,
                reverse=True
            )
            
            # Paginate
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_conversations = sorted_conversations[start_idx:end_idx]
            
            return ConversationListResponse(
                conversations=paginated_conversations,
                total=len(sorted_conversations),
                page=page,
                size=size
            )
            
        except Exception as e:
            logger.error(f"Error listing conversations: {str(e)}")
            raise
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        try:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
            
            # Also delete feedback data
            if conversation_id in self.feedback_data:
                del self.feedback_data[conversation_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            raise
    
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear messages from a conversation."""
        try:
            conversation = self.conversations.get(conversation_id)
            if conversation:
                conversation.messages = []
                conversation.updated_at = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing conversation: {str(e)}")
            raise
    
    async def export_conversation(self, conversation_id: str, format: str) -> str:
        """Export conversation in specified format."""
        try:
            conversation = self.conversations.get(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            if format == "json":
                return json.dumps(conversation.model_dump(), indent=2)
            elif format == "txt":
                return self._export_as_text(conversation)
            elif format == "md":
                return self._export_as_markdown(conversation)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting conversation: {str(e)}")
            raise
    
    def _export_as_text(self, conversation: ConversationHistory) -> str:
        """Export conversation as plain text."""
        lines = [f"Conversation: {conversation.conversation_id}"]
        lines.append(f"Created: {conversation.created_at}")
        lines.append(f"Updated: {conversation.updated_at}")
        lines.append("-" * 50)
        
        for msg in conversation.messages:
            lines.append(f"{msg.role.value.upper()}: {msg.content}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _export_as_markdown(self, conversation: ConversationHistory) -> str:
        """Export conversation as Markdown."""
        lines = [f"# Conversation {conversation.conversation_id}"]
        lines.append(f"**Created:** {conversation.created_at}")
        lines.append(f"**Updated:** {conversation.updated_at}")
        lines.append("")
        
        for msg in conversation.messages:
            if msg.role == MessageRole.USER:
                lines.append(f"## User")
            else:
                lines.append(f"## Assistant")
            lines.append(f"{msg.content}")
            lines.append("")
        
        return "\n".join(lines)
    
    async def submit_feedback(
        self,
        conversation_id: str,
        message_index: int,
        rating: int,
        feedback: Optional[str] = None
    ) -> bool:
        """Submit feedback for a message."""
        try:
            if conversation_id not in self.feedback_data:
                self.feedback_data[conversation_id] = []
            
            feedback_entry = {
                "message_index": message_index,
                "rating": rating,
                "feedback": feedback,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.feedback_data[conversation_id].append(feedback_entry)
            
            logger.info(f"Feedback submitted for conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            raise 