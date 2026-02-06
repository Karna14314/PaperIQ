"""
Upload widget component.
"""

import streamlit as st
from typing import Optional, Callable


def render_upload_widget(
    max_size_mb: int = 50,
    on_file_selected: Optional[Callable] = None
) -> Optional[object]:
    """
    Render the file upload widget with styling.
    
    Args:
        max_size_mb: Maximum file size in MB
        on_file_selected: Callback when file is selected
        
    Returns:
        Uploaded file object or None
    """
    st.markdown("""
    <style>
        .upload-box {
            border: 2px dashed #cbd5e1;
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            background-color: #f8fafc;
            transition: all 0.3s ease;
        }
        
        .upload-box:hover {
            border-color: #667eea;
            background-color: #eef2ff;
        }
        
        .upload-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .upload-text {
            color: #64748b;
            font-size: 1rem;
        }
        
        .upload-hint {
            color: #94a3b8;
            font-size: 0.875rem;
            margin-top: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        accept_multiple_files=False,
        help=f"Maximum file size: {max_size_mb}MB. Supported format: PDF"
    )
    
    if uploaded_file is not None and on_file_selected:
        on_file_selected(uploaded_file)
    
    return uploaded_file


def render_upload_progress(current_step: str, progress: float) -> None:
    """
    Render upload progress indicator.
    
    Args:
        current_step: Current processing step description
        progress: Progress from 0 to 1
    """
    st.progress(progress)
    st.markdown(f"**{current_step}**")
