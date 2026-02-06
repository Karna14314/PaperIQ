"""
Upload Page - PDF Upload and Processing

Handles file upload, validation, and processing pipeline.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import time

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from utils import Config, PDFValidator, get_logger
from models import Paper, ProcessingStatus, ValidationReport, ValidationItem, SectionType
from parsers import PDFExtractor, SectionDetector, ImageHandler, TableHandler, TextCleaner
from storage import DatabaseHandler, FileManager

# Initialize components
config = Config()
logger = get_logger("paperiq.upload")

# Page config
st.set_page_config(
    page_title="Upload - PaperIQ",
    page_icon="📤",
    layout="wide"
)


def process_paper(uploaded_file) -> tuple:
    """
    Process an uploaded PDF file through the complete pipeline.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Tuple of (success, paper_id, message)
    """
    validator = PDFValidator(config)
    db = DatabaseHandler(config)
    file_manager = FileManager(config)
    pdf_extractor = PDFExtractor(config)
    section_detector = SectionDetector(config)
    image_handler = ImageHandler(config)
    table_handler = TableHandler(config)
    text_cleaner = TextCleaner()
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Validate file
        status_text.text("🔍 Validating PDF...")
        progress_bar.progress(5)
        
        validation_result = validator.validate_uploaded_file(
            uploaded_file, uploaded_file.name
        )
        
        if not validation_result.is_valid:
            return False, None, f"Validation failed: {validation_result.message}"
        
        progress_bar.progress(10)
        
        # Step 2: Create paper record
        status_text.text("💾 Creating paper record...")
        
        paper = Paper(
            filename=uploaded_file.name,
            status=ProcessingStatus.PROCESSING,
            file_size_bytes=validation_result.details.get("size_bytes", 0)
        )
        paper_id = db.insert_paper(paper)
        paper.id = paper_id
        
        progress_bar.progress(15)
        
        # Step 3: Save file
        status_text.text("📁 Saving file...")
        
        saved_path, file_size = file_manager.save_uploaded_file(
            uploaded_file, uploaded_file.name, paper_id
        )
        paper.file_path = str(saved_path)
        paper.file_size_bytes = file_size
        
        progress_bar.progress(20)
        
        # Step 4: Extract text
        status_text.text("📝 Extracting text...")
        
        extraction_result = pdf_extractor.extract(saved_path)
        
        if not extraction_result.success:
            db.update_paper_status(paper_id, ProcessingStatus.FAILED)
            return False, paper_id, f"Text extraction failed: {extraction_result.error}"
        
        paper.page_count = extraction_result.page_count
        paper.title = extraction_result.title
        paper.full_text = extraction_result.full_text
        
        progress_bar.progress(40)
        
        # Step 5: Extract images
        status_text.text("🖼️ Extracting images...")
        
        images = image_handler.extract_images(saved_path, paper_id)
        paper.images = images
        
        progress_bar.progress(55)
        
        # Step 6: Extract tables
        status_text.text("📊 Extracting tables...")
        
        tables = table_handler.extract_tables(saved_path, paper_id)
        paper.tables = tables
        
        progress_bar.progress(70)
        
        # Step 7: Detect sections
        status_text.text("🔬 Identifying sections...")
        
        sections = section_detector.detect_sections(
            extraction_result.full_text,
            extraction_result.text_blocks
        )
        
        # Update section paper_id
        for section in sections:
            section.paper_id = paper_id
        
        paper.sections = sections
        
        progress_bar.progress(85)
        
        # Step 8: Generate validation report
        status_text.text("✅ Generating validation report...")
        
        validation_report = generate_validation_report(paper, section_detector)
        paper.validation_report = validation_report
        
        progress_bar.progress(90)
        
        # Step 9: Save to database
        status_text.text("💾 Saving results...")
        
        # Save sections
        db.insert_sections(sections)
        
        # Save images
        db.insert_images(images)
        
        # Save tables
        db.insert_tables(tables)
        
        # Update paper status
        paper.status = ProcessingStatus.COMPLETED
        db.update_paper(paper)
        
        progress_bar.progress(100)
        status_text.text("✨ Processing complete!")
        
        # Log summary
        logger.info(
            f"Paper processed: {paper.filename} - "
            f"{len(sections)} sections, {len(images)} images, {len(tables)} tables"
        )
        
        return True, paper_id, "Paper processed successfully!"
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        if paper_id:
            db.update_paper_status(paper_id, ProcessingStatus.FAILED)
        return False, None, f"Processing error: {str(e)}"


def generate_validation_report(paper: Paper, section_detector: SectionDetector) -> ValidationReport:
    """
    Generate a validation report for a processed paper.
    
    Args:
        paper: Processed Paper object
        section_detector: SectionDetector instance
        
    Returns:
        ValidationReport object
    """
    report = ValidationReport()
    
    # Check required sections
    required_sections = [SectionType.ABSTRACT, SectionType.INTRODUCTION, SectionType.CONCLUSION]
    found_types = {s.section_type for s in paper.sections}
    
    for section_type in required_sections:
        if section_type in found_types:
            section = next(s for s in paper.sections if s.section_type == section_type)
            if section.confidence >= 0.7:
                report.add_check(
                    f"{section_type.value.capitalize()} present",
                    "pass",
                    f"Found with {section.confidence:.0%} confidence"
                )
            else:
                report.add_check(
                    f"{section_type.value.capitalize()} present",
                    "warning",
                    f"Found but low confidence ({section.confidence:.0%})"
                )
        else:
            report.add_check(
                f"{section_type.value.capitalize()} present",
                "fail",
                "Section not found"
            )
    
    # Check optional sections
    optional_sections = [SectionType.METHODOLOGY, SectionType.RESULTS, SectionType.DISCUSSION, SectionType.REFERENCES]
    
    for section_type in optional_sections:
        if section_type in found_types:
            section = next(s for s in paper.sections if s.section_type == section_type)
            report.add_check(
                f"{section_type.value.capitalize()} present",
                "pass",
                f"Found with {section.confidence:.0%} confidence"
            )
        else:
            report.add_check(
                f"{section_type.value.capitalize()} present",
                "warning",
                "Section not found"
            )
    
    # Check section lengths
    for section in paper.sections:
        if section.word_count < 10:
            report.add_check(
                f"{section.section_type.value.capitalize()} content",
                "warning",
                f"Section may be too short ({section.word_count} words)"
            )
    
    # Calculate quality score
    quality_score, quality_level = section_detector.calculate_detection_quality(paper.sections)
    report.quality_score = quality_score
    report.quality_level = quality_level
    
    return report


def main():
    """Main upload page."""
    
    st.markdown("# 📤 Upload Research Paper")
    st.markdown("Upload a PDF research paper to extract and analyze its content.")
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        st.checkbox("Extract images", value=True, key="extract_images", disabled=True)
        st.checkbox("Extract tables", value=True, key="extract_tables", disabled=True)
        st.checkbox("Enable OCR (coming soon)", value=False, disabled=True)
        
        st.markdown("---")
        
        st.markdown("### 📚 Recent Papers")
        try:
            db = DatabaseHandler(config)
            recent_papers = db.get_recent_papers(count=5)
            
            if recent_papers:
                for paper in recent_papers:
                    status_emoji = {
                        "completed": "✅",
                        "processing": "⏳",
                        "failed": "❌",
                        "uploaded": "📤"
                    }
                    emoji = status_emoji.get(paper.status.value, "❓")
                    
                    title = paper.title[:30] + "..." if paper.title and len(paper.title) > 30 else (paper.title or paper.filename)
                    
                    if st.button(f"{emoji} {title}", key=f"paper_{paper.id}"):
                        st.session_state["selected_paper_id"] = paper.id
                        st.switch_page("pages/2_📊_Results.py")
            else:
                st.info("No papers yet")
        except Exception:
            st.info("No papers yet")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📁 Select PDF File")
        
        uploaded_file = st.file_uploader(
            "Drag and drop a PDF file or click to browse",
            type=["pdf"],
            accept_multiple_files=False,
            help=f"Maximum file size: {config.max_pdf_size_mb}MB"
        )
        
        if uploaded_file is not None:
            # Show file info
            st.markdown("---")
            st.markdown("### 📋 File Information")
            
            file_size_mb = uploaded_file.size / (1024 * 1024)
            
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.markdown(f"**Filename:** {uploaded_file.name}")
                st.markdown(f"**Size:** {file_size_mb:.2f} MB")
            with info_col2:
                st.markdown(f"**Type:** {uploaded_file.type}")
            
            st.markdown("---")
            
            # Process button
            if st.button("🚀 Parse Paper", type="primary", use_container_width=True):
                with st.spinner("Processing..."):
                    success, paper_id, message = process_paper(uploaded_file)
                
                if success:
                    st.success(f"✅ {message}")
                    st.session_state["selected_paper_id"] = paper_id
                    
                    st.markdown("---")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("📊 View Results", type="primary", use_container_width=True):
                            st.switch_page("pages/2_📊_Results.py")
                    with col_b:
                        if st.button("📤 Upload Another", use_container_width=True):
                            st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    with col2:
        st.markdown("### 📖 How it works")
        st.markdown("""
        1. **Upload** your PDF research paper
        2. **Wait** for automatic processing
        3. **View** extracted sections, images, and tables
        4. **Review** the validation report
        
        ---
        
        **Supported formats:**
        - Standard research papers (IEEE, ACM, etc.)
        - Single and multi-column layouts
        - Digital PDFs (not scanned)
        
        **Extracted content:**
        - 📝 Abstract, Introduction, Methods, Results, Discussion, Conclusion, References
        - 🖼️ Figures and diagrams
        - 📊 Tables (saved as CSV)
        """)


if __name__ == "__main__":
    main()
