"""
PaperIQ - Main Streamlit Application
Research Paper Insight Analyzer - Milestone 1
"""

import streamlit as st
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from utils import Config

config = Config()

st.set_page_config(
    page_title=config.streamlit_page_title,
    page_icon="docs",
    layout=config.streamlit_layout,
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main { padding: 1rem; }
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1f2937; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #6b7280; margin-bottom: 2rem; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""
    st.markdown('<p class="main-header">PaperIQ</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Research Paper Insight Analyzer - Upload and analyze research papers with AI-powered section detection</p>',
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Welcome to PaperIQ")
        st.markdown("""
        PaperIQ helps you extract and analyze research papers automatically:
        
        - **Upload PDFs** - Upload research papers in PDF format
        - **Section Detection** - Automatically identify Abstract, Introduction, Methods, Results, Discussion, Conclusion, and References
        - **Image Extraction** - Extract all figures and diagrams
        - **Table Extraction** - Extract tables and convert to CSV
        - **Quality Validation** - Get confidence scores and quality reports
        """)
        
        st.markdown("---")
        st.info("Use the sidebar to navigate to the Upload page to get started.")
    
    with col2:
        try:
            from storage import DatabaseHandler
            db = DatabaseHandler(config)
            stats = db.get_statistics()
            
            st.markdown("### Quick Stats")
            
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Papers", stats.get("total_papers", 0))
            with metric_col2:
                st.metric("Sections", stats.get("total_sections", 0))
            
            metric_col3, metric_col4 = st.columns(2)
            with metric_col3:
                st.metric("Images", stats.get("total_images", 0))
            with metric_col4:
                st.metric("Tables", stats.get("total_tables", 0))
                
        except Exception:
            st.warning("Database not initialized yet. Upload a paper to get started.")
    
    st.markdown("---")
    st.markdown("### Recent Papers")
    
    try:
        from storage import DatabaseHandler
        db = DatabaseHandler(config)
        recent_papers = db.get_recent_papers(count=5)
        
        if recent_papers:
            for paper in recent_papers:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        title = paper.title if paper.title else paper.filename
                        st.markdown(f"**{title}**")
                    with col2:
                        st.caption(f"{paper.page_count} pages")
                    with col3:
                        st.caption(f"{paper.status.value.capitalize()}")
        else:
            st.info("No papers uploaded yet. Head to the Upload page to get started.")
            
    except Exception:
        st.info("No papers uploaded yet. Head to the Upload page to get started.")


if __name__ == "__main__":
    main()
