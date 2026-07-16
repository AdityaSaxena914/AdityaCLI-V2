from adityacli.exceptions import RecoverableError

class MCPError(RecoverableError):
    """Base class for all MCP-related errors."""

class MCPConnectionError(MCPError):
    ERROR_CODE = "MCP_CONNECTION"
    DEFAULT_RECOVERY_HINT = (
        "Ensure the MCP server is running and reachable."
    )

class MCPExecutionError(MCPError):
    ERROR_CODE = "MCP_EXECUTION"
    DEFAULT_RECOVERY_HINT = (
        "Retry the request."
    )

class MCPServerNotFoundError(MCPError):
    ERROR_CODE = "MCP_SERVER_NOT_FOUND"
    DEFAULT_RECOVERY_HINT = (
        "Verify the configured MCP server."
    )

class MCPProtocolError(MCPError):
    ERROR_CODE = "MCP_PROTOCOL"
    DEFAULT_RECOVERY_HINT = (
        "Verify the MCP protocol implementation."
    )

class MCPTimeoutError(MCPError):
    ERROR_CODE = "MCP_TIMEOUT"
    DEFAULT_RECOVERY_HINT = (
        "Retry the request or increase the timeout."
    )