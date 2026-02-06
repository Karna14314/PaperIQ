"""Validation report component."""

import streamlit as st


def render_validation_report(report, paper):
    """Render the validation report for a paper."""
    if not report:
        st.warning("No validation report available.")
        return
    
    render_quality_score(report.quality_score, report.quality_level)
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background-color: #d1fae5; border-radius: 8px;">
            <div style="font-size: 1.5rem; font-weight: bold; color: #065f46;">{report.pass_count}</div>
            <div style="color: #065f46;">Passed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background-color: #fef3c7; border-radius: 8px;">
            <div style="font-size: 1.5rem; font-weight: bold; color: #92400e;">{report.warning_count}</div>
            <div style="color: #92400e;">Warnings</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background-color: #fee2e2; border-radius: 8px;">
            <div style="font-size: 1.5rem; font-weight: bold; color: #991b1b;">{report.fail_count}</div>
            <div style="color: #991b1b;">Failed</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Validation Checklist")
    
    for item in report.items:
        render_validation_item(item)


def render_quality_score(score: float, level: str):
    """Render the quality score indicator."""
    colors = {
        "high": ("#10b981", "#d1fae5"),
        "medium": ("#f59e0b", "#fef3c7"),
        "low": ("#ef4444", "#fee2e2"),
        "none": ("#6b7280", "#f3f4f6"),
    }
    
    text_color, bg_color = colors.get(level, colors["none"])
    
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, {bg_color} 0%, white 100%); 
                border-radius: 12px; border: 2px solid {text_color};">
        <div style="font-size: 3rem; font-weight: bold; color: {text_color};">{score:.0%}</div>
        <div style="font-size: 1.2rem; color: {text_color}; text-transform: uppercase;">{level} Quality</div>
    </div>
    """, unsafe_allow_html=True)


def render_validation_item(item):
    """Render a single validation item."""
    styles = {
        "pass": {"bg": "#d1fae5", "border": "#10b981", "text": "#065f46", "icon": "[PASS]"},
        "warning": {"bg": "#fef3c7", "border": "#f59e0b", "text": "#92400e", "icon": "[WARN]"},
        "fail": {"bg": "#fee2e2", "border": "#ef4444", "text": "#991b1b", "icon": "[FAIL]"},
    }
    
    style = styles.get(item.status, styles["warning"])
    
    st.markdown(f"""
    <div style="background-color: {style['bg']}; border-left: 4px solid {style['border']}; 
                padding: 0.75rem 1rem; margin-bottom: 0.5rem; border-radius: 0 6px 6px 0;">
        <div style="color: {style['text']}; font-weight: 600;">{style['icon']} {item.name}</div>
        <div style="color: {style['text']}; opacity: 0.8; font-size: 0.9rem;">{item.message}</div>
    </div>
    """, unsafe_allow_html=True)
