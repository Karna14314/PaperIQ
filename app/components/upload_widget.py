"""Upload widget component."""

import streamlit as st
from typing import Optional, Callable


def render_upload_widget(max_size_mb: int = 50, on_file_selected: Optional[Callable] = None):
    """Render the file upload widget."""
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        accept_multiple_files=False,
        help=f"Maximum file size: {max_size_mb}MB"
    )
    
    if uploaded_file is not None and on_file_selected:
        on_file_selected(uploaded_file)
    
    return uploaded_file


def render_upload_progress(current_step: str, progress: float):
    """Render upload progress indicator."""
    st.progress(progress)
    st.markdown(f"**{current_step}**")
