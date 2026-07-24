from __future__ import annotations

import typer
from rich.console import Console

from adityacli.agent import AgentRequest
from adityacli.application import Application

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
        response = app.runtime_manager.execute(prompt)
        console.print(response.content)

    except KeyboardInterrupt:
        console.print(
            "\n[red]Generation interrupted.[/red]"
        )