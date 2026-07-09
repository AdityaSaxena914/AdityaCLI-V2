# Architecture

## Purpose

AdityaCLI is a terminal-based AI software engineering assistant that orchestrates Large Language Models (LLMs), tools, and MCP servers to perform software development tasks inside a user's workspace.

The application is **local-first**. It is designed to work with local models by default while remaining provider-agnostic through a common provider interface. Cloud providers are supported through the same architecture without changing the core system.

The terminal is the primary user interface because it provides direct access to the developer's workspace, operating system, Git repositories, and development tools.

---

# High-Level Architecture

```
                    User
                      │
                      ▼
              Typer + Rich CLI
                      │
                      ▼
            Application Services
                      │
                      ▼
          LangGraph Agent Runtime
                      │
      ┌───────────────┼────────────────┐
      ▼               ▼                ▼
 Provider        Tool Registry      Workspace
      │               │                │
      ▼               ▼                ▼
 LM Studio      Local Tools       Project Files
 Ollama         MCP Tools         Git Repository
 OpenAI
 Anthropic
 Gemini
```

---

# Execution Flow

A request travels through the system in the following order.

```
User
    │
    ▼
CLI
    │
    ▼
Application Service
    │
    ▼
Agent
    │
    ▼
Determine Mode
(Ask / Plan / Agent / ...)
    │
    ▼
Plan Task
    │
    ▼
Select Required Tools
    │
    ▼
Execute Tools
    │
    ▼
Generate Final Response
    │
    ▼
CLI
```

The CLI never performs business logic.

The Agent decides how a request should be executed.

---

# Layer Responsibilities

## CLI Layer

### Purpose

Provides the terminal user interface.

### Responsibilities

- Read user input
- Display streaming output
- Display progress
- Display errors
- Invoke application services

### Does NOT

- Execute business logic
- Access databases
- Call tools directly
- Call providers directly

---

## Service Layer

### Purpose

Owns the application's business logic.

### Responsibilities

- Coordinate application workflow
- Manage agent lifecycle
- Coordinate providers
- Coordinate tools
- Coordinate workspace operations

### Does NOT

- Render UI
- Execute SQL
- Know terminal implementation

---

## Agent Layer

### Purpose

Reason about the user's request and decide how it should be completed.

### Responsibilities

- Understand user intent
- Select execution mode
- Build execution plans
- Decide which tools are required
- Produce final responses

### Does NOT

- Know provider implementation
- Know CLI implementation
- Know file system implementation

---

## Provider Layer

### Purpose

Provide a common interface for all LLM providers.

### Responsibilities

- Connect to model providers
- Send prompts
- Stream responses
- Handle provider-specific APIs

### Initial Provider

- LM Studio

### Future Providers

- Ollama
- OpenAI
- Anthropic
- Gemini

The remainder of the application must never know which provider is active.

---

## Tool Registry

### Purpose

Manage every executable capability available to the agent.

### Responsibilities

- Register tools
- Discover tools
- Validate tool execution
- Execute tools
- Return tool results

### Initial Tool Categories

- Read File
- Write File
- Edit File
- Terminal
- Git
- Search

Future MCP tools and plugins will also be registered here.

The Agent never communicates directly with individual tools.

---

## Workspace

### Purpose

Represent the active software project.

### Responsibilities

- Read project files
- Write project files
- Search project
- Respect workspace boundaries

Each running CLI instance owns exactly one active workspace.

---

# Workspace Model

Every CLI process owns:

- One Session
- One Workspace
- One Active Agent

Opening multiple terminal windows creates multiple independent sessions.

Example:

```
VSCode Window A
        │
        ▼
Session A
        │
        ▼
Workspace A


VSCode Window B
        │
        ▼
Session B
        │
        ▼
Workspace B
```

Runtime state is never shared between sessions.

---

# Persistence (V2.0.0)

AdityaCLI V2.0.0 is intentionally stateless.

No database is used.

No chat history is stored.

No permanent memory exists.

Project context is maintained only through repository documentation such as:

- README.md
- CONTEXT.md
- PROJECT.md

Future versions introduce structured persistence.

---

# Dependency Rules

Dependencies flow in one direction only.

```
CLI
    │
    ▼
Services
    │
    ▼
Agent
    │
    ▼
Provider
Tool Registry
Workspace
```

Forbidden dependencies:

- CLI → Provider
- CLI → Tool
- CLI → Workspace
- Provider → CLI
- Tool → CLI

Every layer communicates only with the layer directly below it.

---

# Design Principles

- Local-first architecture.
- Provider-independent.
- Frameworks are preferred over custom infrastructure where appropriate.
- Business logic is separated from presentation.
- Components should be independently replaceable.
- One responsibility per module.
- Runtime state belongs to the current session only.
- Future capabilities must not complicate the current version.

---

# V2.0.0 Scope

Included

- Typer CLI
- Rich terminal UI
- LangChain
- LangGraph
- LM Studio provider
- Tool execution
- MCP client support
- Workspace operations
- Repository documentation for context

Excluded

- Database
- Chat persistence
- Permanent memory
- RAG
- Vector database
- Multi-agent system
- Plugin system