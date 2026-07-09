import logging

def get_default_formatter() -> logging.Formatter:
    """Formatter used for log files."""

    return logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_console_formatter() -> logging.Formatter:
    """Formatter used for console output."""

    return logging.Formatter(
        fmt="[%(levelname)s] %(message)s"
    )


def get_json_formatter() -> logging.Formatter:
    """Placeholder for future JSON logging."""

    raise NotImplementedError("JSON formatter is not implemented yet.")

