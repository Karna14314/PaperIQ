"""Section viewer component."""

import streamlit as st


def render_section_card(section_type: str, content: str, confidence: float, word_count: int, expanded: bool = False):
    """Render a section card with expandable content."""
    if confidence >= 0.8:
        badge_color = "#10b981"
    elif confidence >= 0.6:
        badge_color = "#f59e0b"
    else:
        badge_color = "#ef4444"
    
    st.markdown(f"""
    <div style="background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 1.1rem; font-weight: 600;">{section_type.capitalize()}</span>
            <span style="background-color: {badge_color}; color: white; padding: 0.2rem 0.6rem; 
                         border-radius: 9999px; font-size: 0.8rem;">{confidence:.0%}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander(f"Read more ({word_count} words)", expanded=expanded):
        st.markdown(content)


def render_section_summary(sections: list):
    """Render a summary of all sections."""
    st.markdown("### Section Overview")
    for section in sections:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**{section.section_type.value.capitalize()}**")
        with col2:
            st.markdown(f"{section.word_count} words")
        with col3:
            st.markdown(f"{section.confidence:.0%}")
