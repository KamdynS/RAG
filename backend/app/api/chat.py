from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
import uuid
import logging
from datetime import datetime

from app.models.chat import (
    ChatRequest,
    ChatResponse,
    ConversationHistory,
    ConversationListResponse,
    ChatMessage,
    MessageRole
)
from app.models.common import ErrorResponse, PaginationParams
from app.core.config import settings
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get chat service
def get_chat_service() -> ChatService:
    return ChatService()


@router.post("/", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Generate a chat completion using RAG.
    
    - **message**: The user's message/question
    - **conversation_id**: Optional conversation ID for context
    - **knowledge_base_id**: Optional knowledge base to search
    - **max_tokens**: Maximum tokens in response
    - **temperature**: Response temperature (0.0 to 1.0)
    - **include_sources**: Whether to include source citations
    """
    try:
        # Generate or use existing conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Generate chat response
        chat_response = await chat_service.generate_response(
            message=request.message,
            conversation_id=conversation_id,
            knowledge_base_id=request.knowledge_base_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            include_sources=request.include_sources,
            use_annotations=request.use_annotations
        )
        
        logger.info(f"Chat completion generated for conversation: {conversation_id}")
        return chat_response
        
    except Exception as e:
        logger.error(f"Error generating chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during chat completion")


@router.post("/stream", response_class=StreamingResponse)
async def chat_completion_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Generate a streaming chat completion using RAG.
    
    - **message**: The user's message/question
    - **conversation_id**: Optional conversation ID for context
    - **knowledge_base_id**: Optional knowledge base to search
    - **max_tokens**: Maximum tokens in response
    - **temperature**: Response temperature (0.0 to 1.0)
    - **include_sources**: Whether to include source citations
    """
    try:
        # Generate or use existing conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Generate streaming response
        stream_generator = chat_service.generate_streaming_response(
            message=request.message,
            conversation_id=conversation_id,
            knowledge_base_id=request.knowledge_base_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            include_sources=request.include_sources,
            use_annotations=request.use_annotations
        )
        
        return StreamingResponse(
            stream_generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating streaming chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during streaming chat completion")


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    List user's conversations with pagination.
    
    - **page**: Page number (starting from 1)
    - **size**: Number of conversations per page
    """
    try:
        conversations_response = await chat_service.list_conversations(
            page=page,
            size=size
        )
        return conversations_response
        
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while listing conversations")


@router.get("/conversations/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(
    conversation_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get a specific conversation by ID.
    
    - **conversation_id**: The conversation ID
    """
    try:
        conversation = await chat_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving conversation")


@router.delete("/conversations/{conversation_id}", response_model=dict)
async def delete_conversation(
    conversation_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Delete a conversation and its message history.
    
    - **conversation_id**: The conversation ID to delete
    """
    try:
        # Check if conversation exists
        conversation = await chat_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Delete the conversation
        await chat_service.delete_conversation(conversation_id)
        
        return {
            "message": "Conversation deleted successfully",
            "deleted_conversation_id": conversation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting conversation")


@router.post("/conversations/{conversation_id}/clear", response_model=dict)
async def clear_conversation(
    conversation_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Clear all messages from a conversation (but keep the conversation).
    
    - **conversation_id**: The conversation ID to clear
    """
    try:
        # Check if conversation exists
        conversation = await chat_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Clear the conversation
        await chat_service.clear_conversation(conversation_id)
        
        return {
            "message": "Conversation cleared successfully",
            "conversation_id": conversation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while clearing conversation")


@router.get("/conversations/{conversation_id}/export", response_model=dict)
async def export_conversation(
    conversation_id: str,
    format: str = Query("json", description="Export format: json, txt, or md"),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Export a conversation in the specified format.
    
    - **conversation_id**: The conversation ID to export
    - **format**: Export format (json, txt, or md)
    """
    try:
        # Check if conversation exists
        conversation = await chat_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Validate format
        if format not in ["json", "txt", "md"]:
            raise HTTPException(status_code=400, detail="Invalid format. Supported formats: json, txt, md")
        
        # Export the conversation
        exported_data = await chat_service.export_conversation(conversation_id, format)
        
        return {
            "conversation_id": conversation_id,
            "format": format,
            "exported_at": datetime.utcnow().isoformat(),
            "data": exported_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while exporting conversation")


@router.post("/feedback", response_model=dict)
async def submit_feedback(
    conversation_id: str,
    message_index: int,
    rating: int = Query(..., ge=1, le=5, description="Rating from 1 to 5"),
    feedback: Optional[str] = Query(None, description="Optional feedback text"),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Submit feedback for a specific message in a conversation.
    
    - **conversation_id**: The conversation ID
    - **message_index**: Index of the message to rate
    - **rating**: Rating from 1 to 5
    - **feedback**: Optional feedback text
    """
    try:
        # Submit feedback
        await chat_service.submit_feedback(
            conversation_id=conversation_id,
            message_index=message_index,
            rating=rating,
            feedback=feedback
        )
        
        return {
            "message": "Feedback submitted successfully",
            "conversation_id": conversation_id,
            "message_index": message_index,
            "rating": rating
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while submitting feedback")


@router.get("/annotations/{annotation_id}", response_model=dict)
async def get_annotation_detail(
    annotation_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get detailed information about a specific annotation.
    
    This endpoint is called when users click on citation links to get
    the full context and source information.
    
    - **annotation_id**: The annotation ID from the response
    """
    try:
        # This is a placeholder implementation
        # In a real system, you'd look up the annotation by ID
        # For now, we'll return a placeholder response
        return {
            "annotation_id": annotation_id,
            "message": "Annotation detail retrieval not fully implemented",
            "note": "This endpoint will be enhanced when we add persistent storage"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving annotation {annotation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving annotation") 