import typer


def version() -> None:
    """Display the current AdityaCLI version."""

    typer.echo("AdityaCLI v2.0.0")