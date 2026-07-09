# Provider Architecture

## Purpose

The Provider subsystem is responsible for connecting AdityaCLI to Large Language Models (LLMs).

A Provider abstracts the implementation details of a model host, allowing the remainder of the application to communicate with every model through a single, consistent interface.

Providers may be local or cloud-hosted.

Examples include:

- LM Studio
- Ollama
- OpenAI
- Anthropic
- Gemini

The rest of AdityaCLI must remain unaware of provider-specific APIs.

---

# Design Goals

The Provider subsystem exists to achieve the following goals:

- Provider independence
- Standardized interfaces
- Runtime provider switching
- Future extensibility
- Streaming support
- Capability discovery
- Isolation of provider-specific logic

---

# Runtime Architecture

```
Application Runtime
        │
        ▼
 Provider Manager
        │
        ▼
 Provider Interface
        │
 ┌──────┼──────────────┐
 ▼      ▼              ▼
LM Studio OpenAI    Ollama
                    Anthropic
                    Gemini
```

Neither the CLI nor the Agent communicates directly with provider implementations.

---

# What is a Provider?

A Provider is a software system that hosts AI models and exposes a standardized API through which AdityaCLI performs inference.

A Provider is responsible for infrastructure-level operations such as authentication, model execution, streaming, and capability discovery.

Providers do **not** own application behaviour.

---

# Responsibilities

A Provider is responsible for:

## Infrastructure

- Model inference
- Chat completion
- Streaming responses
- Embedding generation
- Tokenization
- Context window limits
- Output token limits

---

## Connectivity

- Authentication
- Endpoint communication
- Health checks
- Connection management
- Retry-safe request handling

---

## Discovery

- Model listing
- Model metadata
- Capability reporting
- Version information

---

## Does NOT Own

Providers never own:

- Planning
- Tool execution
- Session management
- Workspace
- Memory
- Retrieval
- Security
- Business logic
- Runtime modes

These responsibilities belong to the Application Runtime.

---

# Provider Lifecycle

Every Provider follows the same lifecycle.

```
Configure
        │
        ▼
Validate
        │
        ▼
Initialize
        │
        ▼
Discover Models
        │
        ▼
Ready
        │
        ▼
Generate
        │
        ▼
Shutdown
```

---

## Configure

Load configuration.

Examples

- API key
- Base URL
- Timeout
- Model ID

---

## Validate

Verify configuration.

Examples

- Credential format
- Endpoint reachability
- Required parameters

---

## Initialize

Create provider resources.

Examples

- HTTP client
- Authentication
- Connection pools

---

## Discover Models

Retrieve available models and their capabilities.

This step allows runtime validation before inference begins.

---

## Ready

Provider is idle and available.

---

## Generate

Provider performs inference.

Responsibilities include:

- Formatting payloads
- Streaming tokens
- Returning tool requests
- Returning structured responses

---

## Shutdown

Release all provider resources.

Examples

- Close connections
- Dispose HTTP clients
- Remove runtime credentials
- Flush telemetry

---

# Provider State Machine

```
UNCONFIGURED
        │
        ▼
CONFIGURED
        │
        ▼
VALIDATED
        │
        ▼
INITIALIZED
        │
        ▼
READY
        │
        ▼
GENERATING
        │
        ▼
READY

ERROR

SHUTDOWN
```

The Provider Manager owns all state transitions.

---

# Provider Interface

Every Provider implementation must expose a common interface.

## Lifecycle

- Initialize
- Shutdown

---

## Connectivity

- Health Check

---

## Discovery

- List Models
- Load Model
- Get Model Capabilities

---

## Inference

- Generate Response
- Stream Response

---

## Capability Discovery

Providers must expose capability queries instead of relying on provider-specific branching.

Examples

- Supports Streaming
- Supports Tool Calling
- Supports Embeddings
- Supports Vision

The remainder of AdityaCLI should never contain provider-specific conditional logic.

---

## Data Translation

Providers translate between:

Application Runtime Format

↓

Provider API Format

↓

Provider Response

↓

Application Runtime Format

This translation layer is owned exclusively by the Provider.

---

# Provider Manager

The Provider Manager owns runtime provider management.

Responsibilities include:

- Active Provider
- Active Model
- Provider switching
- Configuration validation
- Health monitoring
- Provider lifecycle
- Error propagation

The Agent communicates only with the Provider Manager.

---

# Provider Registry

The Provider Registry stores every available Provider implementation.

Examples

- LM Studio Provider
- OpenAI Provider
- Anthropic Provider
- Ollama Provider
- Gemini Provider

Adding a new Provider requires:

1. Implement Provider Interface.
2. Register Provider.

No other subsystem should require modification.

---

# Error Handling

Provider implementations report technical failures.

Examples

- Authentication failed
- Provider offline
- Model unavailable
- Timeout

The Provider Manager determines the application response.

Examples

- Retry
- Display error
- Switch Provider
- Abort request

---

# Design Principles

- Provider independent
- Runtime configurable
- Streaming first
- Capability driven
- Replaceable implementations
- No provider-specific business logic
- No direct Provider access outside the Provider Manager

---

# Supported Providers

## V2.0.0

- LM Studio

## Planned

- Ollama
- OpenAI
- Anthropic
- Gemini

---

# V2.0.0 Scope

Included

- LM Studio Provider
- Provider Manager
- Provider Registry
- Streaming
- Health checking
- Model discovery

Deferred

- Multi-provider routing
- Provider load balancing
- Automatic provider failover
- Cost optimization
- Distributed inference