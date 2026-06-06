"""
Windows OS との統合ユーティリティ (Phase 2) のテスト。
CTypes や subprocess をモックして検証します。
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from src.core.system.windows_tasks import (
    LOGON_TASK_NAME,
    WATCHDOG_TASK_NAME,
    install_scheduled_tasks,
    is_admin,
    remove_scheduled_tasks,
    run_as_admin,
)


@patch("src.core.system.windows_tasks.ctypes.windll.shell32.IsUserAnAdmin")
def test_is_admin_true(mock_is_admin):
    """管理者権限がある場合のテスト"""
    mock_is_admin.return_value = 1
    assert is_admin() is True


@patch("src.core.system.windows_tasks.ctypes.windll.shell32.IsUserAnAdmin")
def test_is_admin_false(mock_is_admin):
    """管理者権限がない場合のテスト"""
    mock_is_admin.return_value = 0
    assert is_admin() is False


@patch("src.core.system.windows_tasks.ctypes.windll.shell32.ShellExecuteW")
def test_run_as_admin_success(mock_shell_execute):
    """UAC昇格リクエストが成功した場合のテスト"""
    mock_shell_execute.return_value = 42  # > 32 is success
    result = run_as_admin(executable="test.exe", parameters="--foo")
    assert result is True
    mock_shell_execute.assert_called_once_with(None, "runas", "test.exe", "--foo", None, 1)


@patch("src.core.system.windows_tasks.ctypes.windll.shell32.ShellExecuteW")
def test_run_as_admin_failure(mock_shell_execute):
    """UAC昇格リクエストが失敗した場合のテスト"""
    mock_shell_execute.return_value = 5  # <= 32 is error
    result = run_as_admin(executable="test.exe", parameters="--foo")
    assert result is False


@patch("src.core.system.windows_tasks.is_admin", return_value=True)
@patch("src.core.system.windows_tasks.subprocess.run")
def test_install_scheduled_tasks_success(mock_run, mock_is_admin, tmp_path):
    """タスクスケジューラへの登録が成功した場合のテスト"""
    hub_path = tmp_path / "LogicHive-Hub.exe"
    hub_path.touch()

    result = install_scheduled_tasks(hub_path)
    assert result is True
    assert mock_run.call_count == 2

    # Logon task check
    call1 = mock_run.call_args_list[0]
    args1 = call1[0][0]
    assert "schtasks" in args1
    assert "/create" in args1
    assert LOGON_TASK_NAME in args1

    # Watchdog task check
    call2 = mock_run.call_args_list[1]
    args2 = call2[0][0]
    assert WATCHDOG_TASK_NAME in args2
    assert "hourly" in args2


@patch("src.core.system.windows_tasks.is_admin", return_value=False)
def test_install_scheduled_tasks_not_admin(mock_is_admin, tmp_path):
    """管理者権限がない場合は登録が失敗することのテスト"""
    result = install_scheduled_tasks(tmp_path / "LogicHive-Hub.exe")
    assert result is False


@patch("src.core.system.windows_tasks.is_admin", return_value=True)
@patch("src.core.system.windows_tasks.subprocess.run")
def test_remove_scheduled_tasks_success(mock_run, mock_is_admin):
    """タスクスケジューラからの削除が成功した場合のテスト"""
    result = remove_scheduled_tasks()
    assert result is True
    assert mock_run.call_count == 3  # logon, watchdog, folder

    calls = mock_run.call_args_list
    assert LOGON_TASK_NAME in calls[0][0][0]
    assert WATCHDOG_TASK_NAME in calls[1][0][0]
