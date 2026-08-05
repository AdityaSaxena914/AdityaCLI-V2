from rich.console import Console

from adityacli.constants import APP_VERSION


def print_banner(
    console: Console,
    *,
    workspace: str,
    model: str,
    context_window: int,
    continued: bool,
) -> None:
    console.print(
        r"""
 █████╗ ██████╗ ██╗████████╗██╗   ██╗ █████╗
██╔══██╗██╔══██╗██║╚══██╔══╝╚██╗ ██╔╝██╔══██╗
███████║██║  ██║██║   ██║    ╚████╔╝ ███████║
██╔══██║██║  ██║██║   ██║     ╚██╔╝  ██╔══██║
██║  ██║██████╔╝██║   ██║      ██║   ██║  ██║
╚═╝  ╚═╝╚═════╝ ╚═╝   ╚═╝      ╚═╝   ╚═╝  ╚═╝
""",
        style="bold bright_green",
    )

    console.print(
        "[bold bright_white]                    >>>  A D I T Y A C L I  <<<[/]"
    )

    console.print(
        "[dim]              LOCAL-FIRST AI SOFTWARE ENGINEERING ASSISTANT[/]\n"
    )

    console.print(
        "[green]" + ("═" * 86) + "[/]"
    )

    status = [
        ("Runtime", "READY"),
        ("Prompt System", "LOADED"),
        ("Tool Registry", "READY"),
        ("Language Model", model),
        ("Context Window", f"{context_window:,} TOKENS"),
        ("Workspace", workspace),
        ("Session", "CONTINUE" if continued else "NEW"),
        ("Version", f"v{APP_VERSION}"),
    ]

    for key, value in status:
        dots = "." * max(1, 24 - len(key))

        console.print(
            f"[green][+][/green] "
            + f"[white]{key}[/white] "
            + f"[dim]{dots}[/dim] "
            + f"[cyan]{value}[/cyan]"
        )

    console.print(
        "\n[green]"
        + "═" * 86
        + "[/]"
    )

    console.print(
        "\n[bold white]AVAILABLE COMMANDS[/]\n"
    )

    commands = [
        ("/read", "Read one or more project files"),
        ("/search", "Find files or search code"),
        ("/write", "Generate new source files"),
        ("/edit", "Modify existing source files"),
        ("/web", "Search the internet"),
        ("/git", "Run Git operations"),
        ("/clear", "Reset the current session"),
        ("/help", "Show this help screen"),
        ("/exit", "Exit AdityaCLI"),
    ]

    for command, description in commands:
        console.print(
            f"  [cyan]{command:<10}[/cyan]"
            + f"{description}"
        )

    console.print(
        "\n[green]" + ("═" * 86) + "[/]"
    )

    console.print(
        "\n[bold green]READY[/] [dim]Awaiting command...[/]\n"
    )