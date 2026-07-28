from pathlib import Path

from cli import CLI
from config import AppConfig, LMStudioConfig, SecurityConfig, WorkspaceConfig
from core.runtime import Runtime
from llm.client import LLMClient


def main() -> None:
    config = AppConfig(
        workspace=WorkspaceConfig(
            root=Path.cwd(),
        ),
        lmstudio=LMStudioConfig(),
        security=SecurityConfig(),
    )

    client = LLMClient(config.lmstudio)
    runtime = Runtime(config, client)
    cli = CLI(runtime)

    cli.run()


if __name__ == "__main__":
    main()