from __future__ import annotations
from pathlib import Path
from adityacli.agent import AgentManager, DefaultAgent
from adityacli.config import settings
from adityacli.logging import get_logger
from adityacli.mcp import MCPManager, MCPRegistry
from adityacli.provider import ProviderManager, ProviderRegistry, LMStudioProvider
from adityacli.security import SecurityManager
from adityacli.session import SessionManager
from adityacli.tool import (
    EditFileTool,
    GitStatusTool,
    ReadFileTool,
    WorkspaceSearchTool,
    TerminalTool,
    ToolManager,
    ToolRegistry,
    WriteFileTool,
    CopyFileTool,
    MoveFileTool,
    DeleteFileTool,
)
from adityacli.workspace import WorkspaceManager
from adityacli.runtime import RuntimeManager


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
            "git_status",
            GitStatusTool,
        )

        self.tool_registry.register(
            "workspace_search",
            WorkspaceSearchTool,
        )

        self.tool_registry.register(
            "copy_file",
            CopyFileTool,
        )

        self.tool_registry.register(
            "move_file",
            MoveFileTool,
        )

        self.tool_registry.register(
            "delete_file",
            DeleteFileTool,
        )

        
        self.mcp_registry = MCPRegistry()

        #
        # Managers
        #
        self.workspace_manager = WorkspaceManager()
        self.workspace_manager.load(Path.cwd())
        self.session_manager = SessionManager()
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
            registry=self.tool_registry,
        )

        self.mcp_manager = MCPManager(
            self.mcp_registry,
        )

        self.agent_manager = AgentManager(
            provider_manager=self.provider_manager,
            tool_manager=self.tool_manager,
            workspace_manager=self.workspace_manager,
            session_manager=self.session_manager,
            security_manager=self.security_manager,
        )

        self.runtime_manager = RuntimeManager(
            provider_manager=self.provider_manager,
            tool_manager=self.tool_manager,
            workspace_manager=self.workspace_manager,
            security_manager=self.security_manager,
            agent_manager=self.agent_manager,
        )

        self.agent_manager.set_agent(
            DefaultAgent(
                provider_manager=self.provider_manager,
                tool_manager=self.tool_manager,
                workspace_manager=self.workspace_manager,
                security_manager=self.security_manager,
            )
        )

        self.logger.debug("Application initialized.")

    @property
    def ready(self) -> bool:
        """Return whether the application has been initialized."""

        return True