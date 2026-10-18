from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text
from textual.widgets import Static


class ConversationMessage(Static):
    """A resizable transcript entry that can be updated during generation."""

    DEFAULT_CSS = "ConversationMessage { height: auto; margin-bottom: 1; }"

    def __init__(self, title: str, text: str, *, markdown: bool = False) -> None:
        super().__init__(markup=False)
        self.title = title
        self.markdown = markdown
        self.set_text(text)

    def set_text(self, text: str, *, incomplete: bool = False) -> None:
        self.text = text
        self.incomplete = incomplete
        title = self.title + (" · incomplete; not saved" if incomplete else "")
        style = "bold #e0a568" if incomplete else (
            "bold #6ed6b5" if self.title == "Assistant" else "bold #94bfff"
        )
        self.update(Group(Text(title, style=style), Markdown(text) if self.markdown else Text(text)))
