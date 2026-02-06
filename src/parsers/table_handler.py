"""
Table extraction from PDF files.

Extracts tables and converts them to structured CSV format.
Uses Camelot for accurate table detection and extraction.
"""

from pathlib import Path
from typing import List, Optional
import pandas as pd

from models import ExtractedTable
from utils import Config, get_logger


logger = get_logger("paperiq.tables")


class TableHandler:
    """
    Handles extraction of tables from PDF files.
    
    Uses Camelot-py for table detection and extraction,
    with fallback to pdfplumber for complex layouts.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize table handler with configuration.
        
        Args:
            config: Configuration instance (uses default if not provided)
        """
        self.config = config or Config()
        self.tables_dir = self.config.tables_dir
        self._camelot_available = self._check_camelot()
    
    def _check_camelot(self) -> bool:
        """Check if Camelot is available."""
        try:
            import camelot
            return True
        except ImportError:
            logger.warning("Camelot not available, using pdfplumber fallback")
            return False
    
    def extract_tables(
        self,
        pdf_path: Path,
        paper_id: int
    ) -> List[ExtractedTable]:
        """
        Extract all tables from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            paper_id: ID of the paper (for naming files)
            
        Returns:
            List of ExtractedTable objects
        """
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return []
        
        if self._camelot_available:
            return self._extract_with_camelot(pdf_path, paper_id)
        else:
            return self._extract_with_pdfplumber(pdf_path, paper_id)
    
    def _extract_with_camelot(
        self,
        pdf_path: Path,
        paper_id: int
    ) -> List[ExtractedTable]:
        """
        Extract tables using Camelot.
        
        Args:
            pdf_path: Path to PDF file
            paper_id: Paper ID for file naming
            
        Returns:
            List of ExtractedTable objects
        """
        import camelot
        
        extracted_tables: List[ExtractedTable] = []
        
        try:
            # Try lattice flavor first (for tables with borders)
            tables = camelot.read_pdf(
                str(pdf_path),
                pages="all",
                flavor="lattice",
                suppress_stdout=True
            )
            
            # If no tables found, try stream flavor (for borderless tables)
            if len(tables) == 0:
                tables = camelot.read_pdf(
                    str(pdf_path),
                    pages="all",
                    flavor="stream",
                    suppress_stdout=True
                )
            
            for idx, table in enumerate(tables):
                try:
                    df = table.df
                    
                    # Skip empty or single-cell tables
                    if df.empty or (len(df) == 1 and len(df.columns) == 1):
                        continue
                    
                    # Save to CSV
                    table_num = idx + 1
                    csv_path = self._save_table_csv(df, paper_id, table_num)
                    
                    if csv_path:
                        # Get page number from Camelot
                        page_num = table.page if hasattr(table, 'page') else 1
                        
                        extracted_tables.append(ExtractedTable(
                            paper_id=paper_id,
                            file_path=str(csv_path),
                            page_number=page_num,
                            row_count=len(df),
                            column_count=len(df.columns),
                            preview=self._generate_preview(df),
                        ))
                        
                except Exception as e:
                    logger.warning(f"Failed to process table {idx}: {e}")
                    continue
            
            logger.info(f"Extracted {len(extracted_tables)} tables with Camelot")
            return extracted_tables
            
        except Exception as e:
            logger.error(f"Camelot extraction failed: {e}")
            # Fallback to pdfplumber
            return self._extract_with_pdfplumber(pdf_path, paper_id)
    
    def _extract_with_pdfplumber(
        self,
        pdf_path: Path,
        paper_id: int
    ) -> List[ExtractedTable]:
        """
        Extract tables using pdfplumber as fallback.
        
        Args:
            pdf_path: Path to PDF file
            paper_id: Paper ID for file naming
            
        Returns:
            List of ExtractedTable objects
        """
        import pdfplumber
        
        extracted_tables: List[ExtractedTable] = []
        table_counter = 0
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_tables = page.extract_tables()
                        
                        for table_data in page_tables:
                            if not table_data or len(table_data) < 2:
                                continue
                            
                            # Convert to DataFrame
                            # Use first row as header if it looks like headers
                            if self._is_header_row(table_data[0]):
                                df = pd.DataFrame(table_data[1:], columns=table_data[0])
                            else:
                                df = pd.DataFrame(table_data)
                            
                            # Skip empty tables
                            if df.empty:
                                continue
                            
                            table_counter += 1
                            csv_path = self._save_table_csv(df, paper_id, table_counter)
                            
                            if csv_path:
                                extracted_tables.append(ExtractedTable(
                                    paper_id=paper_id,
                                    file_path=str(csv_path),
                                    page_number=page_num,
                                    row_count=len(df),
                                    column_count=len(df.columns),
                                    preview=self._generate_preview(df),
                                ))
                                
                    except Exception as e:
                        logger.warning(f"Failed to extract tables from page {page_num}: {e}")
                        continue
            
            logger.info(f"Extracted {len(extracted_tables)} tables with pdfplumber")
            return extracted_tables
            
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return []
    
    def _is_header_row(self, row: List) -> bool:
        """
        Check if a row looks like a header row.
        
        Heuristic: Header rows typically have shorter, non-numeric values.
        
        Args:
            row: List of cell values
            
        Returns:
            True if row appears to be headers
        """
        if not row:
            return False
        
        # Count string-like cells
        string_count = 0
        for cell in row:
            cell_str = str(cell).strip() if cell else ""
            if cell_str and not cell_str.replace(".", "").replace("-", "").isdigit():
                if len(cell_str) < 50:  # Headers are usually short
                    string_count += 1
        
        return string_count >= len(row) * 0.5
    
    def _save_table_csv(
        self,
        df: pd.DataFrame,
        paper_id: int,
        table_num: int
    ) -> Optional[Path]:
        """
        Save DataFrame to CSV file.
        
        Args:
            df: Pandas DataFrame
            paper_id: Paper ID for file naming
            table_num: Table number for file naming
            
        Returns:
            Path to saved file, or None on failure
        """
        try:
            filename = f"paper_{paper_id}_table_{table_num}.csv"
            save_path = self.tables_dir / filename
            
            df.to_csv(save_path, index=False, encoding="utf-8")
            
            logger.debug(f"Saved table: {filename} ({len(df)} rows)")
            return save_path
            
        except Exception as e:
            logger.warning(f"Failed to save table: {e}")
            return None
    
    def _generate_preview(self, df: pd.DataFrame, max_rows: int = 5) -> str:
        """
        Generate a text preview of a table.
        
        Args:
            df: Pandas DataFrame
            max_rows: Maximum rows to include in preview
            
        Returns:
            Preview string
        """
        try:
            preview_df = df.head(max_rows)
            return preview_df.to_string(index=False, max_colwidth=30)
        except Exception:
            return ""
    
    def read_table_csv(self, csv_path: Path) -> Optional[pd.DataFrame]:
        """
        Read a saved table CSV back into a DataFrame.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            DataFrame or None on failure
        """
        try:
            if not csv_path.exists():
                return None
            return pd.read_csv(csv_path, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read table CSV: {e}")
            return None
    
    def cleanup_paper_tables(self, paper_id: int) -> int:
        """
        Delete all tables associated with a paper.
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            Number of files deleted
        """
        deleted = 0
        pattern = f"paper_{paper_id}_table_*.csv"
        
        for csv_file in self.tables_dir.glob(pattern):
            try:
                csv_file.unlink()
                deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete {csv_file}: {e}")
        
        return deleted
