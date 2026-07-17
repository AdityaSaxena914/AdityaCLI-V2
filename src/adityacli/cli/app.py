import typer

from adityacli.cli.callbacks import callback
from adityacli.cli.commands.version import version
from adityacli.cli.commands.doctor import doctor


app = typer.Typer(
    name="aditya",
    help="Local-first AI Developer Assistant",
    add_completion=False,
    pretty_exceptions_enable=True,
)

app.callback()(callback)
app.command()(version)
app.command(name="doctor")(doctor)