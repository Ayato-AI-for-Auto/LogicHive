# ADR-0033: Record Raw LLM Outputs and Provider Metadata in Quality Gate

Date: 2026-07-05
Status: Accepted

## Context
LogicHive's Quality Gate uses LLMs to evaluate code assets. Currently, only the parsed `score` and `reason` are stored in the database. This lack of raw trace makes debugging prompt failures, auditing AI decisions, and improving the evaluation logic difficult. Furthermore, without recording the specific model used, comparing quality metrics across model versions is impossible.

## Decision
We will record the raw LLM response and the provider metadata (provider name, model ID) for all AI-based evaluations in the `verification_report` field within the `logichive_functions` table.

## Implementation Details
1.  **`EvaluationResult`**: Add `details` field to store arbitrary metadata (already exists).
2.  **`LogicIntelligence`**: Introduce `_call_llm_async_raw()` to capture both parsed results and raw response strings without breaking existing callers of `_call_llm_async`.
3.  **`AIGateEvaluator`**: Populate the `EvaluationResult.details` dictionary with `raw_output` and `provider_info` during evaluation.
4.  **Storage**: The `verification_report` JSON field will automatically include these nested details via the existing `_serialize_results` serialization flow.

## Consequences
- **Positive**:
    - Complete traceability of AI-based quality gate decisions.
    - Ability to re-parse raw outputs if evaluation logic changes in the future, avoiding redundant LLM API calls.
    - Improved debugging of prompt-response issues.
    - Accurate tracking of evaluation performance per model version.
- **Negative**:
    - Increased storage usage in the `logichive_functions` table (negligible for the current scale).
    - Minor increase in data serialization complexity.
