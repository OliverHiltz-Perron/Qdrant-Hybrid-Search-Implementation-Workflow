"""Document processing module for analyzing and chunking markdown documents."""

import re
from typing import List, Dict, Tuple, Optional
import tiktoken
from pathlib import Path


class DocumentProcessor:
    """Process markdown documents for extraction."""
    
    def __init__(self, config: Dict):
        """Initialize document processor with configuration.
        
        Args:
            config: Configuration dictionary containing model and chunking settings
        """
        self.config = config
        model_name = config['model_config']['model_name']
        # Map gpt-4.1-mini to gpt-4o-mini for tokenizer
        if model_name == "gpt-4.1-mini":
            tokenizer_model = "gpt-4o-mini"
        else:
            tokenizer_model = model_name
        
        try:
            self.encoding = tiktoken.encoding_for_model(tokenizer_model)
        except KeyError:
            # Fallback to cl100k_base encoding (used by GPT-4 models)
            self.encoding = tiktoken.get_encoding("cl100k_base")
        self.chunk_config = config.get('chunking_config', {})
        
    def analyze_structure(self, markdown_text: str) -> Dict:
        """Analyze document structure to identify key sections.
        
        Args:
            markdown_text: The markdown content to analyze
            
        Returns:
            Dictionary containing document structure information
        """
        structure = {
            "headings": [],
            "sections": {},
            "total_tokens": len(self.encoding.encode(markdown_text)),
            "pages": self._estimate_pages(markdown_text)
        }
        
        # Extract all headings with their levels
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        for match in re.finditer(heading_pattern, markdown_text, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            position = match.start()
            
            structure["headings"].append({
                "level": level,
                "title": title,
                "position": position
            })
        
        # Identify major sections
        section_keywords = [
            "eligibility", "monitoring", "evaluation", "funding", 
            "workforce", "trauma", "equity", "outcomes", "populations",
            "accountability", "prevention", "services", "implementation"
        ]
        
        for keyword in section_keywords:
            pattern = rf'(?i)^#+.*{keyword}.*$'
            matches = list(re.finditer(pattern, markdown_text, re.MULTILINE))
            if matches:
                structure["sections"][keyword] = [
                    {"title": m.group(), "position": m.start()} 
                    for m in matches
                ]
        
        return structure
    
    def smart_chunk(self, markdown_text: str, 
                   target_size: Optional[int] = None,
                   overlap: Optional[int] = None) -> List[Dict]:
        """Create smart chunks that respect document structure.
        
        Args:
            markdown_text: The markdown content to chunk
            target_size: Target chunk size in tokens (uses config default if None)
            overlap: Overlap size in tokens (uses config default if None)
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        if target_size is None:
            target_size = self.chunk_config.get('target_chunk_size', 10000)
        if overlap is None:
            overlap = self.chunk_config.get('overlap', 500)
            
        chunks = []
        structure = self.analyze_structure(markdown_text)
        
        # Split by major sections first
        section_boundaries = self._find_section_boundaries(markdown_text, structure)
        
        for i, (start, end, section_info) in enumerate(section_boundaries):
            section_text = markdown_text[start:end]
            section_tokens = len(self.encoding.encode(section_text))
            
            if section_tokens <= target_size:
                # Section fits in one chunk
                chunks.append({
                    "id": f"chunk_{i}",
                    "content": section_text,
                    "tokens": section_tokens,
                    "section": section_info.get("title", "Unknown"),
                    "type": "section",
                    "start_pos": start,
                    "end_pos": end
                })
            else:
                # Need to split section into smaller chunks
                sub_chunks = self._split_large_section(
                    section_text, target_size, overlap, 
                    base_id=f"chunk_{i}", section_info=section_info,
                    start_offset=start
                )
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _find_section_boundaries(self, text: str, structure: Dict) -> List[Tuple]:
        """Find major section boundaries in the document.
        
        Args:
            text: The markdown text
            structure: Document structure from analyze_structure
            
        Returns:
            List of tuples (start, end, section_info)
        """
        boundaries = []
        headings = structure["headings"]
        
        # Find top-level sections (H1 and H2)
        major_headings = [h for h in headings if h["level"] <= 2]
        
        for i, heading in enumerate(major_headings):
            start = heading["position"]
            # End is either the next major heading or end of document
            if i < len(major_headings) - 1:
                end = major_headings[i + 1]["position"]
            else:
                end = len(text)
                
            boundaries.append((start, end, heading))
        
        # If no major headings, treat whole document as one section
        if not boundaries:
            boundaries.append((0, len(text), {"title": "Full Document", "level": 0}))
        
        return boundaries
    
    def _split_large_section(self, section_text: str, target_size: int, 
                           overlap: int, base_id: str, section_info: Dict,
                           start_offset: int) -> List[Dict]:
        """Split a large section into smaller chunks.
        
        Args:
            section_text: Text of the section to split
            target_size: Target chunk size in tokens
            overlap: Overlap size in tokens
            base_id: Base ID for chunk naming
            section_info: Information about the section
            start_offset: Offset of section start in original document
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        paragraphs = self._split_into_paragraphs(section_text)
        
        current_chunk = []
        current_tokens = 0
        chunk_num = 0
        
        for para in paragraphs:
            para_tokens = len(self.encoding.encode(para))
            
            if current_tokens + para_tokens > target_size and current_chunk:
                # Save current chunk
                chunk_text = "\n\n".join(current_chunk)
                chunks.append({
                    "id": f"{base_id}_{chunk_num}",
                    "content": chunk_text,
                    "tokens": current_tokens,
                    "section": section_info.get("title", "Unknown"),
                    "type": "subsection",
                    "chunk_num": chunk_num,
                    "start_pos": start_offset  # Simplified for now
                })
                
                # Start new chunk with overlap
                if overlap > 0 and chunks:
                    # Include last few paragraphs for overlap
                    overlap_paras = []
                    overlap_tokens = 0
                    for p in reversed(current_chunk):
                        p_tokens = len(self.encoding.encode(p))
                        if overlap_tokens + p_tokens <= overlap:
                            overlap_paras.insert(0, p)
                            overlap_tokens += p_tokens
                        else:
                            break
                    current_chunk = overlap_paras
                    current_tokens = overlap_tokens
                else:
                    current_chunk = []
                    current_tokens = 0
                
                chunk_num += 1
            
            current_chunk.append(para)
            current_tokens += para_tokens
        
        # Save final chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append({
                "id": f"{base_id}_{chunk_num}",
                "content": chunk_text,
                "tokens": current_tokens,
                "section": section_info.get("title", "Unknown"),
                "type": "subsection",
                "chunk_num": chunk_num,
                "start_pos": start_offset
            })
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs.
        
        Args:
            text: Text to split
            
        Returns:
            List of paragraph strings
        """
        # Split on double newlines, but preserve list items and tables
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Clean up and filter empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Merge small paragraphs that might be list items
        merged = []
        i = 0
        while i < len(paragraphs):
            current = paragraphs[i]
            
            # Check if this might be a list item or table row
            if (i < len(paragraphs) - 1 and 
                (current.startswith(('- ', '* ', '+ ', '|')) or 
                 re.match(r'^\d+\.', current))):
                # Merge consecutive list items
                items = [current]
                j = i + 1
                while j < len(paragraphs) and (
                    paragraphs[j].startswith(('- ', '* ', '+ ', '|')) or 
                    re.match(r'^\d+\.', paragraphs[j])
                ):
                    items.append(paragraphs[j])
                    j += 1
                merged.append('\n'.join(items))
                i = j
            else:
                merged.append(current)
                i += 1
        
        return merged
    
    def _estimate_pages(self, text: str) -> int:
        """Estimate number of pages in the document.
        
        Args:
            text: Document text
            
        Returns:
            Estimated page count
        """
        # Rough estimate: ~500 words per page, ~1.3 tokens per word
        tokens = len(self.encoding.encode(text))
        return max(1, tokens // 650)
    
    def extract_metadata(self, markdown_text: str, filename: str) -> Dict:
        """Extract metadata from document.
        
        Args:
            markdown_text: The markdown content
            filename: Original filename
            
        Returns:
            Dictionary containing document metadata
        """
        metadata = {
            "filename": filename,
            "state": self._extract_state_from_filename(filename),
            "document_date": self._extract_date(markdown_text),
            "total_pages": self._estimate_pages(markdown_text),
            "total_tokens": len(self.encoding.encode(markdown_text))
        }
        
        # Try to extract title
        title_match = re.search(r'^#\s+(.+)$', markdown_text, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        
        return metadata
    
    def _extract_state_from_filename(self, filename: str) -> Optional[str]:
        """Extract state abbreviation from filename.
        
        Args:
            filename: The filename
            
        Returns:
            State abbreviation or None
        """
        # Match state abbreviations (2 uppercase letters)
        match = re.search(r'([A-Z]{2})', Path(filename).stem)
        return match.group(1) if match else None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract document date from text.
        
        Args:
            text: Document text
            
        Returns:
            Date string or None
        """
        # Common date patterns
        date_patterns = [
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text[:5000])  # Check first part of doc
            if match:
                return match.group()
        
        return None