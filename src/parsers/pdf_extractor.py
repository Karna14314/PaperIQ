"""
PDF text extraction using PyMuPDF.

Extracts text with layout information including font sizes,
bold/italic formatting, and position coordinates.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple, Optional, Generator
from dataclasses import dataclass

from models import Paper, TextBlock, ProcessingStatus
from utils import Config, get_logger


logger = get_logger("paperiq.extractor")


@dataclass
class ExtractionResult:
    """Result of PDF text extraction."""
    success: bool
    full_text: str
    text_blocks: List[TextBlock]
    page_count: int
    title: str
    error: Optional[str] = None


class PDFExtractor:
    """
    PDF text extractor using PyMuPDF (fitz).
    
    Extracts text with full layout information for accurate
    section detection and content analysis.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize extractor with configuration.
        
        Args:
            config: Configuration instance (uses default if not provided)
        """
        self.config = config or Config()
    
    def extract(self, pdf_path: Path) -> ExtractionResult:
        """
        Extract text and layout information from a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExtractionResult with text, blocks, and metadata
        """
        if not pdf_path.exists():
            return ExtractionResult(
                success=False,
                full_text="",
                text_blocks=[],
                page_count=0,
                title="",
                error=f"File not found: {pdf_path}"
            )
        
        doc = None
        try:
            doc = fitz.open(pdf_path)
            
            if doc.is_encrypted:
                return ExtractionResult(
                    success=False,
                    full_text="",
                    text_blocks=[],
                    page_count=0,
                    title="",
                    error="PDF is encrypted/password protected"
                )
            
            page_count = len(doc)
            if page_count == 0:
                return ExtractionResult(
                    success=False,
                    full_text="",
                    text_blocks=[],
                    page_count=0,
                    title="",
                    error="PDF has no pages"
                )
            
            # Extract text blocks from all pages
            all_blocks: List[TextBlock] = []
            full_text_parts: List[str] = []
            
            for page_num in range(page_count):
                page = doc[page_num]
                page_blocks = self._extract_page_blocks(page, page_num + 1)
                all_blocks.extend(page_blocks)
                
                # Get plain text for full text
                page_text = page.get_text("text")
                if page_text:
                    full_text_parts.append(page_text)
            
            full_text = "\n".join(full_text_parts)
            
            # Extract title from first page (largest text)
            title = self._extract_title(doc[0]) if page_count > 0 else ""
            
            logger.info(
                f"Extracted {len(all_blocks)} text blocks from {page_count} pages"
            )
            
            return ExtractionResult(
                success=True,
                full_text=full_text,
                text_blocks=all_blocks,
                page_count=page_count,
                title=title
            )
            
        except fitz.FileDataError as e:
            return ExtractionResult(
                success=False,
                full_text="",
                text_blocks=[],
                page_count=0,
                title="",
                error=f"Invalid or corrupted PDF: {e}"
            )
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ExtractionResult(
                success=False,
                full_text="",
                text_blocks=[],
                page_count=0,
                title="",
                error=str(e)
            )
        finally:
            if doc is not None:
                doc.close()
    
    def _extract_page_blocks(
        self,
        page: fitz.Page,
        page_number: int
    ) -> List[TextBlock]:
        """
        Extract text blocks from a single page.
        
        Uses PyMuPDF's dict output to get detailed text information
        including font data and positioning.
        
        Args:
            page: PyMuPDF page object
            page_number: 1-indexed page number
            
        Returns:
            List of TextBlock objects
        """
        blocks: List[TextBlock] = []
        
        # Get text with detailed information
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:  # 0 = text block
                continue
            
            block_bbox = block.get("bbox", (0, 0, 0, 0))
            
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    
                    # Get font information
                    font_name = span.get("font", "")
                    font_size = span.get("size", 12.0)
                    flags = span.get("flags", 0)
                    
                    # Decode font flags
                    # Bit 0: Superscript
                    # Bit 1: Italic
                    # Bit 2: Serifed
                    # Bit 3: Monospaced
                    # Bit 4: Bold
                    is_bold = bool(flags & (1 << 4)) or "bold" in font_name.lower()
                    is_italic = bool(flags & (1 << 1)) or "italic" in font_name.lower()
                    
                    span_bbox = span.get("bbox", block_bbox)
                    
                    blocks.append(TextBlock(
                        text=text,
                        x0=span_bbox[0],
                        y0=span_bbox[1],
                        x1=span_bbox[2],
                        y1=span_bbox[3],
                        page_number=page_number,
                        font_size=font_size,
                        font_name=font_name,
                        is_bold=is_bold,
                        is_italic=is_italic,
                    ))
        
        return blocks
    
    def _extract_title(self, first_page: fitz.Page) -> str:
        """
        Extract paper title from first page.
        
        Uses heuristic: largest text in top half of first page.
        
        Args:
            first_page: First page of the PDF
            
        Returns:
            Extracted title string
        """
        page_height = first_page.rect.height
        top_half_cutoff = page_height / 2
        
        text_dict = first_page.get_text("dict")
        
        # Find largest text in top half
        candidates: List[Tuple[float, str]] = []
        
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            
            block_bbox = block.get("bbox", (0, 0, 0, 0))
            if block_bbox[1] > top_half_cutoff:  # Below top half
                continue
            
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    font_size = span.get("size", 12.0)
                    
                    if text and len(text) > 5:  # Minimum length
                        candidates.append((font_size, text))
        
        if not candidates:
            return ""
        
        # Sort by font size (descending) and get largest
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Get all text at the largest size (might be multi-line title)
        max_size = candidates[0][0]
        title_parts = [
            text for size, text in candidates
            if size >= max_size - 0.5  # Allow small tolerance
        ]
        
        # Combine and clean
        title = " ".join(title_parts)
        
        # Remove extra whitespace
        title = " ".join(title.split())
        
        return title[:500]  # Reasonable limit
    
    def get_page_count(self, pdf_path: Path) -> int:
        """
        Get page count without full extraction.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Number of pages, or 0 on error
        """
        doc = None
        try:
            doc = fitz.open(pdf_path)
            return len(doc)
        except Exception:
            return 0
        finally:
            if doc is not None:
                doc.close()
    
    def extract_page_text(self, pdf_path: Path, page_num: int) -> str:
        """
        Extract text from a specific page.
        
        Args:
            pdf_path: Path to PDF file
            page_num: 1-indexed page number
            
        Returns:
            Page text or empty string on error
        """
        doc = None
        try:
            doc = fitz.open(pdf_path)
            if page_num < 1 or page_num > len(doc):
                return ""
            return doc[page_num - 1].get_text("text")
        except Exception:
            return ""
        finally:
            if doc is not None:
                doc.close()
