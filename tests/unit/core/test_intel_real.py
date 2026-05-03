import pytest

from core.config import GEMINI_API_KEY, VECTOR_DIMENSION
from core.consolidation import LogicIntelligence


@pytest.mark.use_real_intelligence
@pytest.mark.asyncio
async def test_real_embedding_generation():
    """
    Unit Test: Verifies real embedding generation using the actual Gemini API.
    Rule: No MagicMock, no Fake client.
    """
    if not GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not set in environment")

    intel = LogicIntelligence(GEMINI_API_KEY)
    text = "Unit test for real embedding generation in LogicHive."

    embedding = await intel.generate_embedding(text)

    assert isinstance(embedding, list)
    assert len(embedding) == VECTOR_DIMENSION
    assert all(isinstance(v, float) for v in embedding)
    print(f"\n[REAL TEST] Embedding generated successfully. Dimension: {len(embedding)}")


@pytest.mark.use_real_intelligence
@pytest.mark.asyncio
async def test_real_quality_evaluation():
    """
    Unit Test: Verifies real LLM-based quality evaluation.
    Rule: No MagicMock.
    """
    if not GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not set in environment")

    intel = LogicIntelligence(GEMINI_API_KEY)
    code = """
def calculate_area(radius):
    \"\"\"Calculates the area of a circle.\"\"\"
    import math
    return math.pi * radius ** 2
"""

    result = await intel.evaluate_quality(code)

    assert isinstance(result, dict)
    assert "score" in result
    assert "reason" in result
    assert result["score"] >= 0 and result["score"] <= 100
    safe_reason = result["reason"].encode("ascii", "ignore").decode()
    print(f"\n[REAL TEST] Quality evaluation result: {result['score']} - {safe_reason}")


@pytest.mark.use_real_intelligence
@pytest.mark.asyncio
async def test_real_query_expansion():
    """
    Unit Test: Verifies real LLM-based query expansion.
    """
    if not GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not set in environment")

    intel = LogicIntelligence(GEMINI_API_KEY)
    query = "calculate circle area"

    expanded = await intel.expand_query(query)

    assert isinstance(expanded, str)
    assert len(expanded) > len(query)
    assert "circle" in expanded.lower()
    # Safe print for Windows console
    safe_expanded = expanded.encode("ascii", "ignore").decode()
    print(f"\n[REAL TEST] Query expanded: {safe_expanded}")
