import re
import uuid
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from app.models.chat import (
    Annotation, 
    AnnotatedText, 
    BlockQuote, 
    CitationLocation
)
from app.models.document import DocumentChunk


@dataclass
class ParsedCitation:
    """Internal data structure for parsed citations."""
    numbers: List[int]
    start_pos: int
    end_pos: int
    text_before: str
    text_after: str
    is_block_quote: bool = False
    quote_content: str = ""


class CitationParser:
    """Parser for extracting and processing citations from AI responses."""
    
    def __init__(self):
        # Regex patterns for different citation formats
        self.citation_patterns = {
            'numbered': r'\[(\d+(?:,\d+)*)\]',  # [1], [2], [1,2]
            'numbered_multiple': r'\[(\d+)\]\[(\d+)\]',  # [1][2]
            'block_quote': r'> "(.*?)" \[(\d+)\]',  # > "quote" [1]
            'block_quote_multiline': r'> "(.*?)" \[(\d+)\]',  # Multi-line quotes
        }
        
        # HTML templates for formatting
        self.html_templates = {
            'citation': '<cite data-annotation="{annotation_id}" data-citation="{citation_num}" class="citation-link">[{citation_num}]</cite>',
            'block_quote': '<blockquote data-annotation="{annotation_id}" data-citation="{citation_num}" class="citation-quote">{content}</blockquote>',
        }
    
    def parse_response(
        self, 
        response_text: str, 
        source_chunks: List[DocumentChunk]
    ) -> AnnotatedText:
        """
        Parse AI response and extract citations to create annotated text.
        
        Args:
            response_text: The AI-generated response text
            source_chunks: List of source chunks that were used for context
            
        Returns:
            AnnotatedText object with parsed citations and annotations
        """
        # Find all citations in the text
        citations = self._find_citations(response_text)
        
        # Create annotations from citations
        annotations = self._create_annotations(citations, source_chunks, response_text)
        
        # Create citation mapping
        citation_map = {ann.citation_number: ann.id for ann in annotations}
        
        # Format text with HTML annotations
        formatted_text = self._format_text_with_annotations(response_text, annotations)
        
        return AnnotatedText(
            raw_text=response_text,
            formatted_text=formatted_text,
            annotations=annotations,
            citation_map=citation_map
        )
    
    def _find_citations(self, text: str) -> List[ParsedCitation]:
        """Find all citations in the text."""
        citations = []
        
        # Find numbered citations [1], [2], [1,2]
        for match in re.finditer(self.citation_patterns['numbered'], text):
            numbers = [int(n.strip()) for n in match.group(1).split(',')]
            citation = ParsedCitation(
                numbers=numbers,
                start_pos=match.start(),
                end_pos=match.end(),
                text_before=text[max(0, match.start()-50):match.start()],
                text_after=text[match.end():match.end()+50]
            )
            citations.append(citation)
        
        # Find block quotes with citations
        for match in re.finditer(self.citation_patterns['block_quote'], text, re.DOTALL):
            quote_content = match.group(1)
            citation_num = int(match.group(2))
            
            citation = ParsedCitation(
                numbers=[citation_num],
                start_pos=match.start(),
                end_pos=match.end(),
                text_before=text[max(0, match.start()-50):match.start()],
                text_after=text[match.end():match.end()+50],
                is_block_quote=True,
                quote_content=quote_content
            )
            citations.append(citation)
        
        return sorted(citations, key=lambda x: x.start_pos)
    
    def _create_annotations(
        self, 
        citations: List[ParsedCitation], 
        source_chunks: List[DocumentChunk],
        response_text: str
    ) -> List[Annotation]:
        """Create annotation objects from parsed citations."""
        annotations = []
        
        for citation in citations:
            for citation_num in citation.numbers:
                # Get the corresponding source chunk (1-indexed)
                if citation_num <= len(source_chunks):
                    chunk = source_chunks[citation_num - 1]
                    
                    # Extract the text snippet that was cited
                    text_snippet = self._extract_text_snippet(
                        response_text, 
                        citation.start_pos, 
                        citation.end_pos,
                        citation.is_block_quote,
                        citation.quote_content
                    )
                    
                    # Create location object
                    location = CitationLocation(
                        document_id=chunk.metadata.get('document_id', 'unknown'),
                        document_name=chunk.metadata.get('document_name', 'Unknown Document'),
                        chunk_id=chunk.id,
                        page_number=chunk.metadata.get('page_number'),
                        section=chunk.metadata.get('section'),
                        start_char=chunk.metadata.get('start_char'),
                        end_char=chunk.metadata.get('end_char')
                    )
                    
                    # Determine quote type
                    quote_type = "quote" if citation.is_block_quote else "reference"
                    
                    # Create annotation
                    annotation = Annotation(
                        id=f"annotation_{uuid.uuid4().hex[:8]}",
                        citation_number=citation_num,
                        text_snippet=text_snippet,
                        source_content=chunk.content,
                        location=location,
                        relevance_score=chunk.metadata.get('similarity_score', 0.0),
                        quote_type=quote_type
                    )
                    
                    annotations.append(annotation)
        
        return annotations
    
    def _extract_text_snippet(
        self, 
        response_text: str, 
        start_pos: int, 
        end_pos: int,
        is_block_quote: bool,
        quote_content: str
    ) -> str:
        """Extract the text snippet that was cited."""
        if is_block_quote:
            return quote_content
        
        # For regular citations, extract surrounding context
        # Look for sentence boundaries
        snippet_start = max(0, start_pos - 100)
        snippet_end = min(len(response_text), end_pos + 100)
        
        # Find sentence boundaries
        text_before = response_text[snippet_start:start_pos]
        text_after = response_text[end_pos:snippet_end]
        
        # Try to find sentence start
        sentence_start = snippet_start
        if '. ' in text_before:
            sentence_start = text_before.rfind('. ') + snippet_start + 2
        
        # Try to find sentence end
        sentence_end = snippet_end
        if '. ' in text_after:
            sentence_end = text_after.find('. ') + end_pos + 1
        
        # Extract the snippet
        snippet = response_text[sentence_start:sentence_end].strip()
        
        # Remove the citation itself from the snippet
        citation_pattern = r'\[\d+(?:,\d+)*\]'
        snippet = re.sub(citation_pattern, '', snippet).strip()
        
        return snippet
    
    def _format_text_with_annotations(
        self, 
        text: str, 
        annotations: List[Annotation]
    ) -> str:
        """Format text with HTML annotations for frontend rendering."""
        formatted_text = text
        
        # Group annotations by citation number to avoid duplicates
        citation_groups = {}
        for annotation in annotations:
            if annotation.citation_number not in citation_groups:
                citation_groups[annotation.citation_number] = annotation
        
        # Replace citations with HTML, working backwards to preserve positions
        citation_pattern = r'\[(\d+(?:,\d+)*)\]'
        
        # Find all matches and their positions
        matches = list(re.finditer(citation_pattern, formatted_text))
        
        # Process matches in reverse order to maintain positions
        for match in reversed(matches):
            citation_nums = [int(n.strip()) for n in match.group(1).split(',')]
            
            # Create HTML for this citation
            html_parts = []
            for num in citation_nums:
                if num in citation_groups:
                    annotation = citation_groups[num]
                    html = self.html_templates['citation'].format(
                        annotation_id=annotation.id,
                        citation_num=num
                    )
                    html_parts.append(html)
                else:
                    html_parts.append(f'[{num}]')
            
            # Replace the citation with HTML
            formatted_text = (
                formatted_text[:match.start()] + 
                ''.join(html_parts) + 
                formatted_text[match.end():]
            )
        
        # Handle block quotes
        block_quote_pattern = r'> "(.*?)" \[(\d+)\]'
        for match in reversed(list(re.finditer(block_quote_pattern, formatted_text, re.DOTALL))):
            quote_content = match.group(1)
            citation_num = int(match.group(2))
            
            if citation_num in citation_groups:
                annotation = citation_groups[citation_num]
                html = self.html_templates['block_quote'].format(
                    annotation_id=annotation.id,
                    citation_num=citation_num,
                    content=quote_content
                )
                
                formatted_text = (
                    formatted_text[:match.start()] + 
                    html + 
                    formatted_text[match.end():]
                )
        
        return formatted_text
    
    def extract_block_quotes(
        self, 
        response_text: str, 
        source_chunks: List[DocumentChunk]
    ) -> List[BlockQuote]:
        """Extract block quotes from the response."""
        block_quotes = []
        
        # Find all block quotes
        pattern = r'> "(.*?)" \[(\d+)\]'
        for match in re.finditer(pattern, response_text, re.DOTALL):
            quote_content = match.group(1)
            citation_num = int(match.group(2))
            
            # Get the corresponding source chunk
            if citation_num <= len(source_chunks):
                chunk = source_chunks[citation_num - 1]
                
                location = CitationLocation(
                    document_id=chunk.metadata.get('document_id', 'unknown'),
                    document_name=chunk.metadata.get('document_name', 'Unknown Document'),
                    chunk_id=chunk.id,
                    page_number=chunk.metadata.get('page_number'),
                    section=chunk.metadata.get('section')
                )
                
                block_quote = BlockQuote(
                    id=f"quote_{uuid.uuid4().hex[:8]}",
                    content=quote_content,
                    location=location,
                    context_before=self._get_context_before(response_text, match.start()),
                    context_after=self._get_context_after(response_text, match.end())
                )
                
                block_quotes.append(block_quote)
        
        return block_quotes
    
    def _get_context_before(self, text: str, pos: int, max_length: int = 100) -> str:
        """Get context before a position."""
        start = max(0, pos - max_length)
        context = text[start:pos].strip()
        
        # Try to find sentence boundary
        if '. ' in context:
            context = context[context.rfind('. ') + 2:]
        
        return context
    
    def _get_context_after(self, text: str, pos: int, max_length: int = 100) -> str:
        """Get context after a position."""
        end = min(len(text), pos + max_length)
        context = text[pos:end].strip()
        
        # Try to find sentence boundary
        if '. ' in context:
            context = context[:context.find('. ') + 1]
        
        return context 