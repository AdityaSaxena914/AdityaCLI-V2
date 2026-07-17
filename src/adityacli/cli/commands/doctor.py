import platform
from pathlib import Path

from adityacli.cli.console import console
from adityacli.cli.ui.panels import info_panel
from adityacli.cli.ui.tables import create_table


def doctor() -> None:
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

    console.print(table)

    console.print(
        "Environment check completed successfully.",
        style="success",
    )