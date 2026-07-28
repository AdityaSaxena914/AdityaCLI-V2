from rich.console import Console
from rich.prompt import Prompt

from constants import APP_NAME, APP_VERSION, PROMPT
from core.runtime import Runtime


class CLI:
    """Interactive CLI."""

    def __init__(self, runtime: Runtime) -> None:
        self._runtime = runtime
        self._console = Console()

    def run(self) -> None:
        self._console.print(
            f"[bold cyan]{APP_NAME}[/] v{APP_VERSION}"
        )
        self._console.print("Type /exit to quit.\n")

        while True:
            try:
                user_input = Prompt.ask(PROMPT).strip()
            except (KeyboardInterrupt, EOFError):
                self._console.print()
                break

            if not user_input:
                continue

            if user_input == "/exit":
                break

            if user_input == "/clear":
                self._runtime.clear()
                self._console.clear()
                continue

            try:
                response = self._runtime.chat(user_input)
                self._console.print(f"\n[bold green]Assistant:[/]")
                self._console.print(response)
                self._console.print()
            except Exception as exc:
                self._console.print(f"[bold red]Error:[/] {exc}")