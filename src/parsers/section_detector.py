"""
Section detection for research papers.

Identifies and extracts standard research paper sections using
pattern matching and layout analysis with confidence scoring.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from models import Section, SectionType, TextBlock
from utils import Config, get_logger
from parsers.text_cleaner import TextCleaner


logger = get_logger("paperiq.sections")


@dataclass
class SectionMatch:
    """Represents a potential section header match."""
    section_type: SectionType
    header_text: str
    position: int  # Character position in text
    confidence: float
    method: str  # 'pattern', 'layout', 'combined'
    font_size: float = 0.0
    is_bold: bool = False


class SectionDetector:
    """
    Detects and extracts sections from research paper text.
    
    Uses a two-phase approach:
    1. Pattern matching for section headers
    2. Layout analysis (font size, bold) for confirmation
    
    Combines both methods for confidence scoring.
    """
    
    # Section header patterns (case-insensitive)
    SECTION_PATTERNS: Dict[SectionType, List[str]] = {
        SectionType.ABSTRACT: [
            r"^abstract\s*$",
            r"^summary\s*$",
            r"^synopsis\s*$",
        ],
        SectionType.INTRODUCTION: [
            r"^(?:\d+\.?\s*)?introduction\s*$",
            r"^(?:I\.?\s*)?introduction\s*$",
            r"^1\s+introduction\s*$",
            r"^background\s*$",
        ],
        SectionType.METHODOLOGY: [
            r"^(?:\d+\.?\s*)?(?:materials?\s+and\s+)?methods?\s*$",
            r"^(?:\d+\.?\s*)?methodology\s*$",
            r"^(?:\d+\.?\s*)?experimental\s+(?:setup|design|methods?)\s*$",
            r"^(?:\d+\.?\s*)?approach\s*$",
            r"^(?:\d+\.?\s*)?proposed\s+(?:method|approach|system)\s*$",
            r"^(?:II\.?\s*)?methods?\s*$",
            r"^(?:III\.?\s*)?methods?\s*$",
        ],
        SectionType.RESULTS: [
            r"^(?:\d+\.?\s*)?results?\s*$",
            r"^(?:\d+\.?\s*)?experiments?\s*$",
            r"^(?:\d+\.?\s*)?experimental\s+results?\s*$",
            r"^(?:\d+\.?\s*)?findings\s*$",
            r"^(?:\d+\.?\s*)?evaluation\s*$",
            r"^(?:III\.?\s*)?results?\s*$",
            r"^(?:IV\.?\s*)?results?\s*$",
        ],
        SectionType.DISCUSSION: [
            r"^(?:\d+\.?\s*)?discussion\s*$",
            r"^(?:\d+\.?\s*)?analysis\s*$",
            r"^(?:\d+\.?\s*)?discussion\s+and\s+(?:analysis|implications)\s*$",
            r"^(?:IV\.?\s*)?discussion\s*$",
            r"^(?:V\.?\s*)?discussion\s*$",
        ],
        SectionType.CONCLUSION: [
            r"^(?:\d+\.?\s*)?conclusions?\s*$",
            r"^(?:\d+\.?\s*)?concluding\s+remarks?\s*$",
            r"^(?:\d+\.?\s*)?summary\s+and\s+conclusions?\s*$",
            r"^(?:\d+\.?\s*)?future\s+work\s*$",
            r"^(?:V\.?\s*)?conclusions?\s*$",
            r"^(?:VI\.?\s*)?conclusions?\s*$",
        ],
        SectionType.REFERENCES: [
            r"^references\s*$",
            r"^bibliography\s*$",
            r"^works?\s+cited\s*$",
            r"^literature\s+cited\s*$",
        ],
    }
    
    # Minimum font size ratio to consider as header
    HEADER_FONT_RATIO = 1.2
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize section detector with configuration.
        
        Args:
            config: Configuration instance (uses default if not provided)
        """
        self.config = config or Config()
        self.text_cleaner = TextCleaner(remove_citations=True)
        
        # Compile regex patterns
        self._compiled_patterns: Dict[SectionType, List[re.Pattern]] = {}
        for section_type, patterns in self.SECTION_PATTERNS.items():
            self._compiled_patterns[section_type] = [
                re.compile(p, re.IGNORECASE | re.MULTILINE)
                for p in patterns
            ]
    
    def detect_sections(
        self,
        full_text: str,
        text_blocks: Optional[List[TextBlock]] = None
    ) -> List[Section]:
        """
        Detect and extract all sections from paper text.
        
        Args:
            full_text: Complete extracted text
            text_blocks: Optional list of TextBlocks with layout info
            
        Returns:
            List of detected Section objects
        """
        if not full_text:
            return []
        
        # Find section headers
        matches = self._find_section_headers(full_text, text_blocks)
        
        if not matches:
            logger.warning("No section headers found in document")
            return []
        
        # Sort by position
        matches.sort(key=lambda m: m.position)
        
        # Extract section content
        sections = self._extract_section_content(full_text, matches)
        
        # Log results
        for section in sections:
            logger.info(
                f"  - {section.section_type.value.capitalize()}: "
                f"Found (confidence: {section.confidence:.2f})"
            )
        
        return sections
    
    def _find_section_headers(
        self,
        text: str,
        text_blocks: Optional[List[TextBlock]] = None
    ) -> List[SectionMatch]:
        """
        Find all potential section headers in text.
        
        Combines pattern matching with layout analysis.
        
        Args:
            text: Full text to search
            text_blocks: Optional layout information
            
        Returns:
            List of SectionMatch objects
        """
        matches: List[SectionMatch] = []
        
        # Phase 1: Pattern matching
        pattern_matches = self._pattern_match(text)
        
        # Phase 2: Layout analysis (if text blocks available)
        layout_matches = []
        if text_blocks:
            layout_matches = self._layout_analysis(text, text_blocks)
        
        # Combine matches
        matches = self._combine_matches(pattern_matches, layout_matches)
        
        # Remove duplicates (same section type close together)
        matches = self._deduplicate_matches(matches)
        
        return matches
    
    def _pattern_match(self, text: str) -> List[SectionMatch]:
        """
        Find sections using regex pattern matching.
        
        Args:
            text: Text to search
            
        Returns:
            List of SectionMatch objects
        """
        matches: List[SectionMatch] = []
        lines = text.split("\n")
        
        char_position = 0
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                char_position += len(line) + 1
                continue
            
            # Check against all patterns
            for section_type, patterns in self._compiled_patterns.items():
                for pattern in patterns:
                    if pattern.match(line_stripped):
                        matches.append(SectionMatch(
                            section_type=section_type,
                            header_text=line_stripped,
                            position=char_position,
                            confidence=0.7,  # Base pattern match confidence
                            method="pattern",
                        ))
                        break
            
            char_position += len(line) + 1
        
        return matches
    
    def _layout_analysis(
        self,
        text: str,
        text_blocks: List[TextBlock]
    ) -> List[SectionMatch]:
        """
        Find potential headers using layout analysis.
        
        Looks for text with larger font size and/or bold formatting.
        
        Args:
            text: Full text
            text_blocks: TextBlocks with layout info
            
        Returns:
            List of SectionMatch objects
        """
        matches: List[SectionMatch] = []
        
        if not text_blocks:
            return matches
        
        # Calculate average font size
        font_sizes = [b.font_size for b in text_blocks if b.font_size > 0]
        if not font_sizes:
            return matches
        
        avg_font_size = sum(font_sizes) / len(font_sizes)
        header_threshold = avg_font_size * self.HEADER_FONT_RATIO
        
        # Find blocks that look like headers
        for block in text_blocks:
            block_text = block.text.strip()
            
            # Skip long text (headers are usually short)
            if len(block_text) > 100:
                continue
            
            # Skip if not potentially a header based on layout
            is_large_font = block.font_size >= header_threshold
            if not (is_large_font or block.is_bold):
                continue
            
            # Try to match to a section type
            section_type = self._match_text_to_section(block_text)
            if section_type:
                # Find position in text
                position = text.lower().find(block_text.lower())
                if position == -1:
                    continue
                
                # Calculate confidence based on layout features
                confidence = 0.5  # Base layout confidence
                if is_large_font:
                    confidence += 0.2
                if block.is_bold:
                    confidence += 0.15
                
                matches.append(SectionMatch(
                    section_type=section_type,
                    header_text=block_text,
                    position=position,
                    confidence=confidence,
                    method="layout",
                    font_size=block.font_size,
                    is_bold=block.is_bold,
                ))
        
        return matches
    
    def _match_text_to_section(self, text: str) -> Optional[SectionType]:
        """
        Try to match text to a section type.
        
        More lenient than full pattern matching.
        
        Args:
            text: Text to match
            
        Returns:
            SectionType or None
        """
        text_lower = text.lower().strip()
        
        # Simple keyword matching
        keyword_map = {
            "abstract": SectionType.ABSTRACT,
            "introduction": SectionType.INTRODUCTION,
            "methodology": SectionType.METHODOLOGY,
            "methods": SectionType.METHODOLOGY,
            "materials and methods": SectionType.METHODOLOGY,
            "experimental setup": SectionType.METHODOLOGY,
            "results": SectionType.RESULTS,
            "experiments": SectionType.RESULTS,
            "experimental results": SectionType.RESULTS,
            "discussion": SectionType.DISCUSSION,
            "analysis": SectionType.DISCUSSION,
            "conclusion": SectionType.CONCLUSION,
            "conclusions": SectionType.CONCLUSION,
            "concluding remarks": SectionType.CONCLUSION,
            "references": SectionType.REFERENCES,
            "bibliography": SectionType.REFERENCES,
        }
        
        for keyword, section_type in keyword_map.items():
            if keyword in text_lower:
                return section_type
        
        return None
    
    def _combine_matches(
        self,
        pattern_matches: List[SectionMatch],
        layout_matches: List[SectionMatch]
    ) -> List[SectionMatch]:
        """
        Combine pattern and layout matches with adjusted confidence.
        
        If both methods agree, confidence is boosted significantly.
        
        Args:
            pattern_matches: Matches from pattern matching
            layout_matches: Matches from layout analysis
            
        Returns:
            Combined list of matches
        """
        combined: List[SectionMatch] = []
        used_layout = set()
        
        for pm in pattern_matches:
            # Look for corresponding layout match
            best_layout = None
            best_distance = float("inf")
            
            for i, lm in enumerate(layout_matches):
                if lm.section_type == pm.section_type:
                    distance = abs(pm.position - lm.position)
                    if distance < best_distance and distance < 500:  # Within 500 chars
                        best_distance = distance
                        best_layout = (i, lm)
            
            if best_layout is not None:
                # Combined match - boost confidence
                idx, lm = best_layout
                used_layout.add(idx)
                
                confidence = min(0.95, pm.confidence + lm.confidence - 0.2)
                
                combined.append(SectionMatch(
                    section_type=pm.section_type,
                    header_text=pm.header_text,
                    position=pm.position,
                    confidence=confidence,
                    method="combined",
                    font_size=lm.font_size,
                    is_bold=lm.is_bold,
                ))
            else:
                combined.append(pm)
        
        # Add remaining layout matches not paired
        for i, lm in enumerate(layout_matches):
            if i not in used_layout:
                combined.append(lm)
        
        return combined
    
    def _deduplicate_matches(
        self,
        matches: List[SectionMatch]
    ) -> List[SectionMatch]:
        """
        Remove duplicate matches for the same section type.
        
        Keeps the match with highest confidence for each section type.
        
        Args:
            matches: List of matches to deduplicate
            
        Returns:
            Deduplicated list
        """
        best_matches: Dict[SectionType, SectionMatch] = {}
        
        for match in matches:
            existing = best_matches.get(match.section_type)
            if existing is None or match.confidence > existing.confidence:
                best_matches[match.section_type] = match
        
        return list(best_matches.values())
    
    def _extract_section_content(
        self,
        text: str,
        matches: List[SectionMatch]
    ) -> List[Section]:
        """
        Extract the content for each detected section.
        
        Content extends from header to the next section header.
        
        Args:
            text: Full text
            matches: Detected section headers
            
        Returns:
            List of Section objects with content
        """
        sections: List[Section] = []
        
        # Sort by position
        sorted_matches = sorted(matches, key=lambda m: m.position)
        
        for i, match in enumerate(sorted_matches):
            # Start position (after header)
            start_pos = match.position
            header_end = text.find("\n", start_pos)
            if header_end == -1:
                header_end = start_pos + len(match.header_text)
            
            content_start = header_end + 1
            
            # End position (start of next section or end of text)
            if i + 1 < len(sorted_matches):
                end_pos = sorted_matches[i + 1].position
            else:
                end_pos = len(text)
            
            # Extract and clean content
            content = text[content_start:end_pos]
            content = self.text_cleaner.clean_section(content)
            
            # Skip if content is too short
            if len(content) < self.config.min_section_length:
                continue
            
            sections.append(Section(
                section_type=match.section_type,
                content=content,
                confidence=match.confidence,
                start_position=content_start,
                end_position=end_pos,
            ))
        
        return sections
    
    def get_missing_sections(
        self,
        found_sections: List[Section]
    ) -> List[SectionType]:
        """
        Get list of expected sections that were not found.
        
        Args:
            found_sections: List of detected sections
            
        Returns:
            List of missing SectionType values
        """
        found_types = {s.section_type for s in found_sections}
        expected = set(SectionType.all_expected())
        
        return list(expected - found_types)
    
    def calculate_detection_quality(
        self,
        found_sections: List[Section]
    ) -> Tuple[float, str]:
        """
        Calculate overall detection quality score.
        
        Args:
            found_sections: List of detected sections
            
        Returns:
            Tuple of (score, level) where level is 'high', 'medium', or 'low'
        """
        if not found_sections:
            return 0.0, "none"
        
        # Count sections found
        total_possible = len(SectionType.all_expected())
        sections_found = len(found_sections)
        
        # Average confidence
        avg_confidence = sum(s.confidence for s in found_sections) / len(found_sections)
        
        # Combined score
        completeness = sections_found / total_possible
        score = (completeness * 0.6) + (avg_confidence * 0.4)
        
        # Determine level
        if score >= 0.75:
            level = "high"
        elif score >= 0.5:
            level = "medium"
        else:
            level = "low"
        
        return score, level
