from __future__ import annotations

import asyncio
from queue import Empty, Full, Queue
from adityacli.core.operations import check_operation

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Footer, LoadingIndicator, Select, Static

from adityacli.core.models import ChatResponse, OverwriteRequest, PendingSelectionRequest, Role
from adityacli.core.runtime import Runtime
from adityacli.error_handler import ErrorHandler
from adityacli.llm.client import LLMClient
from adityacli.ui.conversation import ConversationMessage
from adityacli.ui.screens import ConfirmationScreen, FileSelectionScreen, FollowupScreen, PromptInput


HELP = """Commands

/read path                 Read project files; append instructions on a new line to analyze
/search query              Find a filename or search code; --literal for plain text
/write {path}              Generate one file, then review and confirm
/edit path                 Edit one file, then review the diff and confirm
/web search words          Search the web
/git {status}              Run an allowed Git command
/remember                  Restore archived history and file context for this model
/clear                     Clear session after confirmation
/help                      Show commands
/exit                      Exit

Enter sends · Ctrl+J inserts a new line · Tab moves focus
Ctrl+X cancels the running request.
Select a model beside the prompt. Refresh after changing models in LM Studio.
Model context, GPU offload and quantization are managed in LM Studio.
Switching models starts fresh context. Use /remember to restore session memory.
"""


