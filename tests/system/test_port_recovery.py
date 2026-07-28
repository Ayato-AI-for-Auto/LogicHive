from unittest.mock import MagicMock, patch

import psutil
import pytest

from mcp_server import run_server


# A helper to create mock process objects
def make_mock_process(pid=1234, name="python.exe"):
    proc = MagicMock(spec=psutil.Process)
    proc.pid = pid
    proc.name.return_value = name
    return proc


def test_port_recovery_retry():
    """Test Option 1: Retry port binding after manually freeing the port."""
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", side_effect=["1"]),
        patch("mcp_server.get_conflicting_process", return_value=None),
        patch("uvicorn.run") as mock_run,
    ):
        mock_run.side_effect = [OSError(10048, "Address already in use"), None]

        run_server()

        assert mock_run.call_count == 2


def test_port_recovery_kill():
    """Test Option 2: Kill conflicting process and retry."""
    mock_proc = make_mock_process(pid=5360, name="python.exe")

    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", side_effect=["2"]),
        patch("mcp_server.get_conflicting_process", return_value=mock_proc),
        patch("uvicorn.run") as mock_run,
    ):
        mock_run.side_effect = [OSError(10048, "Address already in use"), None]

        run_server()

        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_once_with(timeout=3)
        assert mock_run.call_count == 2


def test_port_recovery_autofind_with_save():
    """Test Option 3: Auto-find next available port and save to config."""
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", side_effect=["3", "y"]),
        patch("mcp_server.find_available_port", return_value=10881),
        patch("core.config.save_config", return_value=True) as mock_save_config,
        patch("uvicorn.run") as mock_run,
    ):
        mock_run.side_effect = [OSError(10048, "Address already in use"), None]

        run_server()

        mock_save_config.assert_called_once_with({"PORT": 10881})
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[1][1]["port"] == 10881


def test_port_recovery_exit():
    """Test Option 4: Exit application."""
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", side_effect=["4"]),
        patch("mcp_server.wait_on_error"),
        patch("sys.exit", side_effect=SystemExit) as mock_exit,
        patch("uvicorn.run") as mock_run,
    ):
        mock_run.side_effect = OSError(10048, "Address already in use")

        with pytest.raises(SystemExit):
            run_server()

        mock_exit.assert_called_once_with(1)


def test_port_recovery_non_interactive():
    """Test Non-interactive fallback: Auto-find port and run without prompt/saving."""
    with (
        patch("sys.stdin.isatty", return_value=False),
        patch("mcp_server.find_available_port", return_value=10882),
        patch("uvicorn.run") as mock_run,
    ):
        mock_run.side_effect = [OSError(10048, "Address already in use"), None]

        run_server()

        assert mock_run.call_count == 2
        assert mock_run.call_args_list[1][1]["port"] == 10882
