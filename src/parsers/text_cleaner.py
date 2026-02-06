"""
Text cleaning and preprocessing utilities.

Cleans extracted text by removing artifacts, fixing formatting issues,
and normalizing whitespace.
"""

import re
from typing import List, Optional


class TextCleaner:
    """
    Text preprocessing and cleaning for extracted PDF text.
    
    Handles common issues like:
    - Hyphenated line breaks
    - Inline citations
    - Extra whitespace
    - Encoding issues
    """
    
    # Regex patterns for cleaning
    PATTERNS = {
        # Inline citations: [1], [12], [1,2,3], [Author et al., 2020]
        "inline_citation_numeric": re.compile(r"\[\d+(?:,\s*\d+)*\]"),
        "inline_citation_author": re.compile(
            r"\[[A-Z][a-zA-Z]*(?:\s+et\s+al\.?)?,?\s*\d{4}[a-z]?\]"
        ),
        "inline_citation_parenthetical": re.compile(
            r"\([A-Z][a-zA-Z]*(?:\s+et\s+al\.?)?,?\s*\d{4}[a-z]?\)"
        ),
        
        # Hyphenated line breaks: word-\nword
        "hyphen_break": re.compile(r"(\w+)-\n(\w+)"),
        
        # Multiple spaces
        "multi_space": re.compile(r"[ \t]+"),
        
        # Multiple newlines
        "multi_newline": re.compile(r"\n{3,}"),
        
        # Page numbers on their own line
        "page_number": re.compile(r"^\s*\d+\s*$", re.MULTILINE),
        
        # Common header/footer patterns
        "header_footer": re.compile(
            r"^\s*(Page\s+\d+|©\s*\d{4}|All rights reserved|Preprint|Draft)\s*$",
            re.MULTILINE | re.IGNORECASE
        ),
        
        # Figure/Table references: "Figure 1", "Table 2", etc.
        "figure_ref": re.compile(r"Fig(?:ure|\.)\s*\d+[a-z]?", re.IGNORECASE),
        "table_ref": re.compile(r"Table\s*\d+[a-z]?", re.IGNORECASE),
    }
    
    def __init__(self, remove_citations: bool = False):
        """
        Initialize text cleaner.
        
        Args:
            remove_citations: Whether to remove inline citations
        """
        self.remove_citations = remove_citations
    
    def clean(self, text: str) -> str:
        """
        Apply all cleaning operations to text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Fix hyphenated line breaks first
        text = self.fix_hyphenated_breaks(text)
        
        # Remove citations if requested
        if self.remove_citations:
            text = self.remove_inline_citations(text)
        
        # Clean up whitespace
        text = self.normalize_whitespace(text)
        
        # Remove page numbers and headers/footers
        text = self.remove_page_artifacts(text)
        
        # Fix encoding issues
        text = self.fix_encoding(text)
        
        return text.strip()
    
    def clean_section(self, text: str) -> str:
        """
        Clean text for a specific section.
        
        More aggressive cleaning than general clean().
        
        Args:
            text: Section text to clean
            
        Returns:
            Cleaned section text
        """
        if not text:
            return ""
        
        # Apply general cleaning
        text = self.clean(text)
        
        # Additional section-specific cleaning
        # Remove standalone numbers that might be figure/table numbers
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip lines that are just numbers
            if line.isdigit():
                continue
            
            # Skip very short lines that look like artifacts
            if len(line) < 3 and not line.isalpha():
                continue
            
            cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)
    
    def fix_hyphenated_breaks(self, text: str) -> str:
        """
        Fix words split across lines with hyphens.
        
        Example: "computa-\\ntion" -> "computation"
        
        Args:
            text: Text with potential hyphenated breaks
            
        Returns:
            Text with breaks fixed
        """
        # Replace hyphen at end of line followed by word
        return self.PATTERNS["hyphen_break"].sub(r"\1\2", text)
    
    def remove_inline_citations(self, text: str) -> str:
        """
        Remove inline citation markers.
        
        Handles [1], [12, 15], [Author et al., 2020] formats.
        
        Args:
            text: Text with citations
            
        Returns:
            Text without citations
        """
        # Remove numeric citations
        text = self.PATTERNS["inline_citation_numeric"].sub("", text)
        
        # Remove author citations in brackets
        text = self.PATTERNS["inline_citation_author"].sub("", text)
        
        # Remove author citations in parentheses
        text = self.PATTERNS["inline_citation_parenthetical"].sub("", text)
        
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        - Multiple spaces -> single space
        - Multiple newlines -> double newline (paragraph break)
        - Trim lines
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Replace multiple spaces with single space
        text = self.PATTERNS["multi_space"].sub(" ", text)
        
        # Replace 3+ newlines with double newline
        text = self.PATTERNS["multi_newline"].sub("\n\n", text)
        
        # Trim each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)
        
        return text
    
    def remove_page_artifacts(self, text: str) -> str:
        """
        Remove page numbers and common headers/footers.
        
        Args:
            text: Text with potential artifacts
            
        Returns:
            Text without artifacts
        """
        # Remove standalone page numbers
        text = self.PATTERNS["page_number"].sub("", text)
        
        # Remove common header/footer patterns
        text = self.PATTERNS["header_footer"].sub("", text)
        
        return text
    
    def fix_encoding(self, text: str) -> str:
        """
        Fix common encoding issues.
        
        Args:
            text: Text with potential encoding issues
            
        Returns:
            Text with fixed encoding
        """
        # Common substitutions
        replacements = {
            "\u2018": "'",   # Left single quote
            "\u2019": "'",   # Right single quote
            "\u201c": '"',   # Left double quote
            "\u201d": '"',   # Right double quote
            "\u2013": "-",   # En dash
            "\u2014": "-",   # Em dash
            "\u2026": "...", # Ellipsis
            "\u00a0": " ",   # Non-breaking space
            "\ufeff": "",    # BOM
            "\u200b": "",    # Zero-width space
            "ﬁ": "fi",       # fi ligature
            "ﬂ": "fl",       # fl ligature
            "ﬀ": "ff",       # ff ligature
            "ﬃ": "ffi",      # ffi ligature
            "ﬄ": "ffl",      # ffl ligature
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def extract_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting on . ! ?
        # Handles common abbreviations
        
        # Protect common abbreviations
        protected = text
        abbreviations = ["Dr.", "Mr.", "Mrs.", "Ms.", "Prof.", "et al.", "i.e.", "e.g.", "vs.", "Fig.", "Eq."]
        
        for abbr in abbreviations:
            protected = protected.replace(abbr, abbr.replace(".", "<<DOT>>"))
        
        # Split on sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', protected)
        
        # Restore abbreviations
        sentences = [s.replace("<<DOT>>", ".") for s in sentences]
        
        # Filter empty sentences
        return [s.strip() for s in sentences if s.strip()]
    
    def get_word_count(self, text: str) -> int:
        """
        Count words in text.
        
        Args:
            text: Text to count
            
        Returns:
            Number of words
        """
        return len(text.split())
    
    def get_character_count(self, text: str, include_spaces: bool = False) -> int:
        """
        Count characters in text.
        
        Args:
            text: Text to count
            include_spaces: Whether to include whitespace
            
        Returns:
            Number of characters
        """
        if include_spaces:
            return len(text)
        return len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
