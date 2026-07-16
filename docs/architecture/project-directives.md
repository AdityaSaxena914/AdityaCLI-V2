# Project Directives

**AdityaCLI V2 – Single Source of Truth**

---

# Purpose

This document defines the engineering rules, development methodology, roadmap, and current implementation state of AdityaCLI.

It is intended to be read together with:

* architecture.md
* system-model.md
* provider.md
* tools.md
* Current project source code (ZIP)

These documents together are the complete context required for continuing development.

---

# Project Vision

AdityaCLI is a local-first, provider-agnostic, terminal-based AI software engineering assistant.

The architecture is designed to remain stable across every version.

Future versions should extend the implementation rather than redesign the architecture.

The long-term goal is a production-grade developer assistant capable of working with multiple LLM providers, tools, MCP servers, project context, persistent memory, and plugins without requiring architectural refactoring.

---

# Non-Negotiable Engineering Rules

## Rule 1 — Final Architecture First

The final architecture is created during V2.0.0.

Future versions must only implement functionality inside the existing architecture.

Never redesign package structures later.

---

## Rule 2 — Empty Files Are Acceptable

If the final architecture requires a file, create it immediately.

Example:

provider/

* manager.py
* registry.py
* interface.py
* models.py
* exceptions.py
* constants.py
* types.py
* utils.py
* providers/

  * lmstudio.py
  * openai.py
  * anthropic.py
  * ollama.py
  * gemini.py

Even if most files initially contain only:

```python
"""Reserved for future implementation."""
```

This is intentional.

---

## Rule 3 — Never Collapse Architecture

Never merge files because they are currently small.

Bad:

provider.py (700+ lines)

Good:

provider/

* manager.py
* registry.py
* interface.py
* models.py
* exceptions.py

Small files are preferred over future refactoring.

---

## Rule 4 — Implement Only Current Version

Architecture is future-proof.

Implementation is version-specific.

Example:

V2.0.0 creates:

provider/openai.py

The file exists.

The implementation is deferred until V2.7.0.

---

## Rule 5 — One Responsibility Per Module

Every file answers one question.

Examples:

manager.py

* lifecycle

registry.py

* registration

models.py

* data models

exceptions.py

* exceptions

Never mix responsibilities.

---

## Rule 6 — One Responsibility Per Subsystem

Every subsystem owns:

* manager
* registry
* interface
* models
* exceptions
* constants
* types
* utils

if applicable.

Subsystems never own unrelated logic.

---

## Rule 7 — Components Must Be Replaceable

Deleting and rewriting one subsystem should never require changes to unrelated subsystems.

Provider changes should not affect:

* Agent
* Tool
* Workspace
* Session

---

# Architecture Principles

* Local-first
* Provider independent
* Tool independent
* Runtime extensible
* Security before execution
* Separation of concerns
* Dependency inversion
* Open/Closed Principle
* Single Responsibility Principle

---

# Dependency Direction

Always:

CLI

↓

Services

↓

Agent

↓

Manager

↓

Registry

↓

Interface

↓

Implementation

Never reverse dependencies.

---

# Development Methodology

Every subsystem is built in the following order.

1. Folder structure
2. Models
3. Interface
4. Exceptions
5. Registry
6. Manager
7. Implementation
8. Integration testing

Never skip directly to implementation.

---

# Current Version

Current version:

V2.0.0

---

# Current Development State

## Completed

### Core Infrastructure

* Configuration subsystem
* Logging subsystem
* Global exception subsystem

### Runtime Foundation

* Application runtime foundation

### Provider Subsystem

* Models
* Interface
* Exceptions
* Registry
* Manager
* LM Studio provider skeleton
* Public API

### Tool Subsystem

* Models
* Interface
* Exceptions
* Registry
* Manager
* Built-in tool skeletons
* Public API

### Workspace Subsystem

* Models
* Exceptions
* Validator
* Manager
* Public API

### Session Subsystem

