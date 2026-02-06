"""
Logging configuration for PaperIQ.

Provides structured logging with console and optional file output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime


# Store logger instances to avoid recreation
_loggers: Dict[str, logging.Logger] = {}


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with ANSI colors for console output.
    
    Colors:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Red background
    """
    
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[41m",  # Red background
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color."""
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = "paperiq",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    use_colors: bool = True
) -> logging.Logger:
    """
    Set up and configure a logger.
    
    Args:
        name: Logger name (default: 'paperiq')
        level: Logging level (default: INFO)
        log_file: Optional path to log file
        use_colors: Whether to use colored console output
        
    Returns:
        Configured logger instance
    """
    # Return existing logger if already configured
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if use_colors and sys.stdout.isatty():
        console_format = ColoredFormatter(
            "%(levelname)s: %(message)s"
        )
    else:
        console_format = logging.Formatter(
            "%(levelname)s: %(message)s"
        )
    
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    _loggers[name] = logger
    return logger


def get_logger(name: str = "paperiq") -> logging.Logger:
    """
    Get an existing logger or create a new one.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]
    return setup_logger(name)


class ProcessingLogger:
    """
    Context manager for logging processing steps.
    
    Provides timing information and structured output for
    multi-step processing operations.
    """
    
    def __init__(self, operation: str, logger: Optional[logging.Logger] = None):
        """
        Initialize processing logger.
        
        Args:
            operation: Name of the operation being performed
            logger: Logger instance (uses default if not provided)
        """
        self.operation = operation
        self.logger = logger or get_logger()
        self.start_time: Optional[datetime] = None
    
    def __enter__(self) -> "ProcessingLogger":
        """Start timing the operation."""
        self.start_time = datetime.now()
        self.logger.info(f"Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Log completion or failure."""
        elapsed = datetime.now() - self.start_time
        elapsed_str = f"{elapsed.total_seconds():.2f}s"
        
        if exc_type is not None:
            self.logger.error(
                f"Failed: {self.operation} ({elapsed_str}) - {exc_val}"
            )
            return False
        
        self.logger.info(f"Completed: {self.operation} ({elapsed_str})")
        return False
    
    def step(self, message: str) -> None:
        """Log an intermediate step."""
        self.logger.info(f"  → {message}")
    
    def warning(self, message: str) -> None:
        """Log a warning during processing."""
        self.logger.warning(f"  ⚠ {message}")
