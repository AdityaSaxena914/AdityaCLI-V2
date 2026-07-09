import logging
from .handlers import (
    create_file_handler,
    create_console_handler,
    create_error_handler
)
from adityacli.config import settings

class LoggerManager:
    """Central manager responsible for creating and caching loggers."""

    def __init__(self) -> None:
        self._loggers: dict[str, logging.Logger] ={}

    def get_logger(self, name: str) -> logging.Logger:
        """Return a configured logger for the given subssystem."""

        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(f"adityacli.{name}")

        logger.setLevel(settings.logging.log_level)
        logger.propagate = False

        logger.addHandler(create_file_handler(name))
        logger.addHandler(create_console_handler())
        logger.addHandler(create_error_handler())

        self._loggers[name] = logger

        return logger
    
_manager = LoggerManager()

def get_logger(name: str) -> logging.Logger:
    """Return a subsystem logger."""
    return _manager.get_logger(name)