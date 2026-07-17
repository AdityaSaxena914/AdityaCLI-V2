from rich.markdown import Markdown


def render_markdown(content: str) -> Markdown:
    """Convert Markdown text into a Rich renderable."""

    return Markdown(content)