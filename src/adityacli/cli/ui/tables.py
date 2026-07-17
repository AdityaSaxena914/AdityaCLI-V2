from rich.table import Table


def create_table(
    *columns: str,
    title: str | None = None,
) -> Table:
    """Create a standard AdityaCLI table."""

    table = Table(
        title=title,
        header_style="title",
        show_lines=False,
    )

    for column in columns:
        table.add_column(column)

    return table