# ADR-006: Star-Driven Open Source Strategy (GitHub Star Focus)

- **Date**: 2026-05-26
- **Status**: Accepted
- **Deciders**: ayato-labs (Human), Antigravity (Agent)

## Context
Making LogicHive a commercial SaaS from the start introduces massive operational overhead, host-side runtime execution security risks (sandboxing costs), and high LLM API hosting costs. Instead of taking on immediate financial deficit (red-ink SaaS) or building complex billing/security layers prematurely, we need a strategy to prove market validation, gain developer adoption, and prevent being front-run by other tools.

## Decision
We decided to adopt a **Star-Driven Open Source Strategy (GitHub Star Focus)**:
1. **Source Code Disclosure**: Distribute the project as open source under the **AGPL-3.0 License** to protect the codebase from silent commercial SaaS exploitation by competitors while remaining completely open.
2. **Career & Portfolio Focus**: Leverage the codebase as a high-quality portfolio piece for career advancement, proving specialized skills in AI Agent architectures, Model Context Protocol (MCP), AST-based quality gates, and system resilience.
3. **Distribution Over Infrastructure**: Prioritize developer adoption (stars, forks, shares) on GitHub over complex cloud infrastructure (GCP/Supabase).
4. **Fast and Open Launch**: Launch the tool early as an open-source project to establish a first-mover advantage rather than delaying to build SaaS-specific features.

## Consequences
### Positive
- **No Hosting Deficit**: Avoids high hosting costs (isolated execution containers, constant SSE connections, LLM APIs).
- **Strong Career Leverage**: Represents a highly sophisticated engineering asset for technical recruitment (advanced Python, AST parsing, MCP integration).
- **Competitor Deterrence**: The AGPL-3.0 license mandates copyleft for network services, preventing others from taking the code and silently SaaS-ifying it.
- **Fast Feedback Loop**: Enables rapid validation of the product concept through organic GitHub stars and developer feedback.

### Negative / Risks
- **No Direct SaaS Revenue**: Relies on commercial licenses for specialized users (dual-licensing) or direct consultation rather than standard SaaS subscriptions.
