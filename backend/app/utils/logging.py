"""
Structured logging configuration with JSON formatting.
"""
import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger
from app.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add service name
        log_record['service'] = settings.APP_NAME
        
        # Add logger name
        log_record['logger'] = record.name


def setup_logging():
    """Configure application logging."""
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler (always enabled in development)
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT == "json":
        console_formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handlers
    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Access log handler
    if settings.LOG_ACCESS:
        access_handler = logging.handlers.RotatingFileHandler(
            log_dir / "access.log",
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        access_handler.setFormatter(formatter)
        access_handler.setLevel(logging.INFO)
        access_logger = logging.getLogger("access")
        access_logger.addHandler(access_handler)
    
    # Error log handler
    if settings.LOG_ERROR:
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "error.log",
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
    
    # Performance log handler
    if settings.LOG_PERFORMANCE:
        perf_handler = logging.handlers.RotatingFileHandler(
            log_dir / "performance.log",
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        perf_handler.setFormatter(formatter)
        perf_handler.setLevel(logging.INFO)
        perf_logger = logging.getLogger("performance")
        perf_logger.addHandler(perf_handler)
    
    # Audit log handler
    if settings.LOG_AUDIT:
        audit_handler = logging.handlers.RotatingFileHandler(
            log_dir / "audit.log",
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        audit_handler.setFormatter(formatter)
        audit_handler.setLevel(logging.INFO)
        audit_logger = logging.getLogger("audit")
        audit_logger.addHandler(audit_handler)
    
    # Application log handler
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    app_handler.setFormatter(formatter)
    root_logger.addHandler(app_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


# Convenience loggers
access_logger = logging.getLogger("access")
performance_logger = logging.getLogger("performance")
audit_logger = logging.getLogger("audit")
