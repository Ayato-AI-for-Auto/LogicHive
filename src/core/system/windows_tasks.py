"""
Windows OS との統合ユーティリティ (Phase 2)。
タスクスケジューラへの自動起動登録と、UAC (管理者権限) の制御を提供します。
"""

import ctypes
import subprocess
import sys
from pathlib import Path

from loguru import logger

TASK_FOLDER = r"LogicHive"
LOGON_TASK_NAME = rf"{TASK_FOLDER}\LogicHive-Hub-Logon"
WATCHDOG_TASK_NAME = rf"{TASK_FOLDER}\LogicHive-Hub-Watchdog"


def is_admin() -> bool:
    """現在のプロセスが管理者権限 (UAC昇格済み) で動作しているか判定します。"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logger.error(f"Failed to check admin status: {e}")
        return False


def run_as_admin(executable: str = None, parameters: str = "") -> bool:
    """
    指定された実行ファイルを管理者権限で実行します。
    ユーザーに UAC プロンプトが表示されます。

    Args:
        executable: 実行するファイルのパス。None の場合は現在の実行ファイル (sys.executable) を使用します。
        parameters: コマンドライン引数

    Returns:
        bool: プロセス起動要求が成功したか (※起動したプロセスの成否ではありません)
    """
    if executable is None:
        executable = sys.executable

    logger.info(f"Requesting UAC elevation for: {executable} {parameters}")
    try:
        # ShellExecuteW
        # (hwnd, operation, file, parameters, directory, showcmd)
        # operation="runas" が UAC 昇格のトリガーとなる
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            parameters,
            None,
            1  # SW_SHOWNORMAL
        )
        # 成功すると 32 より大きい値が返る
        if result > 32:
            return True
        else:
            logger.warning(f"ShellExecuteW failed with code: {result}")
            return False
    except Exception as e:
        logger.error(f"Failed to run as admin: {e}")
        return False


def install_scheduled_tasks(hub_exe_path: Path) -> bool:
    """
    Windows タスクスケジューラに自動起動設定を登録します。
    ※この関数は管理者権限で実行されている必要があります。

    Args:
        hub_exe_path: 登録する LogicHive Hub の実行ファイルパス

    Returns:
        bool: 全ての登録が成功したか
    """
    if not is_admin():
        logger.error("install_scheduled_tasks requires administrator privileges.")
        return False

    exe_path_str = str(hub_exe_path.absolute())
    if not hub_exe_path.exists():
        logger.warning(f"Registering scheduled task for a path that does not exist currently: {exe_path_str}")

    success = True

    # schtasks はクォートの中に引数を含める場合、少し癖がある。
    # ここでは単純に EXE 自体を起動するタスクにする。
    # 実際には Hub 側に重複起動防止（ポート占有やMutex）の仕組みがある前提とする。

    # 1. ログオン時起動タスク
    logger.info("Registering Logon Task...")
    logon_cmd = [
        "schtasks", "/create", "/tn", LOGON_TASK_NAME,
        "/tr", f'"{exe_path_str}"',
        "/sc", "onlogon",
        "/rl", "highest",  # 最高特権(管理者権限)で実行
        "/f"               # 既存のタスクを上書き
    ]
    try:
        subprocess.run(logon_cmd, check=True, capture_output=True, text=True, creationflags=0x08000000)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create Logon task: {e.stderr}")
        success = False

    # 2. 1時間ごとの死活監視(Watchdog)タスク
    logger.info("Registering Hourly Watchdog Task...")
    watchdog_cmd = [
        "schtasks", "/create", "/tn", WATCHDOG_TASK_NAME,
        "/tr", f'"{exe_path_str}"',
        "/sc", "hourly", "/mo", "1",
        "/rl", "highest",
        "/f"
    ]
    try:
        subprocess.run(watchdog_cmd, check=True, capture_output=True, text=True, creationflags=0x08000000)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create Watchdog task: {e.stderr}")
        success = False

    return success


def remove_scheduled_tasks() -> bool:
    """
    登録済みのタスクをタスクスケジューラから削除します。
    ※この関数は管理者権限で実行されている必要があります。
    """
    if not is_admin():
        logger.error("remove_scheduled_tasks requires administrator privileges.")
        return False

    success = True

    # 1. タスクの削除
    for task_name in [LOGON_TASK_NAME, WATCHDOG_TASK_NAME]:
        logger.info(f"Removing task: {task_name}")
        cmd = ["schtasks", "/delete", "/tn", task_name, "/f"]
        try:
            # 存在しない場合のエラーは無視する
            subprocess.run(cmd, check=True, capture_output=True, text=True, creationflags=0x08000000)
        except subprocess.CalledProcessError as e:
            if "ERROR: The specified task name" not in e.stderr:
                logger.error(f"Failed to remove task {task_name}: {e.stderr}")
                success = False
            else:
                logger.info(f"Task {task_name} already removed or not found.")

    # 2. フォルダの削除 (空になっていれば)
    logger.info(f"Removing task folder: {TASK_FOLDER}")
    folder_cmd = ["schtasks", "/delete", "/tn", TASK_FOLDER, "/f"]
    try:
         subprocess.run(folder_cmd, check=True, capture_output=True, text=True, creationflags=0x08000000)
    except subprocess.CalledProcessError:
         pass # フォルダの削除は空でないと失敗するか、そもそも削除コマンドの挙動が異なるため、厳密にチェックしない

    return success
