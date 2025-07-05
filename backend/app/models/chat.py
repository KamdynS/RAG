from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message roles in chat."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Model for chat messages."""
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What is the main topic of the uploaded document?",
                "timestamp": "2023-01-01T00:00:00Z"
            }
        }


class ChatRequest(BaseModel):
    """Request model for chat completion."""
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    knowledge_base_id: Optional[str] = Field(None, description="Knowledge base to search")
    max_tokens: Optional[int] = Field(default=1000, description="Maximum tokens in response")
    temperature: Optional[float] = Field(default=0.7, description="Response temperature")
    include_sources: bool = Field(default=True, description="Include source citations")
    use_annotations: bool = Field(default=True, description="Use in-text annotations for citations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the key findings in the research paper?",
                "conversation_id": "conv_123",
                "knowledge_base_id": "kb_456",
                "max_tokens": 1000,
                "temperature": 0.7,
                "include_sources": True,
                "use_annotations": True
            }
        }


class CitationLocation(BaseModel):
    """Model for specific location within a document."""
    document_id: str = Field(..., description="Source document ID")
    document_name: str = Field(..., description="Source document name")
    chunk_id: str = Field(..., description="Source chunk ID")
    page_number: Optional[int] = Field(None, description="Page number if available")
    section: Optional[str] = Field(None, description="Section or chapter")
    start_char: Optional[int] = Field(None, description="Character start position in chunk")
    end_char: Optional[int] = Field(None, description="Character end position in chunk")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123",
                "document_name": "research_paper.pdf",
                "chunk_id": "chunk_456",
                "page_number": 15,
                "section": "Results",
                "start_char": 100,
                "end_char": 350
            }
        }


class Annotation(BaseModel):
    """Model for in-text annotations with citations."""
    id: str = Field(..., description="Unique annotation ID")
    citation_number: int = Field(..., description="Citation number in text (1, 2, 3, etc.)")
    text_snippet: str = Field(..., description="The actual text that was cited")
    source_content: str = Field(..., description="Original content from source")
    location: CitationLocation = Field(..., description="Location in source document")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    quote_type: str = Field(default="reference", description="Type: 'quote', 'paraphrase', 'reference'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "annotation_1",
                "citation_number": 1,
                "text_snippet": "revenue increased by 15%",
                "source_content": "The quarterly revenue increased by 15% compared to the previous quarter, showing strong market performance.",
                "location": {
                    "document_id": "doc_123",
                    "document_name": "financial_report.pdf",
                    "chunk_id": "chunk_456",
                    "page_number": 5,
                    "section": "Financial Summary"
                },
                "relevance_score": 0.95,
                "quote_type": "quote"
            }
        }


class AnnotatedText(BaseModel):
    """Model for text with embedded annotations."""
    raw_text: str = Field(..., description="Original response text with citation markers")
    formatted_text: str = Field(..., description="Text formatted for display")
    annotations: List[Annotation] = Field(default_factory=list, description="List of annotations")
    citation_map: Dict[int, str] = Field(default_factory=dict, description="Map of citation numbers to annotation IDs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "raw_text": "The quarterly revenue increased by 15% [1] according to the latest financial report.",
                "formatted_text": "The quarterly revenue increased by 15% <cite data-annotation='annotation_1'>[1]</cite> according to the latest financial report.",
                "annotations": [
                    {
                        "id": "annotation_1",
                        "citation_number": 1,
                        "text_snippet": "revenue increased by 15%",
                        "source_content": "The quarterly revenue increased by 15% compared to the previous quarter",
                        "location": {
                            "document_id": "doc_123",
                            "document_name": "financial_report.pdf",
                            "chunk_id": "chunk_456"
                        },
                        "relevance_score": 0.95,
                        "quote_type": "quote"
                    }
                ],
                "citation_map": {"1": "annotation_1"}
            }
        }


