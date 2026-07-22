from __future__ import annotations

from adityacli.agent import AgentManager, DefaultAgent
from adityacli.config import settings
from adityacli.logging import get_logger
from adityacli.mcp import MCPManager, MCPRegistry
from adityacli.mode import ModeManager
from adityacli.provider import ProviderManager, ProviderRegistry, LMStudioProvider
from adityacli.security import SecurityManager
from adityacli.session import SessionManager
from adityacli.tool import (
    EditFileTool,
    GitTool,
    ReadFileTool,
    SearchTool,
    TerminalTool,
    ToolManager,
    ToolRegistry,
    WriteFileTool,
)
from adityacli.workspace import WorkspaceManager


class Application:
    """Central application composition root."""

    def __init__(self) -> None:
        self.settings = settings
        self.logger = get_logger(__name__)

        #
        # Registries
        #
        self.provider_registry = ProviderRegistry()
        self.provider_registry.register(
            "lmstudio",
            LMStudioProvider,
        )
        self.tool_registry = ToolRegistry()

        #
        # Built-in Tools
        #
        self.tool_registry.register(
            "read_file",
            ReadFileTool,
        )

        self.tool_registry.register(
            "write_file",
            WriteFileTool,
        )

        self.tool_registry.register(
            "edit_file",
            EditFileTool,
        )

        self.tool_registry.register(
            "terminal",
            TerminalTool,
        )

        self.tool_registry.register(
            "git",
            GitTool,
        )

        self.tool_registry.register(
            "search",
            SearchTool,
        )

        self.mcp_registry = MCPRegistry()

        #
        # Managers
        #
        self.workspace_manager = WorkspaceManager()
        self.session_manager = SessionManager()
        self.mode_manager = ModeManager()
        self.security_manager = SecurityManager()

        self.provider_manager = ProviderManager(
            self.provider_registry,
        )

        self.provider_manager.switch_provider(
            self.settings.provider.default_provider,
        )

        self.provider_manager.load_model(
            self.settings.provider.default_model,
        )
        
        self.tool_manager = ToolManager(
            self.tool_registry,
        )

        self.mcp_manager = MCPManager(
            self.mcp_registry,
        )

        self.agent_manager = AgentManager(
            provider_manager=self.provider_manager,
            tool_manager=self.tool_manager,
            workspace_manager=self.workspace_manager,
            session_manager=self.session_manager,
            mode_manager=self.mode_manager,
            security_manager=self.security_manager,
        )

        self.agent_manager.set_agent(
            DefaultAgent(
                provider_manager=self.provider_manager,
                tool_manager=self.tool_manager,
            )
        )

        self.logger.debug("Application initialized.")

    @property
    def ready(self) -> bool:
        """Return whether the application has been initialized."""

        return True