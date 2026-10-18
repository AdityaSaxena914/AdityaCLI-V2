from pathlib import Path

from rich.syntax import Syntax
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, RichLog, Select, Static, TextArea

from adityacli.core.models import OverwriteRequest, PendingSelectionRequest
from adityacli.ui.diff import build_diff
from adityacli.core.workspace_guard import WorkspaceGuard
from adityacli.exceptions import AdityaCLIError


class PromptInput(TextArea):
    """Enter submits; Ctrl+J inserts a newline across terminal types."""

    BINDINGS = [
        Binding("enter", "submit", "Send", priority=True),
        Binding("ctrl+j", "newline", "New line", priority=True),
        Binding("shift+enter", "newline", "New line", show=False, priority=True),
    ]

    class Submitted(Message):
        def __init__(self, text: str) -> None:
            super().__init__()
            self.text = text

    def action_submit(self) -> None:
        if self.text.strip():
            self.post_message(self.Submitted(self.text.strip()))

    def action_newline(self) -> None:
        self.insert("\n")


class ConfirmationScreen(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(
        self, message: str, *, request: OverwriteRequest | None = None,
        workspace: Path | None = None, editing: bool = False,
    ) -> None:
        super().__init__()
        self.message = message
        self.request = request
        self.workspace = workspace
        self.editing = editing

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog", classes="preview-dialog" if self.request else ""):
            yield Static("Review changes" if self.request else "Clear session", classes="dialog-title")
            yield Static(self.message, markup=False, classes="dialog-message")
            if self.request:
                yield RichLog(id="preview", highlight=False, markup=False, wrap=False)
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Apply changes" if self.request else "Clear", id="confirm", variant="primary")

    def on_mount(self) -> None:
        if self.request:
            preview = self.query_one("#preview", RichLog)
            for path, content in self.request.files.items():
                preview.write(Text(path, style="bold cyan"))
                if self.editing and self.workspace is not None:
                    try:
                        original = WorkspaceGuard(self.workspace).read_text(path)
                    except (OSError, UnicodeError, AdityaCLIError) as exc:
                        preview.write(Text(f"Cannot preview current file: {exc}", style="red"))
                        self.query_one("#confirm", Button).disabled = True
                        continue
                    preview.write(Syntax(build_diff(original, content), "diff", background_color="default"))
                else:
                    lexer = Syntax.guess_lexer(path, content)
                    preview.write(Syntax(content, lexer, line_numbers=True, background_color="default"))
        self.query_one("#cancel", Button).focus()

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#confirm")
    def confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class FollowupScreen(ModalScreen[str | None]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, question: str) -> None:
        super().__init__()
        self.question = question

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self.question, markup=False, classes="dialog-title")
            yield PromptInput(id="followup", show_line_numbers=False)
            yield Static("Enter to continue · Ctrl+J for a new line", classes="dialog-message")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Continue", id="continue", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#followup", PromptInput).focus()

    @on(PromptInput.Submitted)
    def submitted(self, event: PromptInput.Submitted) -> None:
        event.stop()
        self.dismiss(event.text)

    @on(Button.Pressed, "#continue")
    def continue_prompt(self) -> None:
        text = self.query_one("#followup", PromptInput).text.strip()
        if text:
            self.dismiss(text)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class FileSelectionScreen(ModalScreen[int | None]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, request: PendingSelectionRequest) -> None:
        super().__init__()
        self.request = request

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Select a file", classes="dialog-title")
            yield Static(f"'{self.request.query}' matched multiple files.", markup=False, classes="dialog-message")
            yield Select(
                [(Text(path), i) for i, path in enumerate(self.request.candidates)],
                prompt="Choose a file", id="file-choice",
            )
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Read file", id="read-file", variant="primary", disabled=True)

    @on(Select.Changed, "#file-choice")
    def selection_changed(self, event: Select.Changed) -> None:
        value = event.select.value
        self.query_one("#read-file", Button).disabled = not (
            type(value) is int and 0 <= value < len(self.request.candidates)
        )

    @on(Button.Pressed, "#read-file")
    def select_file(self) -> None:
        value = self.query_one("#file-choice", Select).value
        if type(value) is int and 0 <= value < len(self.request.candidates):
            self.dismiss(value)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
