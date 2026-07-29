from pathlib import Path
import argparse

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
from adityacli.providers.duckduckgo import DuckDuckGoProvider
from adityacli.prompts import load_prompt


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="aditya",
        description="AdityaCLI",
    )

    parser.add_argument(
        "--continue",
        dest="continue_session",
        action="store_true",
        help="Continue the previous session.",
    )

    args = parser.parse_args()

    config = AppConfig(
        workspace=WorkspaceConfig(
            root=Path.cwd(),
        ),
        lmstudio=LMStudioConfig(),
        security=SecurityConfig(),
    )

    client = LLMClient(config.lmstudio)
    search_provider = DuckDuckGoProvider()

    registry = ToolRegistry(
        config=config,
        search_provider=search_provider,
    )

    runtime = Runtime(
        config=config,
        client=client,
        registry=registry,
        continue_session=args.continue_session,
    )
    runtime.add_system_prompt(
        load_prompt("system")
    )

    cli = CLI(runtime)
    cli.run()


if __name__ == "__main__":
    main()