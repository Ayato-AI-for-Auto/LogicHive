import pytest

from storage.sqlite_api import sqlite_storage


@pytest.mark.asyncio
async def test_score_based_rag_prioritization(test_db):
    """SYSTEM: Verify that when two functions match a query, the one with higher reliability score is returned first."""
    dummy_embedding = [0.1] * 768  # Match dimension

    # 1. Low quality function
    await sqlite_storage.upsert_function(
        {
            "name": "func_low_quality",
            "code": "def process(): pass",
            "description": "processes input data",
            "tags": ["process"],
            "language": "python",
            "reliability_score": 10.0,
            "embedding": dummy_embedding,
            "project": "rag_test",
            "verification_status": "failed",
        }
    )

    # 2. High quality function
    await sqlite_storage.upsert_function(
        {
            "name": "func_high_quality",
            "code": "def process():\n    return 'processed'",
            "description": "processes input data",
            "tags": ["process"],
            "language": "python",
            "reliability_score": 95.0,
            "embedding": dummy_embedding,
            "project": "rag_test",
            "verification_status": "verified",
        }
    )

    # Perform hybrid search using the same dummy embedding
    results = await sqlite_storage.find_similar_functions(
        embedding=dummy_embedding, query_text="processes input data", project="rag_test", limit=5
    )

    # We expect func_high_quality to be returned first because its reliability_score is much higher,
    # boosting its hybrid search_score even though they have identical similarity.
    assert len(results) == 2
    assert results[0]["name"] == "func_high_quality"
    assert results[1]["name"] == "func_low_quality"
    assert results[0]["search_score"] > results[1]["search_score"]
