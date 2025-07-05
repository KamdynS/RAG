import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.models.document import DocumentChunk

logger = logging.getLogger(__name__)


@dataclass
class ChunkingOptions:
    """Options for text chunking."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    respect_sentence_boundaries: bool = True
    respect_paragraph_boundaries: bool = True
    min_chunk_size: int = 100
    max_chunk_size: int = 2000


class TextChunker:
    """Intelligent text chunking utility."""
    
    def __init__(self):
        # Sentence boundary patterns
        self.sentence_endings = re.compile(r'[.!?]+\s+')
        self.paragraph_breaks = re.compile(r'\n\s*\n')
        
        # Section headers (for documents with structure)
        self.section_headers = re.compile(r'^#+\s+.*$|^[A-Z][A-Z\s]+:?\s*$', re.MULTILINE)
    
    async def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        document_id: str = "",
        options: Optional[ChunkingOptions] = None
    ) -> List[DocumentChunk]:
        """
        Split text into chunks with intelligent boundaries.
        
        Args:
            text: Text to chunk
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            document_id: Document ID for chunk metadata
            options: Additional chunking options
            
        Returns:
            List of DocumentChunk objects
        """
        if not text.strip():
            return []
        
        if options is None:
            options = ChunkingOptions(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        
        try:
            # Preprocess text
            text = self._preprocess_text(text)
            
            # Try hierarchical chunking first
            chunks = self._hierarchical_chunk(text, options, document_id)
            
            # If hierarchical chunking didn't work well, fall back to simple chunking
            if not chunks or self._needs_rechunking(chunks, options):
                chunks = self._simple_chunk(text, options, document_id)
            
            # Post-process chunks
            chunks = self._post_process_chunks(chunks, options)
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for chunking."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Clean up common document artifacts
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\t+', ' ', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        
        return text.strip()
    
    def _hierarchical_chunk(
        self,
        text: str,
        options: ChunkingOptions,
        document_id: str
    ) -> List[DocumentChunk]:
        """
        Chunk text using hierarchical approach (sections -> paragraphs -> sentences).
        """
        chunks = []
        
        # Try to split by major sections first
        sections = self._split_by_sections(text)
        
        for section_idx, section in enumerate(sections):
            section_chunks = self._chunk_section(
                section,
                options,
                document_id,
                section_idx
            )
            chunks.extend(section_chunks)
        
        return chunks
    
    def _split_by_sections(self, text: str) -> List[str]:
        """Split text into sections based on headers."""
        # Look for section headers
        sections = []
        current_section = ""
        
        lines = text.split('\n')
        for line in lines:
            # Check if this line is a section header
            if self._is_section_header(line):
                # Save previous section if it exists
                if current_section.strip():
                    sections.append(current_section.strip())
                # Start new section
                current_section = line + '\n'
            else:
                current_section += line + '\n'
        
        # Add the last section
        if current_section.strip():
            sections.append(current_section.strip())
        
        # If no sections found, return the entire text
        if not sections:
            return [text]
        
        return sections
    
    def _is_section_header(self, line: str) -> bool:
        """Check if a line is a section header."""
        line = line.strip()
        
        # Markdown headers
        if line.startswith('#'):
            return True
        
        # All caps headers
        if line.isupper() and len(line) > 3 and line.endswith(':'):
            return True
        
        # Numbered sections
        if re.match(r'^\d+\.?\s+[A-Z]', line):
            return True
        
        return False
    
    def _chunk_section(
        self,
        section: str,
        options: ChunkingOptions,
        document_id: str,
        section_idx: int
    ) -> List[DocumentChunk]:
        """Chunk a single section."""
        chunks = []
        
        # If section is small enough, keep it as one chunk
        if len(section) <= options.chunk_size:
            chunk = DocumentChunk(
                id=f"{document_id}_section_{section_idx}_chunk_0",
                content=section,
                chunk_index=len(chunks),
                metadata={
                    "section": section_idx,
                    "chunk_method": "section_intact"
                }
            )
            return [chunk]
        
        # Split section by paragraphs
        paragraphs = self.paragraph_breaks.split(section)
        
        current_chunk = ""
        chunk_idx = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(para) > options.chunk_size:
                # Save current chunk if it has content
                if current_chunk.strip():
                    chunk = DocumentChunk(
                        id=f"{document_id}_section_{section_idx}_chunk_{chunk_idx}",
                        content=current_chunk.strip(),
                        chunk_index=len(chunks),
                        metadata={
                            "section": section_idx,
                            "chunk_method": "paragraph_boundary"
                        }
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                
                # Start new chunk
                if len(para) > options.max_chunk_size:
                    # Paragraph is too long, need to split it
                    para_chunks = self._split_large_paragraph(
                        para,
                        options,
                        document_id,
                        section_idx,
                        chunk_idx
                    )
                    chunks.extend(para_chunks)
                    chunk_idx += len(para_chunks)
                    current_chunk = ""
                else:
                    current_chunk = para
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Save final chunk
        if current_chunk.strip():
            chunk = DocumentChunk(
                id=f"{document_id}_section_{section_idx}_chunk_{chunk_idx}",
                content=current_chunk.strip(),
                chunk_index=len(chunks),
                metadata={
                    "section": section_idx,
                    "chunk_method": "paragraph_boundary"
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_large_paragraph(
        self,
        paragraph: str,
        options: ChunkingOptions,
        document_id: str,
        section_idx: int,
        start_chunk_idx: int
    ) -> List[DocumentChunk]:
        """Split a large paragraph into smaller chunks."""
        chunks = []
        
        # Try to split by sentences
        sentences = self._split_by_sentences(paragraph)
        
        current_chunk = ""
        chunk_idx = start_chunk_idx
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > options.chunk_size:
                # Save current chunk if it has content
                if current_chunk.strip():
                    chunk = DocumentChunk(
                        id=f"{document_id}_section_{section_idx}_chunk_{chunk_idx}",
                        content=current_chunk.strip(),
                        chunk_index=len(chunks),
                        metadata={
                            "section": section_idx,
                            "chunk_method": "sentence_boundary"
                        }
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                
                # If sentence is still too long, split it arbitrarily
                if len(sentence) > options.max_chunk_size:
                    sentence_chunks = self._split_sentence_arbitrarily(
                        sentence,
                        options,
                        document_id,
                        section_idx,
                        chunk_idx
                    )
                    chunks.extend(sentence_chunks)
                    chunk_idx += len(sentence_chunks)
                    current_chunk = ""
                else:
                    current_chunk = sentence
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Save final chunk
        if current_chunk.strip():
            chunk = DocumentChunk(
                id=f"{document_id}_section_{section_idx}_chunk_{chunk_idx}",
                content=current_chunk.strip(),
                chunk_index=len(chunks),
                metadata={
                    "section": section_idx,
                    "chunk_method": "sentence_boundary"
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences."""
        sentences = []
        current_sentence = ""
        
        # Split by sentence endings
        parts = self.sentence_endings.split(text)
        
        for i, part in enumerate(parts):
            current_sentence += part
            
            # If this isn't the last part, add the sentence ending back
            if i < len(parts) - 1:
                # Find the sentence ending that was used to split
                match = self.sentence_endings.search(text[len(''.join(parts[:i+1])):])
                if match:
                    current_sentence += match.group()
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
        
        # Add any remaining content
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences
    
    def _split_sentence_arbitrarily(
        self,
        sentence: str,
        options: ChunkingOptions,
        document_id: str,
        section_idx: int,
        start_chunk_idx: int
    ) -> List[DocumentChunk]:
        """Split a very long sentence arbitrarily."""
        chunks = []
        chunk_idx = start_chunk_idx
        
        # Split by words and reassemble
        words = sentence.split()
        current_chunk = ""
        
        for word in words:
            if len(current_chunk) + len(word) + 1 > options.chunk_size:
                if current_chunk.strip():
                    chunk = DocumentChunk(
                        id=f"{document_id}_section_{section_idx}_chunk_{chunk_idx}",
                        content=current_chunk.strip(),
                        chunk_index=len(chunks),
                        metadata={
                            "section": section_idx,
                            "chunk_method": "arbitrary_split"
                        }
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                current_chunk = word
            else:
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word
        
        # Save final chunk
        if current_chunk.strip():
            chunk = DocumentChunk(
                id=f"{document_id}_section_{section_idx}_chunk_{chunk_idx}",
                content=current_chunk.strip(),
                chunk_index=len(chunks),
                metadata={
                    "section": section_idx,
                    "chunk_method": "arbitrary_split"
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _simple_chunk(
        self,
        text: str,
        options: ChunkingOptions,
        document_id: str
    ) -> List[DocumentChunk]:
        """Simple chunking with overlap."""
        chunks = []
        
        # Calculate positions
        chunk_size = options.chunk_size
        overlap = options.chunk_overlap
        step = chunk_size - overlap
        
        start = 0
        chunk_idx = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If this is not the last chunk, try to end at a word boundary
            if end < len(text) and options.respect_sentence_boundaries:
                # Look for sentence boundary within the last 20% of the chunk
                boundary_start = start + int(chunk_size * 0.8)
                boundary_end = min(end, len(text))
                
                # Find the last sentence ending in this range
                chunk_text = text[boundary_start:boundary_end]
                sentence_match = None
                for match in self.sentence_endings.finditer(chunk_text):
                    sentence_match = match
                
                if sentence_match:
                    end = boundary_start + sentence_match.end()
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            if chunk_text and len(chunk_text) >= options.min_chunk_size:
                chunk = DocumentChunk(
                    id=f"{document_id}_chunk_{chunk_idx}",
                    content=chunk_text,
                    chunk_index=chunk_idx,
                    metadata={
                        "start_pos": start,
                        "end_pos": end,
                        "chunk_method": "simple_overlap"
                    }
                )
                chunks.append(chunk)
                chunk_idx += 1
            
            start += step
        
        return chunks
    
    def _needs_rechunking(self, chunks: List[DocumentChunk], options: ChunkingOptions) -> bool:
        """Check if chunks need to be rechunked."""
        if not chunks:
            return True
        
        # Check if chunks are too small or too large
        for chunk in chunks:
            if len(chunk.content) < options.min_chunk_size:
                return True
            if len(chunk.content) > options.max_chunk_size:
                return True
        
        return False
    
    def _post_process_chunks(
        self,
        chunks: List[DocumentChunk],
        options: ChunkingOptions
    ) -> List[DocumentChunk]:
        """Post-process chunks to improve quality."""
        if not chunks:
            return chunks
        
        # Merge very small chunks with adjacent chunks
        merged_chunks = []
        i = 0
        
        while i < len(chunks):
            current_chunk = chunks[i]
            
            # If chunk is too small and not the last chunk
            if (len(current_chunk.content) < options.min_chunk_size and 
                i < len(chunks) - 1):
                
                next_chunk = chunks[i + 1]
                
                # Try to merge with next chunk
                if (len(current_chunk.content) + len(next_chunk.content) 
                    <= options.max_chunk_size):
                    
                    merged_content = current_chunk.content + "\n\n" + next_chunk.content
                    merged_metadata = {**current_chunk.metadata, **next_chunk.metadata}
                    merged_metadata["merged"] = True
                    
                    merged_chunk = DocumentChunk(
                        id=current_chunk.id,
                        content=merged_content,
                        chunk_index=current_chunk.chunk_index,
                        metadata=merged_metadata
                    )
                    merged_chunks.append(merged_chunk)
                    i += 2  # Skip both chunks
                    continue
            
            merged_chunks.append(current_chunk)
            i += 1
        
        # Update chunk indices
        for idx, chunk in enumerate(merged_chunks):
            chunk.chunk_index = idx
        
        return merged_chunks 