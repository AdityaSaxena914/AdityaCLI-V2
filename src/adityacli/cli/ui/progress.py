from rich.progress import Progress


def create_progress() -> Progress:
    """Create the standard AdityaCLI progress display."""

    return Progress()