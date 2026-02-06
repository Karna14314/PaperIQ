"""
SQLite database operations for PaperIQ.

Handles all database interactions using Python's built-in sqlite3.
Auto-creates tables on first run.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager

from models import (
    Paper, Section, SectionType, ExtractedImage, 
    ExtractedTable, ProcessingStatus
)
from utils import Config, get_logger


logger = get_logger("paperiq.database")


class DatabaseHandler:
    """
    SQLite database handler for persistent storage.
    
    Manages paper metadata, sections, images, and tables.
    Auto-creates schema on first initialization.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize database handler.
        
        Args:
            config: Configuration instance (uses default if not provided)
        """
        self.config = config or Config()
        self.db_path = self.config.db_path
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        
        Ensures connections are properly closed and commits are handled.
        
        Yields:
            sqlite3.Connection
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def _init_database(self) -> None:
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Papers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    title TEXT,
                    upload_date TEXT NOT NULL,
                    page_count INTEGER DEFAULT 0,
                    file_size_bytes INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'uploaded',
                    file_path TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER NOT NULL,
                    section_type TEXT NOT NULL,
                    content TEXT,
                    confidence REAL DEFAULT 0.0,
                    start_position INTEGER DEFAULT 0,
                    end_position INTEGER DEFAULT 0,
                    word_count INTEGER DEFAULT 0,
                    FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE
                )
            """)
            
            # Images table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    page_number INTEGER DEFAULT 0,
                    width INTEGER DEFAULT 0,
                    height INTEGER DEFAULT 0,
                    format TEXT DEFAULT 'PNG',
                    FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE
                )
            """)
            
            # Tables table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    page_number INTEGER DEFAULT 0,
                    row_count INTEGER DEFAULT 0,
                    column_count INTEGER DEFAULT 0,
                    preview TEXT,
                    FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sections_paper 
                ON sections (paper_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_images_paper 
                ON images (paper_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tables_paper 
                ON tables (paper_id)
            """)
            
            conn.commit()
            logger.debug("Database schema initialized")
    
    # ==================== Paper Operations ====================
    
    def insert_paper(self, paper: Paper) -> int:
        """
        Insert a new paper into the database.
        
        Args:
            paper: Paper object to insert
            
        Returns:
            ID of the inserted paper
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO papers (filename, title, upload_date, page_count, 
                                    file_size_bytes, status, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                paper.filename,
                paper.title,
                paper.upload_date.isoformat() if paper.upload_date else datetime.now().isoformat(),
                paper.page_count,
                paper.file_size_bytes,
                paper.status.value,
                paper.file_path,
            ))
            
            conn.commit()
            paper_id = cursor.lastrowid
            
            logger.info(f"Inserted paper: {paper.filename} (ID: {paper_id})")
            return paper_id
    
    def update_paper(self, paper: Paper) -> bool:
        """
        Update an existing paper.
        
        Args:
            paper: Paper object with updated data
            
        Returns:
            True if update successful
        """
        if paper.id is None:
            return False
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE papers 
                SET title = ?, page_count = ?, file_size_bytes = ?, status = ?
                WHERE id = ?
            """, (
                paper.title,
                paper.page_count,
                paper.file_size_bytes,
                paper.status.value,
                paper.id,
            ))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def update_paper_status(self, paper_id: int, status: ProcessingStatus) -> bool:
        """
        Update paper processing status.
        
        Args:
            paper_id: ID of the paper
            status: New status
            
        Returns:
            True if update successful
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE papers SET status = ? WHERE id = ?
            """, (status.value, paper_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_paper(self, paper_id: int, include_content: bool = True) -> Optional[Paper]:
        """
        Get a paper by ID.
        
        Args:
            paper_id: ID of the paper
            include_content: Whether to load sections, images, tables
            
        Returns:
            Paper object or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            paper = self._row_to_paper(row)
            
            if include_content:
                paper.sections = self.get_sections(paper_id)
                paper.images = self.get_images(paper_id)
                paper.tables = self.get_tables(paper_id)
            
            return paper
    
    def get_all_papers(self, limit: int = 100) -> List[Paper]:
        """
        Get all papers (metadata only).
        
        Args:
            limit: Maximum number of papers to return
            
        Returns:
            List of Paper objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM papers 
                ORDER BY upload_date DESC 
                LIMIT ?
            """, (limit,))
            
            return [self._row_to_paper(row) for row in cursor.fetchall()]
    
    def get_recent_papers(self, count: int = 5) -> List[Paper]:
        """
        Get most recently uploaded papers.
        
        Args:
            count: Number of papers to return
            
        Returns:
            List of Paper objects
        """
        return self.get_all_papers(limit=count)
    
    def delete_paper(self, paper_id: int) -> bool:
        """
        Delete a paper and all related data.
        
        Args:
            paper_id: ID of the paper to delete
            
        Returns:
            True if deleted successfully
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete related records first (cascade should handle this, but being explicit)
            cursor.execute("DELETE FROM sections WHERE paper_id = ?", (paper_id,))
            cursor.execute("DELETE FROM images WHERE paper_id = ?", (paper_id,))
            cursor.execute("DELETE FROM tables WHERE paper_id = ?", (paper_id,))
            cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Deleted paper ID: {paper_id}")
                return True
            return False
    
    def _row_to_paper(self, row: sqlite3.Row) -> Paper:
        """Convert database row to Paper object."""
        upload_date = None
        if row["upload_date"]:
            try:
                upload_date = datetime.fromisoformat(row["upload_date"])
            except ValueError:
                upload_date = datetime.now()
        
        return Paper(
            id=row["id"],
            filename=row["filename"],
            title=row["title"] or "",
            upload_date=upload_date,
            page_count=row["page_count"],
            file_size_bytes=row["file_size_bytes"],
            status=ProcessingStatus(row["status"]),
            file_path=row["file_path"] or "",
        )
    
    # ==================== Section Operations ====================
    
    def insert_section(self, section: Section) -> int:
        """
        Insert a section into the database.
        
        Args:
            section: Section object to insert
            
        Returns:
            ID of the inserted section
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sections (paper_id, section_type, content, confidence,
                                      start_position, end_position, word_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                section.paper_id,
                section.section_type.value,
                section.content,
                section.confidence,
                section.start_position,
                section.end_position,
                section.word_count,
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def insert_sections(self, sections: List[Section]) -> List[int]:
        """
        Insert multiple sections.
        
        Args:
            sections: List of Section objects
            
        Returns:
            List of inserted IDs
        """
        return [self.insert_section(s) for s in sections]
    
    def get_sections(self, paper_id: int) -> List[Section]:
        """
        Get all sections for a paper.
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            List of Section objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM sections WHERE paper_id = ?
                ORDER BY start_position
            """, (paper_id,))
            
            return [self._row_to_section(row) for row in cursor.fetchall()]
    
    def _row_to_section(self, row: sqlite3.Row) -> Section:
        """Convert database row to Section object."""
        return Section(
            id=row["id"],
            paper_id=row["paper_id"],
            section_type=SectionType.from_string(row["section_type"]),
            content=row["content"] or "",
            confidence=row["confidence"],
            start_position=row["start_position"],
            end_position=row["end_position"],
            word_count=row["word_count"],
        )
    
    # ==================== Image Operations ====================
    
    def insert_image(self, image: ExtractedImage) -> int:
        """
        Insert an image record.
        
        Args:
            image: ExtractedImage object
            
        Returns:
            ID of the inserted image
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO images (paper_id, file_path, page_number, 
                                    width, height, format)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                image.paper_id,
                image.file_path,
                image.page_number,
                image.width,
                image.height,
                image.format,
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def insert_images(self, images: List[ExtractedImage]) -> List[int]:
        """
        Insert multiple image records.
        
        Args:
            images: List of ExtractedImage objects
            
        Returns:
            List of inserted IDs
        """
        return [self.insert_image(img) for img in images]
    
    def get_images(self, paper_id: int) -> List[ExtractedImage]:
        """
        Get all images for a paper.
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            List of ExtractedImage objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM images WHERE paper_id = ?
                ORDER BY page_number
            """, (paper_id,))
            
            return [self._row_to_image(row) for row in cursor.fetchall()]
    
    def _row_to_image(self, row: sqlite3.Row) -> ExtractedImage:
        """Convert database row to ExtractedImage object."""
        return ExtractedImage(
            id=row["id"],
            paper_id=row["paper_id"],
            file_path=row["file_path"],
            page_number=row["page_number"],
            width=row["width"],
            height=row["height"],
            format=row["format"],
        )
    
    # ==================== Table Operations ====================
    
    def insert_table(self, table: ExtractedTable) -> int:
        """
        Insert a table record.
        
        Args:
            table: ExtractedTable object
            
        Returns:
            ID of the inserted table
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tables (paper_id, file_path, page_number,
                                    row_count, column_count, preview)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                table.paper_id,
                table.file_path,
                table.page_number,
                table.row_count,
                table.column_count,
                table.preview,
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def insert_tables(self, tables: List[ExtractedTable]) -> List[int]:
        """
        Insert multiple table records.
        
        Args:
            tables: List of ExtractedTable objects
            
        Returns:
            List of inserted IDs
        """
        return [self.insert_table(t) for t in tables]
    
    def get_tables(self, paper_id: int) -> List[ExtractedTable]:
        """
        Get all tables for a paper.
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            List of ExtractedTable objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM tables WHERE paper_id = ?
                ORDER BY page_number
            """, (paper_id,))
            
            return [self._row_to_table(row) for row in cursor.fetchall()]
    
    def _row_to_table(self, row: sqlite3.Row) -> ExtractedTable:
        """Convert database row to ExtractedTable object."""
        return ExtractedTable(
            id=row["id"],
            paper_id=row["paper_id"],
            file_path=row["file_path"],
            page_number=row["page_number"],
            row_count=row["row_count"],
            column_count=row["column_count"],
            preview=row["preview"] or "",
        )
    
    # ==================== Statistics ====================
    
    def get_paper_count(self) -> int:
        """Get total number of papers in database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM papers")
            return cursor.fetchone()[0]
    
    def get_statistics(self) -> dict:
        """
        Get overall database statistics.
        
        Returns:
            Dictionary with counts and statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM papers")
            paper_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sections")
            section_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM images")
            image_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tables")
            table_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM papers GROUP BY status
            """)
            status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            return {
                "total_papers": paper_count,
                "total_sections": section_count,
                "total_images": image_count,
                "total_tables": table_count,
                "by_status": status_counts,
            }
