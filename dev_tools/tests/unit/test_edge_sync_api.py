from unittest.mock import MagicMock, patch
import pytest
from edge.sync import GitHubSyncEngine


@pytest.fixture
def sync_engine():
    engine = GitHubSyncEngine()
    engine.local_dir = MagicMock()
    engine.functions_dir = MagicMock()
    engine._initialized = True
    engine._repo = MagicMock()
    return engine


@patch("edge.sync.get_db_connection")
@patch("edge.sync.httpx.Client")
@patch("edge.sync.config.HUB_URL", "http://mockhub")
def test_edge_sync_push_delegates_to_hub(mock_client_class, mock_get_conn, sync_engine):
    # Setup mock DB
    mock_conn = MagicMock()
    mock_get_conn.return_value = mock_conn

    # Mock export to cache (return True)
    with patch.object(sync_engine, "_export_to_cache") as mock_export:
        mock_export.return_value = True

        # Mock file read
        mock_file_content = '{"name": "test_f", "code": "pass"}'
        with patch(
            "edge.sync.open",
            MagicMock(
                return_value=MagicMock(
                    __enter__=lambda s: MagicMock(read=lambda: mock_file_content)
                )
            ),
        ):
            # Wait, easier to mock json.load
            with patch("edge.sync.json.load") as mock_json_load:
                mock_json_load.return_value = {"name": "test_f", "code": "pass"}

                # Setup mock HTTP client
                mock_client = MagicMock()
                mock_client_class.return_value.__enter__.return_value = mock_client
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_client.post.return_value = mock_resp

                # Run
                result = sync_engine.push("test_f")

                # Verify
                assert result is True
                mock_client.post.assert_called_once()
                args, kwargs = mock_client.post.call_args
                assert args[0] == "http://mockhub/api/v1/sync/push"
                assert kwargs["json"]["name"] == "test_f"


@patch("edge.sync.get_db_connection")
@patch("edge.sync.httpx.Client")
@patch("edge.sync.config.HUB_URL", "http://mockhub")
def test_edge_sync_push_failure_handling(mock_client_class, mock_get_conn, sync_engine):
    # Setup mock to return 500 error
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("Hub Error")
    mock_client.post.return_value = mock_resp

    with patch.object(sync_engine, "_export_to_cache", return_value=True):
        with patch("edge.sync.json.load", return_value={}):
            # Run
            result = sync_engine.push("fail_func")

            # Verify
            assert result is False
