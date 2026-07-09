# Tool Architecture

## Purpose

The Tool subsystem enables AdityaCLI to perform deterministic actions beyond natural language generation.

A Tool is an executable software module exposed by the Application Runtime to the Agent, allowing it to interact with the operating system, project workspace, external services, and MCP servers.

The Agent never performs actions itself.

It only requests Tool execution.

---

# Design Goals

The Tool subsystem is designed around the following principles:

- Stateless execution
- Provider independence
- Security-first execution
- Runtime extensibility
- Uniform interfaces
- Standardized results
- Human-controlled permissions
- Future plugin compatibility

---

# Runtime Architecture

```
                    Agent
                      │
                      ▼
               Tool Registry
                      │
                      ▼
              Security Manager
                      │
                      ▼
               Tool Instance
                      │
                      ▼
             Session Runtime
                      │
                      ▼
                    Agent
```

The Agent never communicates directly with Tool implementations.

---

# What is a Tool?

A Tool is an executable function or software module exposed by the Application Runtime to the Agent, allowing the model to interact with external environments, manipulate data, or perform deterministic actions beyond text generation.

A Tool contains logic.

It does not contain reasoning.

---

# Tool Definition vs Tool Instance

## Tool Definition

A Tool Definition is the permanent description of a tool.

It contains:

- Name
- Description
- Parameters
- Permission metadata
- Interface implementation

Tool Definitions are immutable after registration.

---

## Tool Instance

A Tool Instance is created only when the Agent invokes a Tool.

It exists only during execution.

After execution completes, the Tool Instance is destroyed.

Tool instances never persist between invocations.

---

# Tool Lifecycle

Tool execution consists of two completely independent phases.

---

## Registration Phase

Executed once during Application Runtime startup.

```
Discover
      │
      ▼
Register
      │
      ▼
Validate Definition
      │
      ▼
Generate Provider Schema
      │
      ▼
Registry Ready
```

### Discover

The Application Runtime discovers Tools from:

- Native tool modules
- Custom tool directories
- MCP servers
- Future plugins

---

### Register

Tool Definitions are registered inside the Tool Registry.

---

### Validate Definition

The Runtime verifies:

- Interface implementation
- Parameter schema
- Permission metadata
- Unique naming

---

### Generate Provider Schema

The Registry converts internal Tool Definitions into the format required by the active Provider.

Examples:

- OpenAI Function Calling
- Anthropic Tool Schema
- Gemini Tool Schema

The Agent never performs this translation.

---

## Execution Phase

Executed once for every Tool invocation.

```
Agent Requests Tool
        │
        ▼
Registry Lookup
        │
        ▼
Security Validation
        │
        ▼
Instantiate Tool
        │
        ▼
Validate Inputs
        │
        ▼
Execute
        │
        ▼
Validate Output
        │
        ▼
Return Standard Result
        │
        ▼
Destroy Tool Instance
```

Tool Instances never remain resident in memory after execution.

---

# Tool Interface

Every Tool implementation must expose a common interface.

## Identity

- Name
- Version
- Namespace
- Description

---

## Schema

- Parameters
- Input validation
- Output validation

---

## Execution

- Execute

---

## Permissions

- Permission Category
- Risk Tier
- Requires Confirmation

---

## Runtime

- Timeout
- Response Formatter

---

# Tool Categories

## Filesystem

Examples

- Read File
- Write File
- Edit File
- Delete File

---

## Terminal

Examples

- Execute Command
- Process Management

---

## Git

Examples

- Commit
- Branch
- Diff
- Status

---

## Search

Examples

- Search Files
- Search Symbols
- Search Workspace

---

## Web

Examples

- Fetch URL
- Web Search

---

## MCP

External tools exposed through connected MCP servers.

---

## Code Intelligence

Examples

- AST Parsing
- Symbol Lookup
- Reference Search
- Definition Lookup

---

## Context Management

Examples

- Compress Context
- Scratchpad
- Workspace Indexing

