from rich.console import Console
from rich.prompt import Confirm, Prompt

from pathlib import Path

from rich.rule import Rule
from rich.syntax import Syntax

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
                if user_input.startswith("/write") and "\n" not in user_input:
                    description = Prompt.ask(
                        "What would you like to generate?"
                    ).strip()

                    if description:
                        user_input = (
                            f"{user_input}\n{description}"
                        )

                if user_input.startswith("/edit") and "\n" not in user_input:
                    instruction = Prompt.ask(
                        "What would you like to change?"
                    ).strip()

                    if instruction:
                        user_input = (
                            f"{user_input}\n{instruction}"
                        )

                result = self._runtime.chat(user_input)

                if isinstance(result, ChatResponse):
                    self._console.print("\n[bold green]Assistant:[/]")
                    self._console.print(result.content)
                    self._console.print()
                    continue

                if isinstance(result, OverwriteRequest):
                    self._console.print()

                    existing_files = [
                        path
                        for path in result.files
                        if Path(path).exists()
                    ]

                    is_overwrite = bool(existing_files)

                    for path, content in result.files.items():
                        suffix = Path(path).suffix.lower()

                        lexer = {
                            ".py": "python",
                            ".md": "markdown",
                            ".json": "json",
                            ".toml": "toml",
                            ".yaml": "yaml",
                            ".yml": "yaml",
                            ".html": "html",
                            ".css": "css",
                            ".js": "javascript",
                            ".ts": "typescript",
                        }.get(suffix, "text")

                        title = (
                            "Generated"
                            if user_input.startswith("/write")
                            else "Preview"
                        )

                        self._console.print(
                            Rule(f" {title}: {path} ")
)

                        self._console.print(
                            Syntax(
                                content,
                                lexer=lexer,
                                line_numbers=True,
                                word_wrap=False,
                            )
                        )

                        self._console.print()

                    if user_input.startswith("/write"):
                        if is_overwrite:
                            message = "Overwrite existing file(s)?"
                        else:
                            message = "Write new file(s)?"
                    else:
                        message = "Apply these changes?"

                    overwrite = Confirm.ask(
                        message,
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