import platform
from pathlib import Path

import typer

from adityacli.application import Application
from adityacli.cli import console
from adityacli.cli.ui import info_panel
from adityacli.cli.ui import create_table


def doctor(ctx: typer.Context) -> None:
    """Display environment and application diagnostics."""

    app: Application = ctx.obj["application"]

    console.print(
        info_panel(
            "Environment diagnostics",
            title="AdityaCLI Doctor",
        )
    )

    table = create_table(
        "Property",
        "Value",
        title="Environment",
    )

    table.add_row(
        "Python",
        platform.python_version(),
    )

    table.add_row(
        "OS",
        f"{platform.system()} {platform.release()}",
    )

    table.add_row(
        "Directory",
        str(Path.cwd()),
    )

    table.add_row(
        "Application",
        "Initialized",
    )

    table.add_row(
        "Ready",
        "Yes" if app.ready else "No",
    )

    console.print(table)

    console.print(
        "Environment check completed successfully.",
        style="success",
    )