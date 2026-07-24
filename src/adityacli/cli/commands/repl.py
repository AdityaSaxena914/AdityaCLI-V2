from __future__ import annotations

import typer
from rich.console import Console
from rich.prompt import Prompt

from adityacli.agent import AgentRequest
from adityacli.application import Application


console = Console()


def repl(
    ctx: typer.Context,
) -> None:
    """Start an interactive chat session."""

    app: Application = ctx.obj["application"]

    console.print("[bold cyan]AdityaCLI v2[/bold cyan]")
    console.print("Type 'exit' or 'quit' to leave.\n")

    while True:
        try:
            prompt = Prompt.ask("[bold green]You[/bold green]")

            if prompt.strip().lower() in {
                "exit",
                "quit",
            }:
                console.print("\nGoodbye!")
                break

            if not prompt.strip():
                continue

            console.print("[bold blue]Assistant[/bold blue]", end=": ")

            response = app.runtime_manager.execute(prompt)
            console.print(response.content)

            console.print("\n")

        except KeyboardInterrupt:
            console.print("\nUse 'exit' or 'quit' to leave.\n")

        except EOFError:
            console.print("\nGoodbye!")
            break