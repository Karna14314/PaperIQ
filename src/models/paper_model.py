"""
Data models for research paper representation.

Defines data classes for papers, sections, images, tables, and validation.
Uses Python dataclasses for clean, type-safe data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any


class ProcessingStatus(Enum):
    """Status of paper processing."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SectionType(Enum):
    """Standard research paper section types."""
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODOLOGY = "methodology"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_string(cls, value: str) -> "SectionType":
        """
        Convert string to SectionType.
        
        Args:
            value: Section type string
            
        Returns:
            Matching SectionType or UNKNOWN
        """
        value_lower = value.lower().strip()
        for section_type in cls:
            if section_type.value == value_lower:
                return section_type
        return cls.UNKNOWN
    
    @classmethod
    def all_expected(cls) -> List["SectionType"]:
        """Get list of all expected sections (excluding UNKNOWN)."""
        return [s for s in cls if s != cls.UNKNOWN]


@dataclass
class TextBlock:
    """
    A block of text with layout information.
    
    Represents a text element extracted from PDF with position,
    font, and formatting information.
    """
    text: str
    x0: float  # Left coordinate
    y0: float  # Top coordinate
    x1: float  # Right coordinate
    y1: float  # Bottom coordinate
    page_number: int
    font_size: float = 12.0
    font_name: str = ""
    is_bold: bool = False
    is_italic: bool = False
    
    @property
    def width(self) -> float:
        """Width of the text block."""
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        """Height of the text block."""
        return self.y1 - self.y0
    
    @property
    def center_x(self) -> float:
        """Horizontal center of the block."""
        return (self.x0 + self.x1) / 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "text": self.text,
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
            "page_number": self.page_number,
            "font_size": self.font_size,
            "font_name": self.font_name,
            "is_bold": self.is_bold,
            "is_italic": self.is_italic,
        }


@dataclass
class Section:
    """
    A section of a research paper.
    
    Contains the section content, type, and extraction metadata.
    """
    id: Optional[int] = None
    paper_id: Optional[int] = None
    section_type: SectionType = SectionType.UNKNOWN
    content: str = ""
    confidence: float = 0.0
    start_position: int = 0  # Character position in full text
    end_position: int = 0
    word_count: int = 0
    
    def __post_init__(self):
        """Calculate word count if not provided."""
        if self.word_count == 0 and self.content:
            self.word_count = len(self.content.split())
    
    @property
    def confidence_level(self) -> str:
        """Get human-readable confidence level."""
        if self.confidence >= 0.8:
            return "high"
        elif self.confidence >= 0.6:
            return "medium"
        elif self.confidence >= 0.5:
            return "low"
        else:
            return "very_low"
    
    @property
    def preview(self) -> str:
        """Get a short preview of the content (first 200 chars)."""
        if len(self.content) <= 200:
            return self.content
        return self.content[:197] + "..."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "section_type": self.section_type.value,
            "content": self.content,
            "confidence": self.confidence,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "word_count": self.word_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Section":
        """Create Section from dictionary."""
        return cls(
            id=data.get("id"),
            paper_id=data.get("paper_id"),
            section_type=SectionType.from_string(data.get("section_type", "unknown")),
            content=data.get("content", ""),
            confidence=data.get("confidence", 0.0),
            start_position=data.get("start_position", 0),
            end_position=data.get("end_position", 0),
            word_count=data.get("word_count", 0),
        )


@dataclass
class ExtractedImage:
    """
    An image extracted from a research paper.
    
    Contains metadata about the image and its location.
    """
    id: Optional[int] = None
    paper_id: Optional[int] = None
    file_path: str = ""
    page_number: int = 0
    width: int = 0
    height: int = 0
    format: str = "PNG"
    
    @property
    def dimensions(self) -> str:
        """Get dimensions as string."""
        return f"{self.width}x{self.height}"
    
    @property
    def filename(self) -> str:
        """Get just the filename from the path."""
        return Path(self.file_path).name if self.file_path else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "file_path": self.file_path,
            "page_number": self.page_number,
            "width": self.width,
            "height": self.height,
            "format": self.format,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedImage":
        """Create ExtractedImage from dictionary."""
        return cls(
            id=data.get("id"),
            paper_id=data.get("paper_id"),
            file_path=data.get("file_path", ""),
            page_number=data.get("page_number", 0),
            width=data.get("width", 0),
            height=data.get("height", 0),
            format=data.get("format", "PNG"),
        )


@dataclass
class ExtractedTable:
    """
    A table extracted from a research paper.
    
    Contains metadata about the table and path to CSV file.
    """
    id: Optional[int] = None
    paper_id: Optional[int] = None
    file_path: str = ""
    page_number: int = 0
    row_count: int = 0
    column_count: int = 0
    preview: str = ""  # First few rows as text
    
    @property
    def dimensions(self) -> str:
        """Get dimensions as string."""
        return f"{self.row_count} rows × {self.column_count} cols"
    
    @property
    def filename(self) -> str:
        """Get just the filename from the path."""
        return Path(self.file_path).name if self.file_path else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "file_path": self.file_path,
            "page_number": self.page_number,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "preview": self.preview,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedTable":
        """Create ExtractedTable from dictionary."""
        return cls(
            id=data.get("id"),
            paper_id=data.get("paper_id"),
            file_path=data.get("file_path", ""),
            page_number=data.get("page_number", 0),
            row_count=data.get("row_count", 0),
            column_count=data.get("column_count", 0),
            preview=data.get("preview", ""),
        )


