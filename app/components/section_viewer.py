"""
Section viewer component.
"""

import streamlit as st
from typing import Optional


def render_section_card(
    section_type: str,
    content: str,
    confidence: float,
    word_count: int,
    expanded: bool = False
) -> None:
    """
    Render a section card with expandable content.
    
    Args:
        section_type: Type of section (abstract, introduction, etc.)
        content: Section text content
        confidence: Confidence score (0-1)
        word_count: Number of words in section
        expanded: Whether to show expanded by default
    """
    # Section icons
    icons = {
        "abstract": "📝",
        "introduction": "📖",
        "methodology": "⚙️",
        "results": "📈",
        "discussion": "💬",
        "conclusion": "🎯",
        "references": "📚",
    }
    
    icon = icons.get(section_type.lower(), "📄")
    
    # Confidence badge
    if confidence >= 0.8:
        badge_color = "#10b981"
        badge_text = f"{confidence:.0%} ✓"
    elif confidence >= 0.6:
        badge_color = "#f59e0b"
        badge_text = f"{confidence:.0%} ⚠"
    else:
        badge_color = "#ef4444"
        badge_text = f"{confidence:.0%} !"
    
    # Card HTML
    st.markdown(f"""
    <div style="
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.1rem; font-weight: 600;">
                {icon} {section_type.capitalize()}
            </span>
            <span style="
                background-color: {badge_color};
                color: white;
                padding: 0.2rem 0.6rem;
                border-radius: 9999px;
                font-size: 0.8rem;
            ">{badge_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Expandable content
    preview = content[:300] + "..." if len(content) > 300 else content
    
    with st.expander(f"Read more ({word_count} words)", expanded=expanded):
        st.markdown(content)


def render_section_summary(sections: list) -> None:
    """
    Render a summary of all sections.
    
    Args:
        sections: List of section objects
    """
    st.markdown("### Section Overview")
    
    for section in sections:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**{section.section_type.value.capitalize()}**")
        with col2:
            st.markdown(f"{section.word_count} words")
        with col3:
            st.markdown(f"{section.confidence:.0%}")
