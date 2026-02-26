import pytest
from core.config import GEMINI_API_KEY


def test_embedding_dimension_logic():
    """Verify that the embedding logic specifies 768 dimensions."""
    # Assuming there's a class/function that handles this
    # We want to ensure output_dimensionality=768 is always used
    from hub.consolidation import LogicIntelligence

    intel = LogicIntelligence(api_key="fake_key")
    # This is more of a code audit test
    import inspect

    source = inspect.getsource(intel.generate_embedding)
    assert "output_dimensionality=768" in source


@pytest.mark.skipif(not GEMINI_API_KEY, reason="No API key for live embedding test")
def test_live_embedding_dimension():
    """Test actual embedding dimension if API key is available."""
    from hub.consolidation import LogicIntelligence

    intel = LogicIntelligence(api_key=GEMINI_API_KEY)
    import asyncio

    loop = asyncio.get_event_loop()
    embedding = loop.run_until_complete(intel.generate_embedding("test text"))
    assert len(embedding) == 768
