"""
アンインストール用システムユーティリティ (Phase 1) のテスト。
実際のプロセス終了や自己消去を実行するとテストランナーごと終了してしまうため、
主にモックを用いた動作検証を行います。
"""

from unittest.mock import MagicMock, patch

import psutil
import pytest

from src.core.system.uninstall import (
    execute_kamikaze_script,
    kill_logichive_processes,
    remove_data_directory,
)


@pytest.fixture
def mock_get_logic_hive_home():
    with patch("src.core.system.uninstall.get_logic_hive_home") as mock:
        yield mock


def test_remove_data_directory_success(mock_get_logic_hive_home):
    """データディレクトリが正常に削除されることのテスト"""
    mock_dir = MagicMock()
    mock_dir.exists.return_value = True
    mock_get_logic_hive_home.return_value = mock_dir

    with patch("src.core.system.uninstall.shutil.rmtree") as mock_rmtree:
        result = remove_data_directory()

        assert result is True
        mock_rmtree.assert_called_once_with(mock_dir)


def test_remove_data_directory_not_exists(mock_get_logic_hive_home):
    """データディレクトリが存在しない場合は何もせず True を返すことのテスト"""
    mock_dir = MagicMock()
    mock_dir.exists.return_value = False
    mock_get_logic_hive_home.return_value = mock_dir

    with patch("src.core.system.uninstall.shutil.rmtree") as mock_rmtree:
        result = remove_data_directory()

        assert result is True
        mock_rmtree.assert_not_called()


def test_kill_logichive_processes():
    """対象となるプロセス（Hub, Settings）のみに terminate シグナルが送られることのテスト"""
    # モックプロセスの作成
    mock_hub = MagicMock(spec=psutil.Process)
    mock_hub.info = {"pid": 1000, "name": "LogicHive-Hub.exe", "cmdline": []}

    mock_settings = MagicMock(spec=psutil.Process)
    mock_settings.info = {"pid": 1001, "name": "LogicHive-Settings.exe", "cmdline": []}

    mock_other = MagicMock(spec=psutil.Process)
    mock_other.info = {"pid": 1002, "name": "chrome.exe", "cmdline": []}

    mock_self = MagicMock(spec=psutil.Process)
    mock_self.info = {"pid": 9999, "name": "python.exe", "cmdline": ["pytest"]}

    mock_processes = [mock_hub, mock_settings, mock_other, mock_self]

    with patch("src.core.system.uninstall.psutil.process_iter", return_value=mock_processes), \
         patch("src.core.system.uninstall.os.getpid", return_value=9999), \
         patch("src.core.system.uninstall.psutil.wait_procs"):

        kill_logichive_processes()

        # Hub と Settings は終了される
        mock_hub.terminate.assert_called_once()
        mock_settings.terminate.assert_called_once()

        # Chrome や 自プロセスは終了されない
        mock_other.terminate.assert_not_called()
        mock_self.terminate.assert_not_called()


@patch("src.core.system.uninstall.subprocess.Popen")
@patch("src.core.system.uninstall.tempfile.mkstemp")
def test_execute_kamikaze_script(mock_mkstemp, mock_popen, tmp_path):
    """
    指定したファイル群を削除するバッチファイルが生成され、
    バックグラウンドで実行されることのテスト。
    """
    # 一時ファイルのモック設定
    mock_fd = 123
    mock_bat_path = tmp_path / "test_kamikaze.bat"
    mock_mkstemp.return_value = (mock_fd, str(mock_bat_path))

    # 削除対象として扱うダミーファイルを作成
    target1 = tmp_path / "target1.exe"
    target2 = tmp_path / "target2.exe"
    target1.touch()
    target2.touch()

    # fdopenをモックして書き込み内容をキャプチャする
    mock_file = MagicMock()
    with patch("src.core.system.uninstall.os.fdopen", return_value=mock_file) as mock_fdopen:
        execute_kamikaze_script([target1, target2])

        mock_fdopen.assert_called_once_with(mock_fd, "w")

        # バッチファイルの内容が正しく書き込まれたか確認
        written_content = mock_file.__enter__().write.call_args[0][0]
        assert "ping 127.0.0.1 -n 3" in written_content
        assert f'del /F /Q "{target1.absolute()}"' in written_content
        assert f'del /F /Q "{target2.absolute()}"' in written_content
        assert 'del "%~f0"' in written_content  # 自己削除コマンドが含まれているか

    # Popen が正しい引数（黒窓非表示オプション等）で呼び出されたか確認
    mock_popen.assert_called_once_with(
        ["cmd.exe", "/c", str(mock_bat_path)],
        creationflags=0x08000000,
        close_fds=True,
    )
