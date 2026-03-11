"""
Structured Logging Configuration for FlavorHub Recipe Manager

This module provides centralized logging setup with:
- Consistent log format across application
- Timestamps for all log entries
- Severity levels (DEBUG, INFO, WARNING, ERROR)
- No modifications to existing code behavior
"""
import logging
import sys
from datetime import datetime


def configure_logging(level=logging.INFO):
    """
    Configure structured logging for the application.
    
    Args:
        level: Logging level (default: logging.INFO)
    
    Usage:
        from logging_config import configure_logging
        configure_logging()
        logger = logging.getLogger(__name__)
        logger.info("Application started")
    """
    
    # Create formatter with timestamp
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        module_name: Name of the module (typically __name__)
    
    Returns:
        logging.Logger instance
    
    Usage:
        from logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Message")
    """
    return logging.getLogger(module_name)
