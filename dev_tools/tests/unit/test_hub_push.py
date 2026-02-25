import json
from unittest.mock import MagicMock, patch
import pytest
from hub.github_api import push_function_to_github

@patch("hub.github_api.Github")
@patch("hub.github_api.GITHUB_TOKEN", "mock_token")
@patch("hub.github_api.GITHUB_STORAGE_REPO", "mock/repo")
def test_push_function_to_github_new_file(mock_github_class):
    # Setup mock repo
    mock_g = MagicMock()
    mock_github_class.return_value = mock_g
    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo
    
    # Mock get_contents to raise exception (file not found)
    mock_repo.get_contents.side_effect = Exception("Not Found")
    
    # Run
    result = push_function_to_github(
        name="test_func",
        code="print('hello')",
        description="test desc",
        tags=["test"],
        dependencies=["req1"]
    )
    
    # Verify
    assert result is True
    mock_repo.create_file.assert_called_once()
    args, kwargs = mock_repo.create_file.call_args
    assert args[0] == "functions/test_func.json"
    assert "Register new function" in args[1]
    
    # Check JSON content
    data = json.loads(args[2])
    assert data["name"] == "test_func"
    assert data["code"] == "print('hello')"
    assert data["tags"] == ["test"]

@patch("hub.github_api.Github")
@patch("hub.github_api.GITHUB_TOKEN", "mock_token")
def test_push_function_to_github_update_file(mock_github_class):
    # Setup mock repo
    mock_g = MagicMock()
    mock_github_class.return_value = mock_g
    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo
    
    # Mock get_contents to return existing file
    mock_contents = MagicMock()
    mock_contents.path = "functions/test_func.json"
    mock_contents.sha = "old_sha"
    mock_repo.get_contents.return_value = mock_contents
    
    # Run
    result = push_function_to_github(
        name="test_func",
        code="print('updated')",
        description="updated desc"
    )
    
    # Verify
    assert result is True
    mock_repo.update_file.assert_called_once()
    args, kwargs = mock_repo.update_file.call_args
    assert args[0] == "functions/test_func.json"
    assert "Update function" in args[1]
    assert args[3] == "old_sha"
    
    # Check JSON content
    data = json.loads(args[2])
    assert data["code"] == "print('updated')"

@patch("hub.github_api.GITHUB_TOKEN", "")
def test_push_function_to_github_no_token():
    # Run without token
    result = push_function_to_github(name="fail", code="pass")
    assert result is False
