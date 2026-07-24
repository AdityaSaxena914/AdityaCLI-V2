from __future__ import annotations

import typer
from rich.console import Console
from rich.prompt import Prompt
from adityacli.application import Application
from adityacli.exceptions import AdityaCLIError

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

            for chunk in app.runtime_manager.execute_stream(prompt):
                console.print(
                    chunk,
                    end="",
                    highlight=False,
                    soft_wrap=True,
                )

            console.print("\n")

        except AdityaCLIError as exc:
            console.print(f"\n[red]{exc.message}[/red]")

            if exc.recovery_hint:
                console.print(
                    f"[yellow]{exc.recovery_hint}[/yellow]"
                )

        except KeyboardInterrupt:
            console.print("\nUse 'exit' or 'quit' to leave.\n")

        except EOFError:
            console.print("\nGoodbye!")
            break