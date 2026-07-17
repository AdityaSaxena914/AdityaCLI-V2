import typer

from adityacli.application import Application


def callback(ctx: typer.Context) -> None:
    """Initialize the AdityaCLI application."""

    if ctx.obj is None:
        ctx.obj = {}

    if "application" not in ctx.obj:
        ctx.obj["application"] = Application()