---

## Environment

Examples

- Environment Variables
- Dependency Inspection
- Runtime Validation

---

## Human Interaction

Examples

- Ask User
- Request Secret
- Request Confirmation

---

## Custom

User-defined tools.

---

# Tool Registry

## Purpose

The Tool Registry owns every Tool Definition available during the current Session.

It never executes Tools.

---

## Responsibilities

### Discovery

- Discover tools
- Register tools
- Remove tools

---

### Lookup

- Resolve tool names
- Resolve namespaces
- Enable/Disable tools

---

### Schema Management

- Provider schema generation
- Metadata enrichment
- Capability exposure

---

### Namespace Management

Resolve naming collisions.

Example

```
github.search

postgres.search

mongodb.search
```

---

### Dependency Validation

Validate runtime requirements before Tool execution.

Examples

- Required binaries
- Required environment
- MCP availability

---

### Observability

Maintain execution metadata.

Examples

- Registration logs
- Tool statistics
- Performance metrics
- Future telemetry

The Registry does not receive execution results.

---

# Security

Every Tool execution passes through the Security Manager.

```
Agent
      │
      ▼
Registry
      │
      ▼
Security
      │
      ▼
Tool
```

The Security Manager validates:

- Active Mode
- Permission Category
- Risk Tier
- Workspace boundaries
- User confirmation
- Execution policies

The LLM never performs security validation.

---

# Permission Model

Every Tool declares two permission fields.

## Permission Category

Examples

```
filesystem:read

filesystem:write

terminal:execute

network:outbound

context:modify
```

Permission Categories describe the intent of the Tool.

---

## Risk Tier

Every Tool belongs to one of four risk levels.

### Tier 1

Read-only.

Always allowed.

---

### Tier 2

Low risk.

Allowed automatically.

Logged for observability.

---

### Tier 3

Medium risk.

Allowed according to active Mode.

May require user confirmation.

---

### Tier 4

Critical.

Always requires explicit user approval.

Examples

- Execute shell commands
- Delete directories
- Kill processes

---

# Tool Result

Every Tool returns a standardized result.

```
{
    "tool": "write_file",
    "success": true,
    "output": "...",
    "error": null,
    "execution_time_ms": 84,
    "metadata": {}
}
```

## Fields

### Tool

Tool identifier.

---

### Success

Boolean execution state.

---

### Output

Successful execution result.

---

### Error

Structured failure information.

Examples

- Error code
- Message

---

### Execution Time

Execution duration in milliseconds.

---

### Metadata

Additional runtime information.

Examples

- Bytes written
- Files changed
- Exit code
- HTTP status

Metadata is intended primarily for the Application Runtime.

---

# Failure Handling

Tool failures never crash the Session.

```
Tool
      │
      ▼
Session Runtime
      │
      ▼
Agent
```

The Tool reports failures.

The Session Runtime evaluates severity.

Recoverable failures are returned to the Agent for self-correction.

Fatal failures are surfaced directly to the user.

---

# MCP Integration

MCP tools are treated exactly like native tools.

The Agent does not distinguish between:

- Native Tool
- MCP Tool

Routing is handled entirely by the Tool Registry.

---

# Plugins

Future plugin packages may register:

- Tools
- Providers
- Commands
- Modes
- Prompt Packs

No modification to the core runtime should be required.

---

# Design Principles

- Stateless execution
- Immutable Tool Definitions
- Ephemeral Tool Instances
- Security before execution
- Standardized interfaces
- Standardized results
- Runtime extensibility
- Provider independence
- LLM never enforces security
- One Tool, one responsibility

---

# V2.0.0 Scope

Included

- Native tools
- Tool Registry
- Security validation
- MCP tools
- Standard Tool interface
- Standard Tool results
- Tool namespacing
- Provider schema generation

Deferred

- Tool dependency graphs
- Tool version negotiation
- Distributed Tool execution
- Tool sandbox virtualization
- Tool scheduling
- Plugin SDK