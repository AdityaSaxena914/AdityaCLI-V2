from rich.console import Console
from rich.prompt import Confirm, Prompt

from adityacli.constants import APP_NAME, APP_VERSION, PROMPT
from adityacli.core.models import ChatResponse, OverwriteRequest
from adityacli.core.runtime import Runtime


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
                result = self._runtime.chat(user_input)

                if isinstance(result, ChatResponse):
                    self._console.print("\n[bold green]Assistant:[/]")
                    self._console.print(result.content)
                    self._console.print()
                    continue

                if isinstance(result, OverwriteRequest):
                    self._console.print()

                    self._console.print(
                        "[bold yellow]Generated files:[/]"
                    )

                    for path in sorted(result.files):
                        self._console.print(f"  • {path}")

                    overwrite = Confirm.ask(
                        "Write these files?",
                        default=False,
                    )

                    if overwrite:
                        self._runtime.confirm_overwrite(result)

                        self._console.print(
                            "[bold green]Files written successfully.[/]\n"
                        )
                    else:
                        self._console.print(
                            "[yellow]Operation cancelled.[/]\n"
                        )

            except Exception as exc:
                self._console.print(
                    f"[bold red]Error:[/] {exc}"
                )