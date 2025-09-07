import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure comprehensive logging for the dashboard application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, creates timestamped log file.
    """
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Generate log file name if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"dashboard_{timestamp}.log")
    
    # Configure logging format
    log_format = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colored output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5  # 10MB files, keep 5 backups
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)
    
    # Application-specific loggers
    _configure_app_loggers()
    
    logging.info(f"Logging configured - Level: {log_level}, File: {log_file}")

def _configure_app_loggers() -> None:
    """Configure specific loggers for different application components."""
    # Portfolio service logger
    portfolio_logger = logging.getLogger("services.portfolio_service")
    portfolio_logger.setLevel(logging.INFO)
    
    # Data service logger
    data_logger = logging.getLogger("services.data_service")
    data_logger.setLevel(logging.INFO)
    
    # Calculation service logger
    calc_logger = logging.getLogger("services.calculation_service")
    calc_logger.setLevel(logging.WARNING)  # Less verbose for calculations
    
    # UI components logger
    ui_logger = logging.getLogger("ui.components")
    ui_logger.setLevel(logging.WARNING)
    
    # Suppress some noisy third-party loggers
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for console logging."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(name)20s | %(levelname)8s | %(message)s",
            datefmt="%H:%M:%S"
        )
    
    def format(self, record):
        # Get the base formatted message
        formatted = super().format(record)
        
        # Add color if terminal supports it
        if hasattr(os, 'isatty') and os.isatty(2):  # stderr is a terminal
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            formatted = f"{color}{formatted}{reset}"
        
        return formatted

class PerformanceLogger:
    """Context manager for logging performance metrics."""
    
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            if exc_type is None:
                self.logger.info(f"Operation '{self.operation_name}' completed in {duration:.2f}s")
            else:
                self.logger.error(f"Operation '{self.operation_name}' failed after {duration:.2f}s: {exc_val}")

# Convenience function for performance logging
def log_performance(operation_name: str, logger: Optional[logging.Logger] = None):
    """Decorator for logging function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceLogger(f"{func.__name__}({operation_name})", logger):
                return func(*args, **kwargs)
        return wrapper
    return decorator
