import shlex

from adityacli.core.models import Command, Tool
from adityacli.exceptions import InvalidCommandError, InvalidSyntaxError, InvalidPathError


class Parser:
    """Command parser."""

    def parse(self, text: str) -> Command | None:
        text = text.strip()

        if not text.startswith("/"):
            return None

        lines = text.splitlines()
        command_line = lines[0].strip()
        prompt = "\n".join(lines[1:]).strip()

        parts = command_line.split(maxsplit=1)
        tool_name = parts[0][1:]

        try:
            tool = Tool(tool_name)
        except ValueError as exc:
            raise InvalidCommandError(f"Unknown command: {tool_name}") from exc

        arguments: list[str] = []

        if len(parts) == 2:
            raw_args = parts[1].strip()

            if raw_args:
                if tool in {Tool.WRITE, Tool.GIT}:
                    if not (raw_args.startswith("{") and raw_args.endswith("}")):
                        raise InvalidSyntaxError(
                            "Expected arguments enclosed in '{}'."
                        )

                    raw_args = raw_args[1:-1].strip()
                elif tool is Tool.READ:
                    # Braces are optional for READ: '/read runtime' and
                    # '/read {runtime.py}' must both reach the resolver.
                    if raw_args.startswith("{") and raw_args.endswith("}"):
                        raw_args = raw_args[1:-1].strip()

                if tool is Tool.SEARCH:
                    # A search pattern may contain spaces and regex escapes.
                    if len(raw_args) >= 2 and raw_args[0] == raw_args[-1] and raw_args[0] in "\"'":
                        raw_args = raw_args[1:-1]
                    arguments = [raw_args] if raw_args else []
                elif tool is Tool.WEB:
                    arguments = raw_args.split()
                else:
                    lexer = shlex.shlex(raw_args, posix=True)
                    lexer.whitespace_split = True
                    lexer.commenters = ""
                    lexer.escape = ""  # Preserve Windows paths and literal backslashes.
                    try:
                        arguments = list(lexer)
                    except ValueError as exc:
                        raise InvalidSyntaxError(str(exc)) from exc

        return Command(
            tool=tool,
            arguments=arguments,
            prompt=prompt,
        )


    def validate(
        self,
        command: Command,
    ) -> None:
        match command.tool:
            case Tool.REMEMBER:
                if command.arguments or command.prompt:
                    raise InvalidSyntaxError("/remember does not accept arguments.")
            case Tool.WRITE:
                if len(command.arguments) != 1:
                    raise InvalidPathError(
                        "Exactly one file path is currently supported."
                    )
                
            case Tool.EDIT:
                if len(command.arguments) != 1:
                    raise InvalidPathError(
                        "Expected exactly one file path."
                    )

            case Tool.READ:
                if not command.arguments:
                    raise InvalidPathError(
                        "At least one file path is required."
                    )

            case Tool.SEARCH:
                if len(command.arguments) != 1:
                    raise InvalidSyntaxError(
                        "Expected exactly one search query."
                    )

            case Tool.WEB:
                if not command.arguments:
                    raise InvalidSyntaxError(
                        "Expected a search query."
                    )

            case _:
                pass
