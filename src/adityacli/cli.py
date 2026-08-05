from rich.console import Console
from rich.prompt import Confirm, Prompt

from pathlib import Path

from rich.rule import Rule
from rich.syntax import Syntax

from adityacli.constants import PROMPT
from adityacli.core.models import ChatResponse
from adityacli.core.runtime import Runtime
from adityacli.error_handler import ErrorHandler
from adityacli.ui.diff import build_diff
from adityacli.ui.banner import print_banner

class CLI:
    """Interactive CLI."""

    def __init__(self, runtime: Runtime) -> None:
        self._runtime: Runtime = runtime
        self._console: Console = Console()

    def run(self) -> None:
        print_banner(
            self._console,
            workspace=str(self._runtime.config.workspace.root),
            model=(
                self._runtime.last_response.model
                if self._runtime.last_response
                else "AUTO"
            ),
            context_window=self._runtime.config.lmstudio.context_window,
            continued=self._runtime.continued_session,
        )

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
                confirmed = Confirm.ask(
                    "Clear the current session?",
                    default=False,
                )

                if not confirmed:
                    self._console.print(
                        "[yellow]Session not cleared.[/]\n"
                    )
                    continue

                self._runtime.clear()

                self._console.clear(home=True)

                print_banner(
                    self._console,
                    workspace=str(
                        self._runtime.config.workspace.root
                    ),
                    model=(
                        self._runtime.last_response.model
                        if self._runtime.last_response
                        else "AUTO"
                    ),
                    context_window=self._runtime.config.lmstudio.context_window,
                    continued=False,
                )

                continue

            if user_input == "/help":
                print_banner(
                    self._console,
                    workspace=str(self._runtime.config.workspace.root),
                    model=(
                        self._runtime.last_response.model
                        if self._runtime.last_response is not None
                        else "Waiting for first response..."
                    ),
                    context_window=self._runtime.config.lmstudio.context_window,
                    continued=self._runtime.continued_session,
                )
                continue


            try:
                followup = self._runtime.needs_followup(user_input)

                if followup is not None:
                    response = Prompt.ask(followup).strip()

                    if response:
                        user_input += "\n" + response

                result = self._runtime.chat(user_input)

                if isinstance(result, ChatResponse):
                    self._console.print("\n[bold green]Assistant:[/]")
                    self._console.print(result.content)
                    stats = self._runtime.response_stats

                    if stats is not None:

                        status = (
                            f"[dim]Model:[/] {stats.model} | "
                            + f"[dim]Time:[/] {stats.elapsed_seconds:.2f}s | "
                            + f"[dim]Output:[/] {stats.completion_tokens} tok | "
                            + f"[dim]Speed:[/] {stats.speed:.1f} tok/s"
                        )

                        self._console.print(status)
                    self._console.print()
                    continue

                request = result

                self._console.print()

                for path, content in request.files.items():
                    if user_input.startswith("/edit"):
                        original = Path(path).read_text(
                            encoding="utf-8",
                        )

                        self._console.print(
                            Rule(f" Changes: {path} ")
                        )

                        self._console.print(
                            Syntax(
                                build_diff(
                                    original,
                                    content,
                                ),
                                "diff",
                                line_numbers=False,
                                word_wrap=False,
                            )
                        )

                    else:
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

                        self._console.print(
                            Rule(f" Generated: {path} ")
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

                message = self._runtime.confirmation_message(
                    request,
                    user_input,
                )

                overwrite = Confirm.ask(
                    message,
                    default=False,
                )

                if overwrite:
                    self._runtime.confirm_overwrite(request)

                    self._console.print(
                        "[bold green]Files written successfully.[/]\n"
                    )
                else:
                    self._console.print(
                        "[yellow]Operation cancelled.[/]\n"
                    )

            except Exception as exc:
                self._console.print()

                self._console.print(
                    "[bold red]ERROR[/]"
                )

                self._console.print(
                    ErrorHandler.format(exc)
                )

                self._console.print()