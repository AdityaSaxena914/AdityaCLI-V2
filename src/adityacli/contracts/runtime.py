from enum import Enum

from pydantic import BaseModel


class Intent(str, Enum):
    """User intent identified by the Intent Router."""

    FILESYSTEM = "filesystem"
    TERMINAL = "terminal"
    GIT = "git"
    SEARCH = "search"
    WEB = "web"
    MCP = "mcp"
    CODE_INTELLIGENCE = "code_intelligence"
    HUMAN_INTERACTION = "human_interaction"

    CHAT = "chat"
    UNKNOWN = "unknown"


class PipelineType(str, Enum):
    """Execution pipeline selected by Runtime Intelligence."""

    DETERMINISTIC = "deterministic"
    SEMANTIC = "semantic"
    REASONING = "reasoning"


class ModelState(BaseModel):
    """Current model information maintained by the Resource Manager."""

    provider: str
    model: str

    quantization: str | None = None

    context_window: int

    estimated_ram_mb: int | None = None
    available_ram_mb: int | None = None

    supports_streaming: bool = True
    supports_tools: bool = True
    supports_grammar: bool = False


class PipelineDecision(BaseModel):
    """Decision produced by Runtime Intelligence."""

    intent: Intent

    pipeline: PipelineType

    requires_llm: bool
    requires_context: bool
    requires_tools: bool


class RuntimeRequest(BaseModel):
    """Request entering the Runtime."""

    user_input: str

    workspace: str

    provider: str


class RuntimeResponse(BaseModel):
    """Final Runtime response."""

    success: bool = True

    message: str

    pipeline: PipelineType