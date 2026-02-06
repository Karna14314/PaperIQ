"""
Image extraction from PDF files.

Extracts embedded images and saves them with metadata.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image
import io

from models import ExtractedImage
from utils import Config, get_logger


logger = get_logger("paperiq.images")


class ImageHandler:
    """
    Handles extraction of images from PDF files.
    
    Uses PyMuPDF to extract embedded images and saves them
    to the configured images directory.
    """
    
    # Minimum image dimensions to consider (skip tiny images/icons)
    MIN_WIDTH = 50
    MIN_HEIGHT = 50
    
    # Supported output formats
    OUTPUT_FORMAT = "PNG"
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize image handler with configuration.
        
        Args:
            config: Configuration instance (uses default if not provided)
        """
        self.config = config or Config()
        self.images_dir = self.config.images_dir
    
    def extract_images(
        self,
        pdf_path: Path,
        paper_id: int
    ) -> List[ExtractedImage]:
        """
        Extract all images from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            paper_id: ID of the paper (for naming files)
            
        Returns:
            List of ExtractedImage objects
        """
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return []
        
        doc = None
        extracted_images: List[ExtractedImage] = []
        image_counter = 0
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_images = self._extract_page_images(
                    page, page_num + 1, paper_id, image_counter
                )
                
                image_counter += len(page_images)
                extracted_images.extend(page_images)
            
            logger.info(f"Extracted {len(extracted_images)} images from PDF")
            return extracted_images
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return extracted_images
        finally:
            if doc is not None:
                doc.close()
    
    def _extract_page_images(
        self,
        page: fitz.Page,
        page_number: int,
        paper_id: int,
        start_index: int
    ) -> List[ExtractedImage]:
        """
        Extract images from a single page.
        
        Args:
            page: PyMuPDF page object
            page_number: 1-indexed page number
            paper_id: Paper ID for file naming
            start_index: Starting index for image numbering
            
        Returns:
            List of ExtractedImage objects
        """
        images: List[ExtractedImage] = []
        image_list = page.get_images(full=True)
        
        for img_index, img_info in enumerate(image_list):
            try:
                xref = img_info[0]  # Image reference number
                
                # Extract image data
                base_image = page.parent.extract_image(xref)
                if not base_image:
                    continue
                
                image_bytes = base_image.get("image")
                if not image_bytes:
                    continue
                
                # Get image info
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)
                
                # Skip small images (likely icons or artifacts)
                if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
                    continue
                
                # Convert and save image
                image_num = start_index + img_index + 1
                saved_path = self._save_image(
                    image_bytes, paper_id, image_num, width, height
                )
                
                if saved_path:
                    images.append(ExtractedImage(
                        paper_id=paper_id,
                        file_path=str(saved_path),
                        page_number=page_number,
                        width=width,
                        height=height,
                        format=self.OUTPUT_FORMAT,
                    ))
                    
            except Exception as e:
                logger.warning(f"Failed to extract image {img_index} on page {page_number}: {e}")
                continue
        
        return images
    
    def _save_image(
        self,
        image_bytes: bytes,
        paper_id: int,
        image_num: int,
        width: int,
        height: int
    ) -> Optional[Path]:
        """
        Save image bytes to file.
        
        Converts image to PNG format for consistency.
        
        Args:
            image_bytes: Raw image data
            paper_id: Paper ID for file naming
            image_num: Image number for file naming
            width: Image width
            height: Image height
            
        Returns:
            Path to saved file, or None on failure
        """
        try:
            # Open with PIL to handle format conversion
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary (handles CMYK, palette, etc.)
            if image.mode in ("CMYK", "P", "LA", "PA"):
                image = image.convert("RGB")
            elif image.mode == "RGBA":
                # Keep transparency for PNG
                pass
            elif image.mode != "RGB":
                image = image.convert("RGB")
            
            # Generate filename
            filename = f"paper_{paper_id}_img_{image_num}.png"
            save_path = self.images_dir / filename
            
            # Save as PNG
            image.save(save_path, format="PNG", optimize=True)
            
            logger.debug(f"Saved image: {filename} ({width}x{height})")
            return save_path
            
        except Exception as e:
            logger.warning(f"Failed to save image: {e}")
            return None
    
    def get_image_thumbnail(
        self,
        image_path: Path,
        max_size: Tuple[int, int] = (200, 200)
    ) -> Optional[Image.Image]:
        """
        Generate a thumbnail of an extracted image.
        
        Args:
            image_path: Path to the image file
            max_size: Maximum thumbnail dimensions (width, height)
            
        Returns:
            PIL Image thumbnail, or None on failure
        """
        try:
            if not image_path.exists():
                return None
            
            image = Image.open(image_path)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            return image
            
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail: {e}")
            return None
    
    def cleanup_paper_images(self, paper_id: int) -> int:
        """
        Delete all images associated with a paper.
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            Number of files deleted
        """
        deleted = 0
        pattern = f"paper_{paper_id}_img_*.png"
        
        for image_file in self.images_dir.glob(pattern):
            try:
                image_file.unlink()
                deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete {image_file}: {e}")
        
        return deleted
