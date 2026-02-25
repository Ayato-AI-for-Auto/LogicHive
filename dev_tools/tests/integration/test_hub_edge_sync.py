import pytest
import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from hub.app import app
from edge.sync import GitHubSyncEngine
from core import config


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def sync_engine(tmp_path):
    engine = GitHubSyncEngine()
    engine.local_dir = tmp_path
    engine.functions_dir = tmp_path / "functions"
    engine.functions_dir.mkdir(parents=True, exist_ok=True)
    # Mock repo setup to avoid actual git clones
    engine._initialized = True
    engine._repo = MagicMock()
    return engine


@patch("hub.github_api.Github")
@patch("hub.github_api.GITHUB_TOKEN", "mock-hub-token")
@patch("edge.sync.get_db_connection")
def test_full_mediated_push_flow(
    mock_get_db, mock_github_class, test_client, sync_engine, monkeypatch
):
    """
    Integration Test:
    Edge (sync.py) --POST--> Hub (app.py) --API--> GitHub (github_api.py)
    """
    # 1. Mock GitHub Repo structure
    mock_g = MagicMock()
    mock_github_class.return_value = mock_g
    mock_repo = MagicMock()
    mock_g.get_repo.return_value = mock_repo
    mock_repo.get_contents.side_effect = Exception("Not Found")  # Force create_file

    # 2. Mock Edge DB for export
    mock_conn = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.execute.return_value.fetchone.return_value = (
        "test_func",
        "print('hello')",
        "desc",
        '["tag1"]',
        '{"dependencies": []}',
        "[]",
    )

    # Redirect Edge's HUB_URL to match test_client for consistency
    monkeypatch.setattr(config, "HUB_URL", "http://hub.test")

    with patch("edge.sync.httpx.Client") as mock_httpx:
        # Mock httpx.Client to use our TestClient
        mock_httpx.return_value.__enter__.return_value = test_client

        # 4. Run Edge Push
        result = sync_engine.push("test_func")

    # 5. Verify entire chain
    if not result:
        # Print for debugging if it fails

        print(f"Functions dir exists: {sync_engine.functions_dir.exists()}")
        print(f"Files: {list(sync_engine.functions_dir.glob('*'))}")

    assert result is True

    # Verify Hub was called and Hub called GitHub
    mock_repo.create_file.assert_called_once()
    args, _ = mock_repo.create_file.call_args
    assert args[0] == "functions/test_func.json"
    data = json.loads(args[2])
    assert data["name"] == "test_func"
    assert data["code"] == "print('hello')"
