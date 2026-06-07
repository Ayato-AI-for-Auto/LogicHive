# ADR-0021: Score-Scaled Multiplicative RAG Prioritization

- **Date**: 2026-06-07
- **Status**: Accepted
- **Deciders**: ayato-labs (User), Antigravity (Agent)

## Context
LogicHive uses a hybrid retrieval pipeline combining semantic vector search and keyword match to find logic assets.
While each asset is scored on a quality scale (0-100 `reliability_score`), this score was not factored into search priority or ranking, leaving the system vulnerable to bubbling irrelevant high-quality logic or ranking raw/unverified code above identical verified code.

Note that `reliability_score` is a weighted synthesis of multiple validation gates:
* **Deterministic AST assertion check**: 30%
* **Runtime test execution check**: 30%
* **Static analysis & security static checks (Ruff, ESLint, AST vulnerabilities)**: 20%
* **LLM Quality Gate (`ai_gate` using Gemini/Ollama)**: 15%
* **Code metrics check**: 5%

Crucially, the **LLM/AI Gate** holds veto/capping powers over the final `reliability_score`:
1. If the AI Gate scores the asset below 30 (flagged as "Quality Theater" or empty logic), the entire `reliability_score` is forced to **0.0**.
2. If the AI Gate scores the asset below 70, the final score is capped to not exceed the AI Gate score.

Thus, LLM-based evaluation is already a core component of `reliability_score`. Integrating this score into search priority directly allows the LLM's assessment of code quality to influence the search rank.

To blend similarity ($S$) and reliability score ($R$), we compared two mathematical approaches:
1. **Additive Blend**: $w_1 \times S + w_2 \times R_{norm}$
2. **Scaled Multiplicative**: $S \times (w_{min} + (1 - w_{min}) \times R_{norm})$

Simulation results proved that the Additive model introduces noise by allowing completely irrelevant assets with perfect quality scores to bubble to the top. The simple multiplicative model, on the other hand, penalizes valid draft code (e.g. 40% quality) too severely, making them unfindable.


## Decision
We will implement the **Scaled Multiplicative Model** to compute the final search prioritization ranking score:

$$Score_{hybrid} = Similarity \times \left(0.5 + 0.5 \times \frac{ReliabilityScore}{100.0}\right)$$

This ensures that:
- Relevance ($Similarity$) remains the absolute upper bound constraint (preventing irrelevant high-quality code noise).
- Low-quality or draft code (e.g., score = 40) is not completely blacklisted, remaining discoverable under a gentle quality-scaling discount factor ($0.7 \times Similarity$).
- The default minimum multiplier floor is set to `0.5` and will be defined as a configurable variable.

## Consequences
### Positive
- Prevents unrelated top-quality code from polluting search results.
- Preserves search accessibility for draft assets while cleanly prioritizing verified equivalents.
- Highly consistent with modern search engine custom-scoring practices.

### Negative / Risks
- Relies on embedding similarity scoring to be accurate. If embedding similarity is noisy, the scaling won't rescue it.

## References
- Issue: N/A
- Script: [compare_ranking_models.py](file:///c:/Users/saiha/.gemini/antigravity-ide/brain/55c99f94-f891-412f-88dd-5e58ee780825/scratch/compare_ranking_models.py)
