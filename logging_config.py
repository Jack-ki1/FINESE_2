import logging
import sys

def setup_logging():
    """Setup centralized logging configuration for the application."""
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    
    # Prevent adding multiple handlers if called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    
    # Return a logger instance for use in modules
    return logging.getLogger(__name__)