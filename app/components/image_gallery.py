"""Image gallery component."""

import streamlit as st
from pathlib import Path
from typing import List


def render_image_gallery(images: List, columns: int = 3, show_metadata: bool = True):
    """Render a gallery of extracted images."""
    if not images:
        st.info("No images found in this paper.")
        return
    
    st.markdown(f"**{len(images)} images extracted**")
    
    for i in range(0, len(images), columns):
        cols = st.columns(columns)
        for j, col in enumerate(cols):
            if i + j < len(images):
                img = images[i + j]
                with col:
                    img_path = Path(img.file_path)
                    if img_path.exists():
                        st.image(str(img_path), caption=f"Page {img.page_number}", use_container_width=True)
                        if show_metadata:
                            st.caption(f"{img.width}x{img.height} - {img.format}")
                    else:
                        st.warning("Image not found")


def render_image_detail(image):
    """Render detailed view of a single image."""
    img_path = Path(image.file_path)
    
    if img_path.exists():
        st.image(str(img_path), use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Page", image.page_number)
        with col2:
            st.metric("Dimensions", f"{image.width}x{image.height}")
        with col3:
            st.metric("Format", image.format)
        
        with open(img_path, "rb") as f:
            st.download_button(
                label="Download Image",
                data=f.read(),
                file_name=img_path.name,
                mime=f"image/{image.format.lower()}"
            )
    else:
        st.error("Image file not found")
