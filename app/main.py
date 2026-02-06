"""
PaperIQ - Main Streamlit Application
Research Paper Insight Analyzer - Milestone 1

This is the main entry point for the Streamlit application.
Run with: streamlit run app/main.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from utils import Config

# Initialize configuration
config = Config()

# Page configuration
st.set_page_config(
    page_title=config.streamlit_page_title,
    page_icon=config.streamlit_page_icon,
    layout=config.streamlit_layout,
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 1rem;
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    
    /* Card styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Section card styling */
    .section-card {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Confidence badge colors */
    .confidence-high {
        background-color: #10b981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .confidence-medium {
        background-color: #f59e0b;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .confidence-low {
        background-color: #ef4444;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f3f4f6;
    }
    
    /* Success/warning/error messages */
    .success-box {
        background-color: #d1fae5;
        border: 1px solid #10b981;
        border-radius: 8px;
        padding: 1rem;
        color: #065f46;
    }
    
    .warning-box {
        background-color: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        color: #92400e;
    }
    
    .error-box {
        background-color: #fee2e2;
        border: 1px solid #ef4444;
        border-radius: 8px;
        padding: 1rem;
        color: #991b1b;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""
    
    # Header
    st.markdown('<p class="main-header">📄 PaperIQ</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Research Paper Insight Analyzer - Upload and analyze research papers with AI-powered section detection</p>',
        unsafe_allow_html=True
    )
    
    # Main content area
    st.markdown("---")
    
    # Welcome message
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 👋 Welcome to PaperIQ!")
        st.markdown("""
        PaperIQ helps you extract and analyze research papers automatically. Here's what you can do:
        
        - **📤 Upload PDFs** - Upload research papers in PDF format
        - **🔍 Section Detection** - Automatically identify Abstract, Introduction, Methods, Results, Discussion, Conclusion, and References
        - **🖼️ Image Extraction** - Extract all figures and diagrams
        - **📊 Table Extraction** - Extract tables and convert to CSV
        - **✅ Quality Validation** - Get confidence scores and quality reports
        """)
        
        st.markdown("---")
        
        st.info("👈 **Get Started:** Use the sidebar to navigate to the Upload page!")
    
    with col2:
        # Quick stats
        try:
            from storage import DatabaseHandler
            db = DatabaseHandler(config)
            stats = db.get_statistics()
            
            st.markdown("### 📊 Quick Stats")
            
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
                
        except Exception as e:
            st.warning("Database not initialized yet. Upload a paper to get started!")
    
    # Recent papers section
    st.markdown("---")
    st.markdown("### 📚 Recent Papers")
    
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
                        st.caption(f"📄 {paper.page_count} pages")
                    with col3:
                        status_emoji = {
                            "completed": "✅",
                            "processing": "⏳",
                            "failed": "❌",
                            "uploaded": "📤"
                        }
                        emoji = status_emoji.get(paper.status.value, "❓")
                        st.caption(f"{emoji} {paper.status.value.capitalize()}")
        else:
            st.info("No papers uploaded yet. Head to the Upload page to get started! 🚀")
            
    except Exception as e:
        st.info("No papers uploaded yet. Head to the Upload page to get started! 🚀")


if __name__ == "__main__":
    main()
