from __future__ import annotations

import typer
from rich.console import Console
from adityacli.application import Application
from adityacli.exceptions import AdityaCLIError

console = Console()


def chat(
    ctx: typer.Context,
    prompt: str = typer.Argument(
        ...,
        help="Prompt to send to the agent.",
    ),
) -> None:
    """Send a prompt to the default agent."""

    app: Application = ctx.obj["application"]

    try:
        for chunk in app.runtime_manager.execute_stream(prompt):
            console.print(
                chunk,
                end="",
                highlight=False,
                soft_wrap=True,
            )

        console.print()

    except AdityaCLIError as exc:
        console.print(f"[red]{exc.message}[/red]")

        if exc.recovery_hint:
            console.print(f"[yellow]{exc.recovery_hint}[/yellow]")

    except KeyboardInterrupt:
        console.print(
            "\n[red]Generation interrupted.[/red]"
        )