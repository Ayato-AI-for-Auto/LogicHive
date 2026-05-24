# ADR-005: Configuration Resolution Strategy

- **Date**: 2026-05-24
- **Status**: Accepted
- **Deciders**: Gemini CLI, ayato-labs

## Context
LogicHive is distributed in multiple formats: Windows Native EXE, OCI Container, and Source code. Users (non-developers) need a predictable and flexible way to configure API keys (Gemini, GitHub) and model settings (Ollama, Gemini models) without modifying the code or system-wide environment variables unless desired.

The challenge is that "Current Working Directory" (CWD) can change based on how the application is launched, especially with `.exe` files or shortcuts.

## Decision
We implement a tiered configuration resolution strategy for `.env` files with the following priority:

1.  **Local Configuration (Primary)**:
    -   Path: The directory where the executable (`.exe`) or the project root (`src/..`) resides.
    -   Use Case: Portable installations, team-shared setups in a specific folder.
2.  **User Home Configuration (Fallback)**:
    -   Path: `~/.logichive/.env` (e.g., `C:\Users\<User>\.logichive\.env`).
    -   Use Case: Global settings for a single user across multiple projects or folder moves.
3.  **Environment Variables (Override)**:
    -   Standard OS environment variables override `.env` values if already set.

## Consequences

### Positive
-   **Predictability**: Users know exactly where to put the `.env` file (next to the `.exe`).
-   **Flexibility**: Allows both global and local configurations.
-   **Ease of Use**: No need for complex installation steps or system environment variable modifications.

### Negative / Risks
-   **Multiple Files**: Users might forget they have a global `.env` that overrides their expectations if they don't see the local one.
-   **Security**: Sensitive keys are stored in plaintext in the home directory if the fallback is used.

## References
- Issue: #N/A (Configuration Standardization)
- PR: #N/A
- Related ADR: ADR-002 (Dual Distribution)
