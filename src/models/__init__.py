"""
Data models for PaperIQ.
"""

from models.paper_model import (
    Paper,
    Section,
    SectionType,
    ExtractedImage,
    ExtractedTable,
    TextBlock,
    ProcessingStatus,
    ValidationReport,
    ValidationItem,
)

__all__ = [
    "Paper",
    "Section",
    "SectionType",
    "ExtractedImage",
    "ExtractedTable",
    "TextBlock",
    "ProcessingStatus",
    "ValidationReport",
    "ValidationItem",
]
