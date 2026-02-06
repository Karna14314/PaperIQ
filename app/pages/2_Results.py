"""
Results Page - View Parsing Results
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from utils import Config, get_logger
from models import SectionType
from storage import DatabaseHandler, FileManager

config = Config()
logger = get_logger("paperiq.results")

st.set_page_config(page_title="Results - PaperIQ", page_icon="docs", layout="wide")


def get_confidence_color(confidence):
    """Get color based on confidence level."""
    if confidence >= 0.8:
        return "#10b981"
    elif confidence >= 0.6:
        return "#f59e0b"
    return "#ef4444"


def display_section(section):
    """Display a single section with expandable content."""
    section_names = {
        SectionType.ABSTRACT: "Abstract",
        SectionType.INTRODUCTION: "Introduction",
        SectionType.METHODOLOGY: "Methodology",
        SectionType.RESULTS: "Results",
        SectionType.DISCUSSION: "Discussion",
        SectionType.CONCLUSION: "Conclusion",
        SectionType.REFERENCES: "References",
        SectionType.UNKNOWN: "Unknown",
    }
    
    name = section_names.get(section.section_type, "Section")
    color = get_confidence_color(section.confidence)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {name}")
    with col2:
        st.markdown(
            f'<span style="background-color: {color}; color: white; padding: 0.2rem 0.6rem; '
            f'border-radius: 9999px; font-size: 0.8rem;">{section.confidence:.0%}</span>',
            unsafe_allow_html=True
        )
    
    with st.expander("Read more", expanded=False):
        st.markdown(section.content)
        st.caption(f"{section.word_count} words")


def display_images(images):
    """Display extracted images in a gallery."""
    if not images:
        st.info("No images found in this paper.")
        return
    
    cols_per_row = 3
    for i in range(0, len(images), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(images):
                img = images[i + j]
                img_path = Path(img.file_path)
                with col:
                    if img_path.exists():
                        st.image(str(img_path), caption=f"Page {img.page_number}")
                        st.caption(f"{img.dimensions} - {img.format}")
                    else:
                        st.warning(f"Image not found: {img.filename}")


def display_tables(tables):
    """Display extracted tables with previews."""
    if not tables:
        st.info("No tables found in this paper.")
        return
    
    for i, table in enumerate(tables):
        with st.expander(f"Table {i + 1} (Page {table.page_number}) - {table.dimensions}"):
            csv_path = Path(table.file_path)
            if csv_path.exists():
                try:
                    df = pd.read_csv(csv_path)
                    st.dataframe(df.head(10), use_container_width=True)
                    st.download_button(
                        label="Download CSV",
                        data=csv_path.read_bytes(),
                        file_name=csv_path.name,
                        mime="text/csv",
                        key=f"download_table_{i}"
                    )
                except Exception as e:
                    st.error(f"Error loading table: {e}")
            else:
                st.warning("Table file not found")


def display_validation(paper):
    """Display validation report."""
    if not paper.validation_report:
        st.warning("No validation report available.")
        return
    
    report = paper.validation_report
    col1, col2, col3 = st.columns(3)
    
    with col1:
        color = "#10b981" if report.quality_level == "high" else "#f59e0b" if report.quality_level == "medium" else "#ef4444"
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background-color: {color}20; border-radius: 8px;">
            <div style="font-size: 2rem; font-weight: bold; color: {color};">{report.quality_score:.0%}</div>
            <div style="color: #6b7280;">Quality Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Passed", report.pass_count)
    with col3:
        st.metric("Warnings", report.warning_count)
    
    st.markdown("---")
    st.markdown("### Validation Checklist")
    
    for item in report.items:
        if item.status == "pass":
            bg_color, text_color, icon = "#d1fae5", "#065f46", "[PASS]"
        elif item.status == "warning":
            bg_color, text_color, icon = "#fef3c7", "#92400e", "[WARN]"
        else:
            bg_color, text_color, icon = "#fee2e2", "#991b1b", "[FAIL]"
        
        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 0.5rem; color: {text_color};">
            {icon} <strong>{item.name}</strong><br>
            <span style="font-size: 0.9rem; opacity: 0.8;">{item.message}</span>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main results page."""
    st.markdown("# Parsing Results")
    
    db = DatabaseHandler(config)
    
    with st.sidebar:
        st.markdown("### Select Paper")
        papers = db.get_all_papers(limit=20)
        
        if not papers:
            st.info("No papers processed yet.")
            st.markdown("---")
            if st.button("Upload Paper", use_container_width=True):
                st.switch_page("pages/1_Upload.py")
            return
        
        paper_options = {f"{p.title or p.filename} ({p.status.value})": p.id for p in papers}
        selected_name = st.selectbox("Choose a paper", options=list(paper_options.keys()), index=0)
        selected_id = paper_options[selected_name]
        
        if "selected_paper_id" in st.session_state:
            if st.session_state["selected_paper_id"] in [p.id for p in papers]:
                selected_id = st.session_state["selected_paper_id"]
    
    paper = db.get_paper(selected_id, include_content=True)
    
    if not paper:
        st.error("Paper not found.")
        return
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pages", paper.page_count)
    with col2:
        st.metric("Sections", paper.section_count)
    with col3:
        st.metric("Images", paper.image_count)
    with col4:
        st.metric("Tables", paper.table_count)
    
    if paper.title:
        st.markdown(f"### {paper.title}")
    else:
        st.markdown(f"### {paper.filename}")
    
    st.caption(f"Uploaded: {paper.upload_date.strftime('%Y-%m-%d %H:%M') if paper.upload_date else 'Unknown'} | Size: {paper.file_size_mb:.2f} MB | Status: {paper.status.value.capitalize()}")
    
    st.markdown("---")
    
    tab_sections, tab_images, tab_tables, tab_validation = st.tabs(["Sections", "Images", "Tables", "Validation"])
    
    with tab_sections:
        if paper.sections:
            st.markdown(f"**{len(paper.sections)} sections identified**")
            st.markdown("---")
            for section in paper.sections:
                display_section(section)
                st.markdown("---")
        else:
            st.warning("No sections were identified in this paper.")
            if paper.full_text:
                with st.expander("View raw text"):
                    st.text(paper.full_text[:5000] + "..." if len(paper.full_text) > 5000 else paper.full_text)
    
    with tab_images:
        st.markdown(f"**{len(paper.images)} images extracted**")
        st.markdown("---")
        display_images(paper.images)
    
    with tab_tables:
        st.markdown(f"**{len(paper.tables)} tables extracted**")
        st.markdown("---")
        display_tables(paper.tables)
    
    with tab_validation:
        display_validation(paper)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Upload New Paper", use_container_width=True):
            st.switch_page("pages/1_Upload.py")
    with col2:
        st.button("Export JSON (Coming Soon)", disabled=True, use_container_width=True)
    with col3:
        if st.button("Delete Paper", use_container_width=True):
            if st.session_state.get("confirm_delete", False):
                file_manager = FileManager(config)
                file_manager.delete_paper_files(paper.id)
                db.delete_paper(paper.id)
                st.success("Paper deleted!")
                st.session_state["confirm_delete"] = False
                st.rerun()
            else:
                st.session_state["confirm_delete"] = True
                st.warning("Click again to confirm deletion")


if __name__ == "__main__":
    main()
