from unittest.mock import AsyncMock, patch

import pytest

from core.exceptions import AIProviderError, SyntaxValidationError
from orchestrator import do_save_async, do_search_async


@pytest.mark.asyncio
async def test_sync_rejection_flow_interaction():
    """Verifies that do_save_async rejects structural errors BEFORE saving to DB."""
    # Mock storage to ensure it's NOT called if validation fails
    with patch("orchestrator.sqlite_storage") as mock_storage:
        mock_storage.get_function_by_hash = AsyncMock(return_value=None)

        # Broken JS
        code = "function err() { "
        with pytest.raises(SyntaxValidationError) as excinfo:
            await do_save_async(name="test_js", code=code, language="javascript")

        assert "Structural Error" in str(excinfo.value)
        # Ensure upsert was NEVER called
        assert mock_storage.upsert_function.call_count == 0


@pytest.mark.asyncio
async def test_search_retry_mechanism_success():
    """Verifies that search retries on transient failures and eventually succeeds."""
    with patch("orchestrator.LogicIntelligence") as mock_intel_cls:
        mock_intel = mock_intel_cls.return_value

        # Scenario: 2 failures then 1 success
        mock_intel.expand_query = AsyncMock(
            side_effect=[
                AIProviderError("Transient 1"),
                AIProviderError("Transient 2"),
                "expanded query",
            ]
        )
        mock_intel.generate_embedding = AsyncMock(return_value=[0.1] * 768)
        mock_intel.rerank_results = AsyncMock(return_value=[{"name": "hit", "similarity": 0.9}])

        with patch(
            "orchestrator.sqlite_storage.find_similar_functions", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = [{"name": "hit", "code": "pass", "description": "desc"}]

            results = await do_search_async(query="test retry")

            assert len(results) == 1
            assert results[0]["name"] == "hit"
            # LogicIntelligence should have been called 3 times for expand_query
            assert mock_intel.expand_query.call_count == 3


@pytest.mark.asyncio
async def test_search_retry_exhaustion():
    """Verifies that search eventually gives up after max retries."""
    with patch("orchestrator.LogicIntelligence") as mock_intel_cls:
        mock_intel = mock_intel_cls.return_value

        # Scenario: Always fail
        mock_intel.expand_query = AsyncMock(side_effect=AIProviderError("Permanent Failure"))

        with pytest.raises(AIProviderError) as excinfo:
            await do_search_async(query="test exhaustion")

        assert "Permanent Failure" in str(excinfo.value)
        # Max retries is 3
        assert mock_intel.expand_query.call_count == 3
