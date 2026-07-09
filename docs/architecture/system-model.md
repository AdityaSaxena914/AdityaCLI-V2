# System Model

## Purpose

This document defines the core runtime concepts of AdityaCLI V2.0.0.

It describes **what exists inside the system**, how each concept behaves, who owns it, and how long it lives.

This is **not** a database document.

---

# Runtime Overview

```
Application Runtime
│
├── CLI
├── Agent Runtime
├── Provider Manager
├── Tool Registry
├── Workspace Manager
└── Security Manager
```

The Application Runtime owns every runtime component.

---

# Project

## Purpose

A Project represents a software workspace managed by AdityaCLI.

The agent performs all development tasks inside the currently active Project.

## Lifecycle

Created

- User starts AdityaCLI inside a project directory.
- OR
- User specifies a project using:

```
adityacli --workspace <path>
```

Destroyed

- When the current session ends.

## Ownership

Owned by

- Workspace Manager

## Persistence

V2.0.0 stores no structured project metadata.

Project context is maintained through repository documentation.

Examples

- README.md
- PROJECT.md
- CONTEXT.md

---

# Workspace

## Purpose

Represents the active filesystem boundary.

All file operations are restricted to the Workspace.

## Lifecycle

Created

- Session startup.

Destroyed

- Session exit.

## Ownership

Owned by

- Workspace Manager

## Rules

- One Workspace per Session.
- Workspace may be specified during startup.
- Workspace cannot be changed during an active Session.
- Tools cannot access files outside the Workspace.

---

# Session

## Purpose

Represents one active execution of AdityaCLI.

A Session contains:

- Active Agent
- Active Workspace
- Active Provider
- Runtime State

## Lifecycle

Created

- CLI startup.

Destroyed

- CLI exit.

## Ownership

Owned by

- Application Runtime

## Rules

- One Session owns one Workspace.
- One Session owns one Agent.
- Multiple Sessions may run simultaneously.
- Sessions never communicate directly.

---

# Session Snapshot

## Purpose

Stores enough information to resume a previous Session.

It is **not** a live Session.

## Format

JSONL

## Lifecycle

Created

- Session exit.

Loaded

- Using resume functionality.

Deleted

- Automatically after the configured retention period.

## Ownership

Owned by

- Application Runtime

---

# Agent

## Purpose

Reason about user requests and determine how work should be completed.

## Responsibilities

- Understand user intent.
- Select execution mode.
- Create execution plans.
- Select tools.
- Generate responses.

## Does NOT

- Execute tools.
- Access providers directly.
- Enforce security.
- Access the filesystem directly.

## Ownership

Owned by

- Agent Runtime

## Rules

- One Agent per Session.
- Agent does not retain memory after Session termination.
- Previous context is restored from Session Snapshot and project documentation.

---

# Provider

## Purpose

Represents a Large Language Model backend.

Examples

- LM Studio
- Ollama
- OpenAI
- Anthropic
- Gemini

## Ownership

Managed by

- Provider Manager

## Rules

- One active Provider per Session.
- Provider may be changed during a Session.
- The Agent is aware of the currently active Provider.
- Future versions may introduce provider routing.

---

# Provider Manager

## Purpose

Acts as the abstraction layer between the Agent and model providers.

## Responsibilities

- Manage providers.
- Switch providers.
- Select models.
- Validate provider configuration.
- Handle streaming.
- Normalize provider APIs.

The Agent never communicates directly with provider implementations.

---

# Tool

## Purpose

Represents one executable capability.

Examples

- Read File
- Write File
- Edit File
- Terminal
- Git
- Search

## Rules

- Tools are independent modules.
- Tools never call other tools.
- Tools never communicate with the LLM.
- Tools perform one responsibility only.

---

# Tool Registry

## Purpose

Maintain every tool available during the Session.

## Responsibilities

- Discover tools.
- Register tools.
- Enable or disable tools.
- Validate execution requests.
- Route requests to local or MCP tools.

The Agent never communicates directly with individual tools.

---

# Tool Discovery

During startup the Application Runtime discovers tools from multiple sources.

```
Native Tools
        │
        ▼

Custom Tool Directory
        │
        ▼

MCP Servers
        │
        ▼

Tool Registry
        │
        ▼

Agent Runtime
```

The Agent receives only the final available tool definitions.

It never performs discovery itself.

---

# MCP Server

## Purpose

Expose external capabilities using the Model Context Protocol.

## Rules

- Multiple MCP Servers may be connected.
- MCP tools appear identical to local tools.
- The Agent does not distinguish between local and MCP tools.
- Routing is handled by the Tool Registry.

---

# Mode

## Purpose

Defines how the Agent behaves during the current Session.

Examples

- Ask
- Plan
- Agent

## Ownership

Controlled by

- User

Enforced by

- Application Runtime

## Rules

- Mode may change during a Session.
- Mode changes both:
    - Agent behaviour.
    - Tool permissions.

Mode acts as an execution policy rather than a prompt modification.

---

# Security

## Principle

The LLM is never trusted to enforce security.

All permission checks are performed by the Application Runtime before tool execution.

The Agent can request a tool.

Only the runtime decides whether execution is permitted.

---

# Relationships

```
Application Runtime
│
├── Session
│
├── Workspace
│
├── Agent Runtime
│
│   ├── Agent
│   ├── Provider Manager
│   └── Tool Registry
│
├── Security Manager
│
└── Session Snapshot
```

Every runtime component is owned by the Application Runtime.

No runtime component communicates outside its defined responsibilities.