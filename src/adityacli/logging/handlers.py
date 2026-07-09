import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .formatters import (
    get_default_formatter,
    get_console_formatter,
    get_json_formatter
)



LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def create_file_handler(name: str) -> RotatingFileHandler:
    """Create a file handler for a subsystem logger."""

    log_file = LOG_DIR / f"{name}.log"

    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )

    handler.setFormatter(get_default_formatter())

    return handler



_console_handler: logging.StreamHandler | None = None

def create_console_handler() -> logging.StreamHandler:
    """Create a console handler."""

    global _console_handler

    if _console_handler is not None:
        return _console_handler

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(get_console_formatter())

    _console_handler = handler

    return handler


_error_handler: logging.FileHandler | None = None

def create_error_handler() -> logging.FileHandler:
    """Return the shared error log hadnler."""\
    
    global _error_handler

    if _error_handler is not None:
        return _error_handler
    
    log_file = LOG_DIR / "error.log"

    handler = logging.FileHandler(
        filename=log_file,
        encoding="utf-8",
    )

    handler.setLevel(logging.ERROR)

    handler.setFormatter(get_default_formatter())

    _error_handler = handler

    return handler


