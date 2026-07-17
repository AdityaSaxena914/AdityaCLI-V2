from rich.panel import Panel


def info_panel(renderable, title: str = "") -> Panel:
    return Panel(
        renderable,
        title=title,
        border_style="info",
    )


def success_panel(renderable, title: str = "") -> Panel:
    return Panel(
        renderable,
        title=title,
        border_style="success",
    )


def warning_panel(renderable, title: str = "") -> Panel:
    return Panel(
        renderable,
        title=title,
        border_style="warning",
    )


def error_panel(renderable, title: str = "") -> Panel:
    return Panel(
        renderable,
        title=title,
        border_style="error",
    )