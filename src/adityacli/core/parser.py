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

                arguments = raw_args.split()

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
            case Tool.WRITE:
                if not command.arguments:
                    raise InvalidPathError(
                        "At least one file path is required."
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