class BlockQuote(BaseModel):
    """Model for block quotes with citations."""
    id: str = Field(..., description="Unique quote ID")
    content: str = Field(..., description="Quoted content")
    location: CitationLocation = Field(..., description="Source location")
    context_before: Optional[str] = Field(None, description="Context before the quote")
    context_after: Optional[str] = Field(None, description="Context after the quote")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "quote_1",
                "content": "Our analysis shows a significant improvement in customer satisfaction metrics across all product lines.",
                "location": {
                    "document_id": "doc_123",
                    "document_name": "customer_survey.pdf",
                    "chunk_id": "chunk_789",
                    "page_number": 12
                },
                "context_before": "The survey results indicate that",
                "context_after": "This trend is consistent with industry benchmarks."
            }
        }


class SourceCitation(BaseModel):
    """Enhanced model for source citations with annotation support."""
    document_id: str = Field(..., description="Source document ID")
    document_name: str = Field(..., description="Source document name")
    chunk_id: str = Field(..., description="Source chunk ID")
    content: str = Field(..., description="Relevant content excerpt")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    page_number: Optional[int] = Field(None, description="Page number if available")
    section: Optional[str] = Field(None, description="Document section")
    citation_count: int = Field(default=0, description="Number of times cited in response")
    used_in_annotations: List[str] = Field(default_factory=list, description="List of annotation IDs that reference this source")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123",
                "document_name": "research_paper.pdf",
                "chunk_id": "chunk_456",
                "content": "The study found that...",
                "relevance_score": 0.95,
                "page_number": 15,
                "section": "Results",
                "citation_count": 2,
                "used_in_annotations": ["annotation_1", "annotation_3"]
            }
        }


class ChatResponse(BaseModel):
    """Enhanced response model for chat completion with annotations."""
    response: str = Field(..., description="Raw generated response")
    annotated_response: Optional[AnnotatedText] = Field(None, description="Response with annotations")
    conversation_id: str = Field(..., description="Conversation ID")
    sources: List[SourceCitation] = Field(default_factory=list, description="Source citations")
    block_quotes: List[BlockQuote] = Field(default_factory=list, description="Block quotes used in response")
    tokens_used: int = Field(..., description="Number of tokens used")
    response_time: float = Field(..., description="Response time in seconds")
    has_annotations: bool = Field(default=False, description="Whether response includes annotations")
    citation_style: str = Field(default="numbered", description="Citation style used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Based on the research paper, the key findings are significant improvements in efficiency [1] and cost reduction [2].",
                "annotated_response": {
                    "raw_text": "Based on the research paper, the key findings are significant improvements in efficiency [1] and cost reduction [2].",
                    "formatted_text": "Based on the research paper, the key findings are significant improvements in efficiency <cite data-annotation='annotation_1'>[1]</cite> and cost reduction <cite data-annotation='annotation_2'>[2]</cite>.",
                    "annotations": [],
                    "citation_map": {"1": "annotation_1", "2": "annotation_2"}
                },
                "conversation_id": "conv_123",
                "sources": [],
                "block_quotes": [],
                "tokens_used": 250,
                "response_time": 1.5,
                "has_annotations": True,
                "citation_style": "numbered"
            }
        }


class ConversationHistory(BaseModel):
    """Model for conversation history."""
    conversation_id: str = Field(..., description="Conversation ID")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    created_at: datetime = Field(..., description="Conversation creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123",
                "messages": [
                    {
                        "role": "user",
                        "content": "What is this document about?",
                        "timestamp": "2023-01-01T00:00:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "This document is about...",
                        "timestamp": "2023-01-01T00:00:05Z"
                    }
                ],
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:05Z"
            }
        }


class ConversationListResponse(BaseModel):
    """Response model for conversation listing."""
    conversations: List[ConversationHistory] = Field(..., description="List of conversations")
    total: int = Field(..., description="Total number of conversations")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversations": [
                    {
                        "conversation_id": "conv_123",
                        "messages": [],
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-01-01T00:00:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 10
            }
        } 