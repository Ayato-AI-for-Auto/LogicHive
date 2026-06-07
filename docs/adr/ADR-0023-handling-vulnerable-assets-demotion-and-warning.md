# ADR-0023: Handling Vulnerable Assets (Demotion & Warning)

- **Date**: 2026-06-07
- **Status**: Accepted
- **Deciders**: ayato-labs (User), Antigravity (Agent)

## Context
When an asset's pinned dependency is flagged as vulnerable (ADR-0022), handling the asset requires a balance between stability and security:
- Deleting the asset immediately breaks backward compatibility for existing client scripts or workflows referencing it.
- Leaving the asset in search results without warning risks exposing LLM agents and human developers to security exploits.
- If a user registers a new, patched version of the function, the RAG search should naturally prioritize it over the vulnerable version without manual intervention.

## Decision
We will handle vulnerable logic assets using a dual-layered deprecation policy:

1. **RAG Ranking Demotion (Debuff)**:
   - When a vulnerability is flagged, the asset's `reliability_score` will be discounted. In the Scaled Multiplicative Model (ADR-0021), this demotes the asset to the bottom of the search ranking.
   - If a new, secure version of the function is saved with high similarity, it will automatically bubble to the top of search results, ensuring a seamless, self-healing migration path.

2. **MCP Response Warnings**:
   - Instead of hiding the code, LogicHive will include a standardized security warning banner (e.g., `[SECURITY WARNING: Vulnerability CVE-XXXX-XXXX detected in dependency Y]`) in the returned MCP server code responses and metadata.
   - This guides LLM callers and human developers to actively avoid or upgrade the dependency instead of silently using insecure code.

## Consequences
### Positive
- **No Breaking Changes**: Existing code referencing the old asset does not break because the asset remains in the database.
- **Seamless Upgrade Path**: Fixed equivalents naturally overtake vulnerable ones in search ranking.
- **Agent Safety**: Explicit warning annotations prevent LLMs from silently adopting vulnerable snippets.

### Negative / Risks
- Vulnerable assets are still executable if explicitly requested by ID or name; client scripts must still be updated.

## References
- ADR-0021: Score-Scaled Multiplicative RAG Prioritization
- ADR-0022: External Vulnerability Database (OSV API) Integration
