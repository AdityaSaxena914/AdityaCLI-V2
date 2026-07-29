from pathlib import Path

from adityacli.cli import CLI
from adityacli.config import (
    AppConfig,
    LMStudioConfig,
    SecurityConfig,
    WorkspaceConfig,
)
from adityacli.core.runtime import Runtime
from adityacli.llm.client import LLMClient
from adityacli.tools.registry import ToolRegistry


def main() -> None:
    config = AppConfig(
        workspace=WorkspaceConfig(
            root=Path.cwd(),
        ),
        lmstudio=LMStudioConfig(),
        security=SecurityConfig(),
    )

    client = LLMClient(config.lmstudio)

    registry = ToolRegistry(
        config=config,
    )

    runtime = Runtime(
        config=config,
        client=client,
        registry=registry,
    )

    cli = CLI(runtime)

    cli.run()


if __name__ == "__main__":
    main()