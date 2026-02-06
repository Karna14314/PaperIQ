"""
File system operations for PaperIQ.

Handles file uploads, storage, and cleanup operations.
"""

import shutil
import os
from pathlib import Path
from typing import Optional, Tuple, BinaryIO
from datetime import datetime
import hashlib

from utils import Config, get_logger


logger = get_logger("paperiq.files")


class FileManager:
    """
    Manages file system operations for PaperIQ.
    
    Handles:
    - PDF file uploads and storage
    - File naming with unique IDs
    - Cleanup operations
    - Storage statistics
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize file manager.
        
        Args:
            config: Configuration instance (uses default if not provided)
        """
        self.config = config or Config()
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        directories = [
            self.config.upload_dir,
            self.config.images_dir,
            self.config.tables_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_uploaded_file(
        self,
        file_data: BinaryIO,
        original_filename: str,
        paper_id: int
    ) -> Tuple[Path, int]:
        """
        Save an uploaded PDF file.
        
        Args:
            file_data: File-like object with PDF data
            original_filename: Original filename from upload
            paper_id: ID of the paper in database
            
        Returns:
            Tuple of (saved_path, file_size_bytes)
        """
        # Sanitize filename
        safe_name = self._sanitize_filename(original_filename)
        
        # Create unique filename with paper ID
        filename = f"paper_{paper_id}_{safe_name}"
        save_path = self.config.upload_dir / filename
        
        # Read file content
        file_data.seek(0)
        content = file_data.read()
        file_size = len(content)
        
        # Save file
        with open(save_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved uploaded file: {filename} ({file_size} bytes)")
        return save_path, file_size
    
    def save_file_from_path(
        self,
        source_path: Path,
        paper_id: int
    ) -> Tuple[Path, int]:
        """
        Copy a file from a path to the uploads directory.
        
        Args:
            source_path: Path to source file
            paper_id: ID of the paper in database
            
        Returns:
            Tuple of (saved_path, file_size_bytes)
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Sanitize filename
        safe_name = self._sanitize_filename(source_path.name)
        
        # Create unique filename with paper ID
        filename = f"paper_{paper_id}_{safe_name}"
        save_path = self.config.upload_dir / filename
        
        # Copy file
        shutil.copy2(source_path, save_path)
        file_size = save_path.stat().st_size
        
        logger.info(f"Copied file: {filename} ({file_size} bytes)")
        return save_path, file_size
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to be safe for filesystem.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename
        """
        # Remove path components
        filename = Path(filename).name
        
        # Replace problematic characters
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in ".-_":
                safe_chars.append(char)
            elif char in " ()[]":
                safe_chars.append("_")
        
        safe_name = "".join(safe_chars)
        
        # Ensure it ends with .pdf
        if not safe_name.lower().endswith(".pdf"):
            safe_name += ".pdf"
        
        # Limit length
        if len(safe_name) > 100:
            safe_name = safe_name[:96] + ".pdf"
        
        return safe_name
    
    def get_file_path(self, paper_id: int) -> Optional[Path]:
        """
        Find the PDF file for a given paper ID.
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            Path to file if found, None otherwise
        """
        pattern = f"paper_{paper_id}_*.pdf"
        matches = list(self.config.upload_dir.glob(pattern))
        
        if matches:
            return matches[0]
        return None
    
    def delete_paper_files(self, paper_id: int) -> int:
        """
        Delete all files associated with a paper.
        
        Removes:
        - Uploaded PDF
        - Extracted images
        - Extracted table CSVs
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            Number of files deleted
        """
        deleted = 0
        
        # Delete uploaded PDF
        pdf_pattern = f"paper_{paper_id}_*.pdf"
        for pdf_file in self.config.upload_dir.glob(pdf_pattern):
            try:
                pdf_file.unlink()
                deleted += 1
                logger.debug(f"Deleted: {pdf_file}")
            except Exception as e:
                logger.warning(f"Failed to delete {pdf_file}: {e}")
        
        # Delete images
        img_pattern = f"paper_{paper_id}_img_*.png"
        for img_file in self.config.images_dir.glob(img_pattern):
            try:
                img_file.unlink()
                deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete {img_file}: {e}")
        
        # Delete tables
        table_pattern = f"paper_{paper_id}_table_*.csv"
        for table_file in self.config.tables_dir.glob(table_pattern):
            try:
                table_file.unlink()
                deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete {table_file}: {e}")
        
        logger.info(f"Deleted {deleted} files for paper ID: {paper_id}")
        return deleted
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage information
        """
        def dir_size(path: Path) -> Tuple[int, int]:
            """Get total size and file count for a directory."""
            total = 0
            count = 0
            if path.exists():
                for f in path.iterdir():
                    if f.is_file():
                        total += f.stat().st_size
                        count += 1
            return total, count
        
        uploads_size, uploads_count = dir_size(self.config.upload_dir)
        images_size, images_count = dir_size(self.config.images_dir)
        tables_size, tables_count = dir_size(self.config.tables_dir)
        
        db_size = 0
        if self.config.db_path.exists():
            db_size = self.config.db_path.stat().st_size
        
        total_size = uploads_size + images_size + tables_size + db_size
        
        return {
            "uploads": {
                "size_bytes": uploads_size,
                "size_mb": uploads_size / (1024 * 1024),
                "file_count": uploads_count,
            },
            "images": {
                "size_bytes": images_size,
                "size_mb": images_size / (1024 * 1024),
                "file_count": images_count,
            },
            "tables": {
                "size_bytes": tables_size,
                "size_mb": tables_size / (1024 * 1024),
                "file_count": tables_count,
            },
            "database": {
                "size_bytes": db_size,
                "size_mb": db_size / (1024 * 1024),
            },
            "total": {
                "size_bytes": total_size,
                "size_mb": total_size / (1024 * 1024),
            },
        }
    
    def cleanup_orphaned_files(self, valid_paper_ids: set) -> int:
        """
        Remove files that don't belong to any valid paper.
        
        Args:
            valid_paper_ids: Set of paper IDs that should be kept
            
        Returns:
            Number of files deleted
        """
        import re
        
        deleted = 0
        paper_id_pattern = re.compile(r"paper_(\d+)_")
        
        # Check all directories
        for directory in [self.config.upload_dir, self.config.images_dir, self.config.tables_dir]:
            for file_path in directory.iterdir():
                if not file_path.is_file():
                    continue
                
                match = paper_id_pattern.match(file_path.name)
                if match:
                    paper_id = int(match.group(1))
                    if paper_id not in valid_paper_ids:
                        try:
                            file_path.unlink()
                            deleted += 1
                            logger.debug(f"Cleaned up orphaned file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete orphaned {file_path}: {e}")
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} orphaned files")
        
        return deleted
    
    def file_exists(self, file_path: Path) -> bool:
        """Check if a file exists."""
        return file_path.exists() and file_path.is_file()
    
    def get_file_hash(self, file_path: Path) -> str:
        """
        Calculate MD5 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex digest of MD5 hash
        """
        if not file_path.exists():
            return ""
        
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
        
        return md5.hexdigest()