class CLI(App[None]):
    """Full-screen terminal UI over the existing deterministic runtime."""

    TITLE = "AdityaCLI"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+l", "clear_session", "Clear", priority=True),
        Binding("ctrl+r", "refresh_models", "Refresh models", priority=True),
        Binding("ctrl+n", "focus_prompt", "Focus input", show=False, priority=True),
        Binding("ctrl+x", "cancel_operation", "Cancel", priority=True),
        Binding("f1", "help", "Help", priority=True),
    ]
    CSS = """
    Screen { background: #101419; color: #d7dee7; }
    #topbar { height: 3; padding: 0 2; background: #181f28; align-vertical: middle; }
    #brand { width: 17; color: #6ed6b5; text-style: bold; }
    #workspace { width: 1fr; color: #a7b5c5; height: 1; }
    #session-state { width: auto; color: #6ed6b5; height: 1; margin-left: 2; }
    #conversation { height: 1fr; margin: 1 2 0 2; padding: 0 1; background: #101419; border: none; }
    #activity { height: 1; margin: 0 3; }
    #spinner { width: 5; height: 1; }
    #status { width: 1fr; height: 1; color: #a7b5c5; }
    #composer { height: auto; margin: 1 2; padding: 0 1; border: round #344455; background: #181f28; }
    #prompt { height: 5; border: none; background: #181f28; padding: 0 1; }
    #prompt:focus { border: none; }
    #composer-tools { height: 3; align-vertical: middle; }
    #model-picker { width: 1fr; }
    #refresh-models { min-width: 11; width: 11; margin-left: 1; }
    #send { min-width: 8; width: 8; margin-left: 1; }
    #input-hint { height: 1; color: #8394a7; padding-left: 1; }
    Footer { background: #181f28; }
    ModalScreen { align: center middle; background: #000000 65%; }
    #dialog { width: 80%; max-width: 110; height: auto; max-height: 90%; padding: 1 2; border: round #6ed6b5; background: #181f28; }
    #dialog.preview-dialog { height: 85%; }
    .dialog-title { height: auto; color: #6ed6b5; text-style: bold; margin-bottom: 1; }
    .dialog-message { height: auto; margin-bottom: 1; }
    .dialog-buttons { height: 3; align-horizontal: right; margin-top: 1; }
    .dialog-buttons Button { margin-left: 1; }
    #preview { height: 1fr; border: solid #344455; background: #101419; }
    #followup { height: 6; }
    """

    def __init__(self, runtime: Runtime, client: LLMClient) -> None:
        super().__init__()
        self._runtime = runtime
        self._client = client
        self._busy = False
        self._refreshing = False
        self._stream_reply: ConversationMessage | None = None
        self._streamed_text = ""
        self._stream_parts: list[str] = []
        self._stream_queue: Queue[tuple[object, str]] = Queue(maxsize=128)
        self._stream_id: object | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Static("ADITYA CLI", id="brand")
            yield Static(str(self._runtime.config.workspace.root), markup=False, id="workspace")
            yield Static("CONTINUED" if self._runtime.continued_session else "NEW SESSION", id="session-state")
        yield VerticalScroll(id="conversation")
        with Horizontal(id="activity"):
            yield LoadingIndicator(id="spinner")
            yield Static("Connecting to LM Studio…", markup=False, id="status")
        with Vertical(id="composer"):
            yield PromptInput(id="prompt", show_line_numbers=False)
            yield Static("Enter sends · Ctrl+J new line · /help commands", id="input-hint")
            with Horizontal(id="composer-tools"):
                yield Select([], prompt="Select a model", id="model-picker", disabled=True)
                yield Button("Refresh", id="refresh-models")
                yield Button("Send", id="send", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(0.05, self._flush_stream)
        self.query_one("#spinner", LoadingIndicator).display = False
        self.query_one("#conversation", VerticalScroll).anchor()
        if self._runtime.continued_session:
            for message in self._runtime.session.messages:
                if message.role is not Role.SYSTEM:
                    self._write_message(message.role.value.title(), message.content, markdown=message.role is Role.ASSISTANT)
        else:
            self._write_message("AdityaCLI", "Chat with your local model. Use /read, /write and /edit to work with project files.")
        self.query_one("#prompt", PromptInput).focus()
        self.refresh_models()

    def _write_message(self, title: str, content: str, *, markdown: bool = False) -> ConversationMessage:
        transcript = self.query_one("#conversation", VerticalScroll)
        message = ConversationMessage(title, content, markdown=markdown)
        transcript.mount(message)
        transcript.scroll_end(animate=False)
        return message

    def _flush_stream(self) -> None:
        """Render at most 20 times/second while retaining every received delta."""
        changed = False
        while True:
            try:
                stream_id, chunk = self._stream_queue.get_nowait()
                if self._stream_id is not None and stream_id is self._stream_id:
                    self._stream_parts.append(chunk)
                    changed = True
            except Empty:
                break
        if not changed:
            return
        self._streamed_text = "".join(self._stream_parts)
        if self._stream_reply is None:
            self._stream_reply = self._write_message("Assistant", self._streamed_text, markdown=True)
            self._set_status("Generating…")
        else:
            self._stream_reply.set_text(self._streamed_text)

    def _receive_chunk(self, chunk: str, stream_id: object) -> None:
        while True:
            check_operation()
            if stream_id is not self._stream_id:
                return
            try:
                self._stream_queue.put((stream_id, chunk), timeout=0.05)
                # Show the first delta immediately; later deltas use the timer.
                if self._stream_reply is None:
                    self.call_from_thread(self._flush_stream)
                return
            except Full:
                pass

    def on_unmount(self) -> None:
        self._runtime.cancel_current()

    def _show_error(self, exc: Exception) -> None:
        self._write_message("Error", ErrorHandler.format(exc))
        self._set_status("Operation failed. Correct the error and retry.")

    def _set_status(self, text: str) -> None:
        self.query_one("#status", Static).update(Text(text))

    def _update_controls(self) -> None:
        self.query_one("#send", Button).disabled = self._busy
        self.query_one("#model-picker", Select).disabled = self._busy or self._refreshing or self._client.selected_model is None
        self.query_one("#refresh-models", Button).disabled = self._busy or self._refreshing
        self.query_one("#spinner", LoadingIndicator).display = self._busy or self._refreshing

    def _model_status(self) -> str:
        model = self._client.selected_model
        if model is None:
            return "No model selected. Start LM Studio's server and refresh models."
        context = f"{model.context_window:,} tokens" if model.context_window else "managed by LM Studio"
        state = (
            "available in LM Studio" if model.loaded is None else
            "loaded" if model.loaded else
            "downloaded · enable JIT loading in LM Studio if needed"
        )
        return f"{model.name} · {state} · context: {context}"

    @work(exclusive=True, group="models", exit_on_error=False)
    async def refresh_models(self) -> None:
        if self._busy:
            return
        self._refreshing = True
        self._update_controls()
        self._set_status("Refreshing LM Studio models…")
        try:
            models = await asyncio.to_thread(self._client.list_models)
            picker = self.query_one("#model-picker", Select)
            # Programmatic refresh events must not act as a user model switch
            # after the async refresh worker has already cleared its flag.
            with self.prevent(Select.Changed):
                picker.set_options([(Text(model.label), model.id) for model in models])
                if models:
                    selected = next((model for model in models if model.id == self._client.model), models[0])
                    self._client.select_model(selected.id)
                    self._runtime.select_model(selected.id)
                    picker.value = selected.id
                else:
                    picker.clear()
            self._set_status(self._model_status())
        except Exception as exc:
            self._set_status("LM Studio unavailable. Start its server, then select Refresh.")
            self.notify(ErrorHandler.format(exc), title="Model discovery failed", severity="error", timeout=8)
        finally:
            self._refreshing = False
            self._update_controls()

    @on(Select.Changed, "#model-picker")
    def select_model(self, event: Select.Changed) -> None:
        if not event.select.is_attached or self._refreshing or self._busy:
            return
        # set_options queues an empty-selection event before the new value.
        # Ignore stale events and accept only actual string model IDs. The
        # empty-selection sentinel differs between supported Textual versions.
        if event.value != event.select.value:
            return
        if not isinstance(event.value, str):
            if self._client.selected_model is not None:
                event.select.value = self._client.model
            return
        if event.value == self._client.model:
            return
        try:
            self._client.select_model(event.value)
            changed = self._runtime.select_model(event.value)
            self._set_status(self._model_status() + (" · fresh context; /remember to restore history" if changed else ""))
        except Exception as exc:
            self._show_error(exc)

    @on(Button.Pressed, "#refresh-models")
    def refresh_pressed(self) -> None:
        self.action_refresh_models()

    @on(Button.Pressed, "#send")
    def send_pressed(self) -> None:
        self._submit()

    @on(PromptInput.Submitted)
    def prompt_submitted(self, event: PromptInput.Submitted) -> None:
        event.stop()
        self._submit()

    def _submit(self) -> None:
        if self._busy:
            return
        prompt = self.query_one("#prompt", PromptInput)
        text = prompt.text.strip()
        if not text:
            return
        if text == "/exit":
            self.action_quit()
            return
        if text == "/help":
            prompt.clear()
            self.action_help()
            return
        if text == "/clear":
            prompt.clear()
            self.action_clear_session()
            return
        if self._refreshing:
            self.notify("Wait for model discovery to finish.")
            return
        # Select.Changed is queued by Textual. Reconcile the visible choice
        # before claiming busy state so an immediate Send uses that model.
        selected = self.query_one("#model-picker", Select).value
        if isinstance(selected, str) and selected != self._client.model:
            try:
                self._client.select_model(selected)
                self._runtime.select_model(selected)
            except Exception as exc:
                self._show_error(exc)
                return
        # Claim the interaction before scheduling, preventing double sends.
        self._busy = True
        self._update_controls()
        prompt.clear()
        self.process_input(text)

    @work(group="interaction", exit_on_error=False)
    async def process_input(self, text: str) -> None:
        self._stream_reply = None
        self._streamed_text = ""
        self._stream_parts = []
        stream_id = self._stream_id = object()
        receive_chunk = lambda chunk: self._receive_chunk(chunk, stream_id)
        try:
            followup = self._runtime.needs_followup(text)
            if followup:
                answer = await self.push_screen_wait(FollowupScreen(followup))
                if answer is None:
                    self.query_one("#prompt", PromptInput).load_text(text)
                    self._set_status("Operation cancelled.")
                    return
                text += "\n" + answer
            self._write_message("You", text)
            self._set_status("Processing…")
            result = await asyncio.to_thread(self._runtime.chat, text, on_chunk=receive_chunk)
            while isinstance(result, PendingSelectionRequest):
                choice = await self.push_screen_wait(FileSelectionScreen(result))
                if choice is None:
                    self._set_status("File selection cancelled.")
                    return
                result = await asyncio.to_thread(
                    self._runtime.confirm_read_selection, result, choice, on_chunk=receive_chunk,
                )
            if isinstance(result, OverwriteRequest):
                confirmed = await self.push_screen_wait(ConfirmationScreen(
                    self._runtime.confirmation_message(result, text),
                    request=result, workspace=self._runtime.config.workspace.root,
                    editing=text.startswith("/edit"),
                ))
                if confirmed:
                    await asyncio.to_thread(self._runtime.confirm_overwrite, result)
                    self._write_message("Files", "Files written successfully.")
                else:
                    self._runtime.cancel_overwrite(result)
                    self._write_message("Files", "Operation cancelled.")
            elif isinstance(result, ChatResponse):
                self._flush_stream()
                if self._stream_reply is not None:
                    self._stream_reply.set_text(result.content)
                else:
                    self._write_message("Assistant", result.content, markdown=self._runtime.last_response is not None)
            stats = self._runtime.response_stats
            if stats:
                self._set_status(f"{stats.model} · {stats.elapsed_seconds:.2f}s · {stats.completion_tokens} tokens · {stats.speed:.1f} tok/s")
            else:
                self._set_status(self._model_status())
        except Exception as exc:
            self._flush_stream()
            if self._stream_reply is not None:
                self._stream_reply.set_text(self._streamed_text, incomplete=True)
            self._show_error(exc)
        finally:
            self._flush_stream()
            self._stream_id = None
            self._stream_reply = None
            self._streamed_text = ""
            self._stream_parts = []
            self._busy = False
            self._update_controls()
            self.query_one("#prompt", PromptInput).focus()

    def action_refresh_models(self) -> None:
        if not self._busy and not self._refreshing:
            self.refresh_models()

    def action_focus_prompt(self) -> None:
        if len(self.screen_stack) == 1:
            self.query_one("#prompt", PromptInput).focus()

    def action_help(self) -> None:
        if len(self.screen_stack) == 1:
            self._write_message("Help", HELP)

    def action_clear_session(self) -> None:
        if self._busy or self._refreshing or len(self.screen_stack) > 1:
            return
        self._busy = True
        self._update_controls()
        self.clear_session()

    @work(group="interaction", exit_on_error=False)
    async def clear_session(self) -> None:
        try:
            confirmed = await self.push_screen_wait(ConfirmationScreen("Clear conversation history and cached files?"))
            if confirmed:
                await asyncio.to_thread(self._runtime.clear)
                await self.query_one("#conversation", VerticalScroll).remove_children()
                self.query_one("#prompt", PromptInput).load_text("")
                self._stream_reply = None
                self._streamed_text = ""
                self.query_one("#conversation", VerticalScroll).anchor()
                self.query_one("#session-state", Static).update("NEW SESSION")
                self._set_status("New session · chat history, file cache, and prompt cleared.")
            else:
                self._set_status("Session not cleared.")
        except Exception as exc:
            self._show_error(exc)
        finally:
            self._busy = False
            self._update_controls()
            self.query_one("#prompt", PromptInput).focus()

    def action_quit(self) -> None:
        if self._busy:
            self.notify("Wait for the operation to finish, or cancel the open dialog.")
            return
        self.exit()

    def action_cancel_operation(self) -> None:
        if self._busy and len(self.screen_stack) == 1:
            self._runtime.cancel_current()
            self._set_status("Cancelling operation…")
