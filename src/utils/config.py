"""
Application configuration management.

Loads configuration from environment variables and .env file,
providing type-safe access to all settings.
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv


class Config:
    """
    Centralized configuration management for PaperIQ.
    
    Loads settings from environment variables with sensible defaults.
    All paths are resolved relative to the project root.
    """
    
    _instance: Optional["Config"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "Config":
        """Singleton pattern to ensure single config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize configuration from environment."""
        if Config._initialized:
            return
        
        # Find project root (where .env file should be)
        self._project_root = self._find_project_root()
        
        # Load .env file if it exists
        env_path = self._project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # Try .env.example as fallback for defaults
            example_path = self._project_root / ".env.example"
            if example_path.exists():
                load_dotenv(example_path)
        
        # File constraints
        self.max_pdf_size_mb: int = int(os.getenv("MAX_PDF_SIZE_MB", "50"))
        self.max_pdf_size_bytes: int = self.max_pdf_size_mb * 1024 * 1024
        self.allowed_extensions: List[str] = os.getenv(
            "ALLOWED_EXTENSIONS", ".pdf"
        ).split(",")
        
        # Processing options
        self.enable_ocr: bool = os.getenv("ENABLE_OCR", "False").lower() == "true"
        self.min_section_length: int = int(os.getenv("MIN_SECTION_LENGTH", "50"))
        self.max_section_length: int = int(os.getenv("MAX_SECTION_LENGTH", "50000"))
        
        # Confidence thresholds
        self.high_confidence_threshold: float = float(
            os.getenv("HIGH_CONFIDENCE_THRESHOLD", "0.8")
        )
        self.medium_confidence_threshold: float = float(
            os.getenv("MEDIUM_CONFIDENCE_THRESHOLD", "0.6")
        )
        self.low_confidence_threshold: float = float(
            os.getenv("LOW_CONFIDENCE_THRESHOLD", "0.5")
        )
        
        # Storage paths (relative to project root)
        self.upload_dir: Path = self._project_root / os.getenv(
            "UPLOAD_DIR", "data/uploads"
        )
        self.images_dir: Path = self._project_root / os.getenv(
            "IMAGES_DIR", "data/extracted/images"
        )
        self.tables_dir: Path = self._project_root / os.getenv(
            "TABLES_DIR", "data/extracted/tables"
        )
        self.db_path: Path = self._project_root / os.getenv(
            "DB_PATH", "data/paperiq.db"
        )
        
        # UI settings
        self.streamlit_page_title: str = os.getenv(
            "STREAMLIT_PAGE_TITLE", "PaperIQ - Research Paper Analyzer"
        )
        self.streamlit_page_icon: str = os.getenv("STREAMLIT_PAGE_ICON", "📄")
        self.streamlit_layout: str = os.getenv("STREAMLIT_LAYOUT", "wide")
        
        # Ensure directories exist
        self._ensure_directories()
        
        Config._initialized = True
    
    def _find_project_root(self) -> Path:
        """
        Find the project root directory.
        
        Looks for markers like requirements.txt, .env, or src/ directory.
        Falls back to current working directory.
        """
        current = Path(__file__).resolve().parent
        
        # Walk up looking for project markers
        for _ in range(5):  # Max 5 levels up
            if (current / "requirements.txt").exists():
                return current
            if (current / ".env").exists():
                return current
            if (current / ".env.example").exists():
                return current
            if current.parent == current:
                break
            current = current.parent
        
        # Fallback to cwd
        return Path.cwd()
    
    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        directories = [
            self.upload_dir,
            self.images_dir,
            self.tables_dir,
            self.db_path.parent,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Create .gitkeep to preserve empty directories
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
    
    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root
    
    def get_confidence_level(self, score: float) -> str:
        """
        Get confidence level string from score.
        
        Args:
            score: Confidence score between 0 and 1
            
        Returns:
            Level string: 'high', 'medium', 'low', or 'very_low'
        """
        if score >= self.high_confidence_threshold:
            return "high"
        elif score >= self.medium_confidence_threshold:
            return "medium"
        elif score >= self.low_confidence_threshold:
            return "low"
        else:
            return "very_low"
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"Config(\n"
            f"  project_root={self._project_root},\n"
            f"  max_pdf_size_mb={self.max_pdf_size_mb},\n"
            f"  enable_ocr={self.enable_ocr},\n"
            f"  db_path={self.db_path}\n"
            f")"
        )


# Global config instance
config = Config()
