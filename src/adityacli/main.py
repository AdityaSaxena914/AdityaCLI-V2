from __future__ import annotations

import argparse
from pathlib import Path

from adityacli.cli import CLI
from adityacli.config import (
    AppConfig,
    LMStudioConfig,
    SecurityConfig,
    WorkspaceConfig,
)
from adityacli.core.file_manager import FileManager
from adityacli.core.parser import Parser
from adityacli.core.prompt_builder import PromptBuilder
from adityacli.core.response_parser import ResponseParser
from adityacli.core.runtime import Runtime
from adityacli.core.session_store import SessionStore
from adityacli.llm.client import LLMClient
from adityacli.prompts import load_prompt
from adityacli.providers.duckduckgo import DuckDuckGoProvider
from adityacli.services.chat_service import ChatService
from adityacli.services.command_service import CommandService
from adityacli.services.llm_service import LLMService
from adityacli.services.overwrite_service import OverwriteService
from adityacli.tools.registry import ToolRegistry
from adityacli.core.token_budget import TokenBudget
from adityacli.core.context_manager import ContextManager


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="aditya",
        description="AdityaCLI",
    )

    _ = parser.add_argument(
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

    registry = ToolRegistry(
        config=config,
        search_provider=DuckDuckGoProvider(),
    )

    parser_service = Parser()
    response_parser = ResponseParser()
    prompt_builder = PromptBuilder()

    token_budget = TokenBudget(
        config.lmstudio.context_window,
    )
    context_manager = ContextManager(
        config.lmstudio.context_window,
    )

    store = SessionStore(config.workspace.root)
    file_manager = FileManager(config)

    command_service = CommandService(
        parser=parser_service,
        registry=registry,
    )

    llm_service = LLMService(
        client=client,
        prompt_builder=prompt_builder,
        token_budget=token_budget,
        context_manager=context_manager,
    )

    overwrite_service = OverwriteService(
        parser=response_parser,
        file_manager=file_manager,
        store=store,
    )

    chat_service = ChatService(
        command_service=command_service,
        llm_service=llm_service,
        overwrite_service=overwrite_service,
        store=store,
    )

    runtime = Runtime(
        config=config,
        parser=parser_service,
        store=store,
        chat_service=chat_service,
        continue_session=args.continue_session,  # pyright: ignore[reportAny]
    )

    runtime.add_system_prompt(
        load_prompt("system")
    )

    CLI(runtime).run()


if __name__ == "__main__":
    main()