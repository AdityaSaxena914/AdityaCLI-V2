import typer

from adityacli.cli.callbacks import callback
from adityacli.cli.commands import version
from adityacli.cli.commands import doctor
from adityacli.cli.commands import chat
from adityacli.cli.commands import repl

app = typer.Typer(
    name="aditya",
    help="Local-first AI Developer Assistant",
    add_completion=False,
    pretty_exceptions_enable=True,
)

app.callback()(callback)

app.command()(version)
app.command(name="doctor")(doctor)
app.command()(chat)
app.command()(repl)