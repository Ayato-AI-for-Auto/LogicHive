import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from hub.consolidation import LogicIntelligence
from hub.supabase_api import SupabaseStorage

@pytest.mark.asyncio
async def test_optimize_metadata():
    """Verify that AI-driven metadata optimization returns expected keys."""
    # Mocking genai client
    api_key = "test_key"
    intel = LogicIntelligence(api_key)
    intel.client = MagicMock()
    
    mock_response = MagicMock()
    mock_response.text = '{"get": "never_mind", "description": "Professional description", "tags": ["tag1", "tag2"]}'
    intel.client.models.generate_content = MagicMock(return_value=mock_response)
    
    code = "def hello(): pass"
    result = await intel.optimize_metadata(code)
    
    assert "description" in result
    assert "tags" in result
    assert result["description"] == "Professional description"
    assert "tag1" in result["tags"]

@pytest.mark.asyncio
async def test_increment_call_count_manual_fallback():
    """Verify that the manual fallback for call_count increment works."""
    storage = SupabaseStorage()
    storage._client = MagicMock()
    
    # Mock RPC failure
    storage._client.rpc = MagicMock(side_effect=Exception("RPC not found"))
    
    # Mock table sequence
    mock_table = MagicMock()
    storage._client.table = MagicMock(return_value=mock_table)
    
    mock_select = MagicMock()
    mock_table.select = MagicMock(return_value=mock_select)
    mock_select.eq = MagicMock(return_value=mock_select)
    
    mock_resp_data = MagicMock()
    mock_resp_data.data = [{"call_count": 5}]
    mock_select.execute = MagicMock(return_value=mock_resp_data)
    
    mock_update = MagicMock()
    mock_table.update = MagicMock(return_value=mock_update)
    mock_update.eq = MagicMock(return_value=mock_update)
    mock_update.execute = MagicMock()
    
    success = await storage.increment_call_count("test_func")
    
    assert success is True
    mock_table.update.assert_called_with({"call_count": 6})
