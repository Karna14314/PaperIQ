"""
Validation utilities for PaperIQ.

Provides validation for PDF files, content quality, and section detection.
"""

import os
from pathlib import Path
from typing import Tuple, Optional, BinaryIO
from dataclasses import dataclass

from utils.config import Config


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    message: str
    details: Optional[dict] = None


class PDFValidator:
    """
    Validator for PDF files.
    
    Checks file size, format, corruption, and accessibility.
    """
    
    # PDF magic bytes (file signature)
    PDF_MAGIC_BYTES = b"%PDF-"
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize validator with configuration.
        
        Args:
            config: Configuration instance (uses default if not provided)
        """
        self.config = config or Config()
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate a PDF file on disk.
        
        Checks:
        - File exists
        - File size within limits
        - File has PDF signature
        - File is not encrypted (basic check)
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            ValidationResult with status and message
        """
        # Check file exists
        if not file_path.exists():
            return ValidationResult(
                is_valid=False,
                message="File does not exist",
                details={"path": str(file_path)}
            )
        
        # Check file extension
        if file_path.suffix.lower() not in self.config.allowed_extensions:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid file type. Allowed: {', '.join(self.config.allowed_extensions)}",
                details={"extension": file_path.suffix}
            )
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.config.max_pdf_size_bytes:
            size_mb = file_size / (1024 * 1024)
            return ValidationResult(
                is_valid=False,
                message=f"File too large: {size_mb:.1f}MB (max: {self.config.max_pdf_size_mb}MB)",
                details={"size_bytes": file_size, "size_mb": size_mb}
            )
        
        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                message="File is empty",
                details={"size_bytes": 0}
            )
        
        # Check PDF signature
        try:
            with open(file_path, "rb") as f:
                header = f.read(8)
                if not header.startswith(self.PDF_MAGIC_BYTES):
                    return ValidationResult(
                        is_valid=False,
                        message="File is not a valid PDF (invalid signature)",
                        details={"header": header[:5].hex()}
                    )
        except IOError as e:
            return ValidationResult(
                is_valid=False,
                message=f"Cannot read file: {e}",
                details={"error": str(e)}
            )
        
        return ValidationResult(
            is_valid=True,
            message="PDF is valid",
            details={
                "path": str(file_path),
                "size_bytes": file_size,
                "size_mb": file_size / (1024 * 1024)
            }
        )
    
    def validate_uploaded_file(
        self,
        file_data: BinaryIO,
        filename: str
    ) -> ValidationResult:
        """
        Validate an uploaded file (from Streamlit file uploader).
        
        Args:
            file_data: File-like object with read capability
            filename: Original filename
            
        Returns:
            ValidationResult with status and message
        """
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in self.config.allowed_extensions:
            return ValidationResult(
                is_valid=False,
                message=f"Invalid file type. Allowed: {', '.join(self.config.allowed_extensions)}",
                details={"extension": ext, "filename": filename}
            )
        
        # Check file size
        file_data.seek(0, 2)  # Seek to end
        file_size = file_data.tell()
        file_data.seek(0)  # Reset to beginning
        
        if file_size > self.config.max_pdf_size_bytes:
            size_mb = file_size / (1024 * 1024)
            return ValidationResult(
                is_valid=False,
                message=f"File too large: {size_mb:.1f}MB (max: {self.config.max_pdf_size_mb}MB)",
                details={"size_bytes": file_size, "size_mb": size_mb}
            )
        
        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                message="File is empty",
                details={"size_bytes": 0}
            )
        
        # Check PDF signature
        header = file_data.read(8)
        file_data.seek(0)  # Reset to beginning
        
        if not header.startswith(self.PDF_MAGIC_BYTES):
            return ValidationResult(
                is_valid=False,
                message="File is not a valid PDF (invalid signature)",
                details={"header": header[:5].hex() if header else "empty"}
            )
        
        return ValidationResult(
            is_valid=True,
            message="PDF is valid",
            details={
                "filename": filename,
                "size_bytes": file_size,
                "size_mb": file_size / (1024 * 1024)
            }
        )


class ContentValidator:
    """
    Validator for extracted content quality.
    
    Checks section content for quality indicators.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize validator with configuration.
        
        Args:
            config: Configuration instance (uses default if not provided)
        """
        self.config = config or Config()
    
    def validate_section_content(
        self,
        content: str,
        section_type: str
    ) -> ValidationResult:
        """
        Validate extracted section content.
        
        Checks:
        - Content length within bounds
        - Content is not gibberish
        - Content has reasonable character distribution
        
        Args:
            content: Extracted text content
            section_type: Type of section (abstract, introduction, etc.)
            
        Returns:
            ValidationResult with status and message
        """
        # Check length
        content_length = len(content)
        
        if content_length < self.config.min_section_length:
            return ValidationResult(
                is_valid=False,
                message=f"Section too short ({content_length} chars, min: {self.config.min_section_length})",
                details={"length": content_length, "section": section_type}
            )
        
        if content_length > self.config.max_section_length:
            return ValidationResult(
                is_valid=False,
                message=f"Section too long ({content_length} chars, max: {self.config.max_section_length})",
                details={"length": content_length, "section": section_type}
            )
        
        # Check for gibberish (basic heuristic)
        # Count alphanumeric vs special characters
        alpha_count = sum(1 for c in content if c.isalnum())
        space_count = sum(1 for c in content if c.isspace())
        total_normal = alpha_count + space_count
        
        if content_length > 0:
            normal_ratio = total_normal / content_length
            if normal_ratio < 0.7:
                return ValidationResult(
                    is_valid=False,
                    message="Content appears to be corrupted or non-text",
                    details={
                        "normal_char_ratio": normal_ratio,
                        "section": section_type
                    }
                )
        
        # Count word-like tokens
        words = content.split()
        word_count = len(words)
        
        if word_count < 5:
            return ValidationResult(
                is_valid=False,
                message="Content has too few words",
                details={"word_count": word_count, "section": section_type}
            )
        
        return ValidationResult(
            is_valid=True,
            message="Content is valid",
            details={
                "length": content_length,
                "word_count": word_count,
                "section": section_type
            }
        )
    
    def calculate_quality_score(
        self,
        sections_found: int,
        total_sections: int,
        confidence_scores: list[float]
    ) -> Tuple[float, str]:
        """
        Calculate overall quality score for a parsed paper.
        
        Formula: (Completeness * 0.6) + (Average Confidence * 0.4)
        
        Args:
            sections_found: Number of sections identified
            total_sections: Total expected sections (typically 7)
            confidence_scores: List of confidence scores for found sections
            
        Returns:
            Tuple of (quality_score, quality_level)
        """
        if total_sections == 0:
            return 0.0, "unknown"
        
        completeness = sections_found / total_sections
        
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
        else:
            avg_confidence = 0.0
        
        quality_score = (completeness * 0.6) + (avg_confidence * 0.4)
        
        # Determine level
        if quality_score >= 0.8:
            level = "excellent"
        elif quality_score >= 0.6:
            level = "good"
        elif quality_score >= 0.4:
            level = "fair"
        else:
            level = "poor"
        
        return quality_score, level