@dataclass
class ValidationItem:
    """Single validation check result."""
    name: str
    status: str  # 'pass', 'warning', 'fail'
    message: str
    
    @property
    def icon(self) -> str:
        """Get status icon."""
        icons = {
            "pass": "✅",
            "warning": "⚠️",
            "fail": "❌",
        }
        return icons.get(self.status, "❓")


@dataclass
class ValidationReport:
    """
    Validation report for a parsed paper.
    
    Contains quality checks and overall assessment.
    """
    items: List[ValidationItem] = field(default_factory=list)
    quality_score: float = 0.0
    quality_level: str = "unknown"
    
    @property
    def pass_count(self) -> int:
        """Number of passed checks."""
        return sum(1 for item in self.items if item.status == "pass")
    
    @property
    def warning_count(self) -> int:
        """Number of warnings."""
        return sum(1 for item in self.items if item.status == "warning")
    
    @property
    def fail_count(self) -> int:
        """Number of failed checks."""
        return sum(1 for item in self.items if item.status == "fail")
    
    def add_check(self, name: str, status: str, message: str) -> None:
        """Add a validation check result."""
        self.items.append(ValidationItem(name=name, status=status, message=message))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "items": [
                {"name": i.name, "status": i.status, "message": i.message}
                for i in self.items
            ],
            "quality_score": self.quality_score,
            "quality_level": self.quality_level,
            "pass_count": self.pass_count,
            "warning_count": self.warning_count,
            "fail_count": self.fail_count,
        }


@dataclass
class Paper:
    """
    Complete research paper representation.
    
    Contains all metadata and extracted content from a paper.
    """
    id: Optional[int] = None
    filename: str = ""
    title: str = ""
    upload_date: Optional[datetime] = None
    page_count: int = 0
    file_size_bytes: int = 0
    status: ProcessingStatus = ProcessingStatus.UPLOADED
    file_path: str = ""
    
    # Extracted content
    sections: List[Section] = field(default_factory=list)
    images: List[ExtractedImage] = field(default_factory=list)
    tables: List[ExtractedTable] = field(default_factory=list)
    
    # Full text (before section splitting)
    full_text: str = ""
    
    # Validation
    validation_report: Optional[ValidationReport] = None
    
    def __post_init__(self):
        """Set upload date if not provided."""
        if self.upload_date is None:
            self.upload_date = datetime.now()
    
    @property
    def file_size_mb(self) -> float:
        """File size in megabytes."""
        return self.file_size_bytes / (1024 * 1024)
    
    @property
    def section_count(self) -> int:
        """Number of identified sections."""
        return len(self.sections)
    
    @property
    def image_count(self) -> int:
        """Number of extracted images."""
        return len(self.images)
    
    @property
    def table_count(self) -> int:
        """Number of extracted tables."""
        return len(self.tables)
    
    @property
    def quality_score(self) -> float:
        """Get quality score from validation report."""
        if self.validation_report:
            return self.validation_report.quality_score
        return 0.0
    
    def get_section(self, section_type: SectionType) -> Optional[Section]:
        """
        Get a specific section by type.
        
        Args:
            section_type: Type of section to find
            
        Returns:
            Section if found, None otherwise
        """
        for section in self.sections:
            if section.section_type == section_type:
                return section
        return None
    
    def get_sections_by_confidence(
        self,
        min_confidence: float = 0.0
    ) -> List[Section]:
        """
        Get sections filtered by minimum confidence.
        
        Args:
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of sections meeting threshold
        """
        return [s for s in self.sections if s.confidence >= min_confidence]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "id": self.id,
            "filename": self.filename,
            "title": self.title,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "page_count": self.page_count,
            "file_size_bytes": self.file_size_bytes,
            "status": self.status.value,
            "file_path": self.file_path,
            "section_count": self.section_count,
            "image_count": self.image_count,
            "table_count": self.table_count,
            "quality_score": self.quality_score,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Paper":
        """Create Paper from dictionary (basic fields only)."""
        upload_date = None
        if data.get("upload_date"):
            try:
                upload_date = datetime.fromisoformat(data["upload_date"])
            except (ValueError, TypeError):
                upload_date = datetime.now()
        
        return cls(
            id=data.get("id"),
            filename=data.get("filename", ""),
            title=data.get("title", ""),
            upload_date=upload_date,
            page_count=data.get("page_count", 0),
            file_size_bytes=data.get("file_size_bytes", 0),
            status=ProcessingStatus(data.get("status", "uploaded")),
            file_path=data.get("file_path", ""),
        )
