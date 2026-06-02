# ADR-0014: Standardized Hybrid Configuration Strategy

- **Date**: 2026-06-02
- **Status**: Accepted
- **Deciders**: ユーザー, Gemini CLI

## Context
LogicHive is designed with a "Local-First, Cloud-Optional" philosophy. However, the initial configuration structure was ambiguous, failing to clearly distinguish between local execution (Ollama + FastEmbed) and cloud-hybrid execution (Gemini API). This ambiguity led to configuration errors, such as accidental usage of cloud models or connection failures when local services were not properly prioritized.

## Decision
We will restructure the system configuration (`.env` and `src/core/config.py`) to explicitly support a hybrid model. The configuration will be divided into three clear logical sections:

1.  **Selection Layer**: Global flags to switch between `ollama/gemini` for LLM and `fastembed/gemini` for Embeddings.
2.  **Local-First Layer (Default)**: Pre-configured settings for zero-cost, private execution using Ollama and FastEmbed.
3.  **Cloud-Hybrid Layer (Optional)**: High-precision settings using Gemini API, pre-populated with formal model identifiers for the Gemma 4 series.

Key model defaults are established as follows:
- **Gemini LLM**: `models/gemma-4-31b-it` (High precision auditor)
- **Gemini Embedding**: `models/gemini-embedding-2` (Official stable version)
- **Ollama LLM**: `mistral-large` (Local powerhouse)
- **FastEmbed**: `nomic-ai/nomic-embed-text-v1.5` (Standard lightweight local embedding)

## Consequences

### Positive
-   **Architecture Alignment**: Implementations now strictly follow the "Local-First" design tenet.
-   **Error Prevention**: Explicit sections prevent accidental key exposure or model mismatches.
-   **Improved DX**: Users can switch environments by simply toggling provider names without hunting for obscure model identifiers.

### Negative / Risks
-   **Config Length**: The `.env` file is slightly more verbose due to explicit sectioning.

## References
- ADR-005: Configuration Resolution Strategy
- ADR-011: Separation of Engine (MCP) and Control (Settings GUI)