* Models
* Exceptions
* Manager
* Public API

### Mode Subsystem

* Models
* Exceptions
* Manager
* Public API

### Security Subsystem

* Models
* Exceptions
* Policy interface
* Validator
* Manager
* Public API

### Agent Subsystem

* Models
* Interface
* Exceptions
* Manager
* Default agent skeleton
* Public API

### MCP Subsystem

* Models
* Interface
* Exceptions
* Registry
* Manager
* Stdio client skeleton
* Public API

---

## Current Status

The complete runtime architecture for AdityaCLI V2.0.0 has been established.

All core subsystems now exist in their final architectural locations.

Current implementations are intentionally minimal and provide the structural foundation for future versions without requiring architectural refactoring.

---

## Next Implementation Phase

The project now transitions from **architecture construction** to **feature implementation**.

Implementation order:

1. CLI subsystem (Typer + Rich)
2. Application wiring
3. LM Studio provider implementation
4. Streaming chat
5. Tool implementations
6. Agent execution loop
7. MCP integration
8. End-to-end integration testing
9. V2.0.0 release


---

# Version Roadmap

## V2.0.0

Core Agent Loop

* Stateless runtime
* Single LangGraph agent
* Typer CLI
* Rich UI
* LM Studio
* Tool Registry
* MCP
* Repository documentation

No DB

No RAG

No Memory

---

## V2.1.0

Database Foundation

SQLite

SQLModel

Projects

Sessions

---

## V2.2.0

Chat & Project Identity

Projects

Chats

Messages

Project Memory

---

## V2.3.0

Synchronization

Chunking

Sync pipeline

Atomic transactions

---

## V2.4.0

MiniRAG

FTS5

BM25

/use

/import

---

## V2.5.0

Global Memory

/save

Memory search

Promotion

---

## V2.6.0

Security Hardening

Docker

Path Jail

Audit Logging

Prompt Injection Protection

---

## V2.7.0

Multi Provider

OpenAI

Anthropic

Ollama

Gemini

Automatic provider setup

---

## V2.8.0

Extended Agent

Email

Messaging

Social

Additional MCP integrations

---

## V2.9.0

Plugin System

Third-party providers

Third-party tools

LSP

Extensions

---

## V2.10.0

Production Release

Testing

Performance

Documentation

Packaging

---

# Backend Development Tasks

Follow the backend task roadmap exactly.

Task order:

1. Documentation
2. Scaffolding
3. Database
4. Repository
5. Services
6. Security
7. Reliability
8. CLI
9. Logging
10. Testing

Never reorder unless architecture requires it.

---

# Coding Standards

* Python 3.12+
* Type hints everywhere
* Pydantic V2
* SQLModel
* Typer
* Rich
* No duplicated logic
* Small modules
* Clear naming
* Explicit dependencies

---

# Testing Policy

Do not stop after every small method.

Complete the subsystem first.

Then perform integration testing.

Testing order:

1. Unit

2. Integration

3. Security

4. Performance

---

# Refactoring Policy

Architecture refactoring is prohibited after V2.0.0.

Future versions may only:

* implement
* extend
* optimize

They must not redesign folder structures.

---

# AI Assistant Instructions

Whenever continuing this project:

1. Read

* architecture.md
* system-model.md
* provider.md
* tools.md
* project-directives.md

2. Inspect the latest project source.

3. Determine completed work.

4. Continue from the exact next unfinished task.

Never recreate already implemented code.

Never redesign architecture.

Never remove placeholder files.

Always preserve the established architecture.

---

# Session Recovery Checklist

Before writing code:

1. Read all architecture documents.

2. Read project-directives.md.

3. Inspect current source code.

4. Determine completed tasks.

5. Continue from the next unfinished implementation.

6. Preserve architecture.

7. Implement only functionality belonging to the current version.

8. Leave future-version files in place.

This document is the authoritative development guide for AdityaCLI V2 and all future versions.
