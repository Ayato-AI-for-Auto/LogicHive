"""
アンインストールおよびOS統合の基礎となるシステムユーティリティ。
Phase 1: プロセス終了、データ削除、自己消去スクリプト機能を提供します。
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import psutil
from loguru import logger

from src.core.config import get_logic_hive_home


def kill_logichive_processes() -> None:
    """
    LogicHive に関連するプロセス (Hub, Settings) を安全に終了します。
    自プロセスは終了させません。
    """
    current_pid = os.getpid()
    # 開発環境(python.exe)の場合は、スクリプト名で判定する必要があるが、
    # 簡略化のため EXE 化された環境を主眼に置く。

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info["pid"] == current_pid:
                continue

            # プロセス名での判定
            name = proc.info["name"]
            if name and any(
                target.lower() in name.lower() for target in ["logichive-hub", "logichive-settings"]
            ):
                logger.info(f"Terminating LogicHive process: {name} (PID: {proc.info['pid']})")
                proc.terminate()
                continue

            # 開発環境用: コマンドライン引数での判定
            cmdline = proc.info["cmdline"]
            if cmdline and name and "python" in name.lower():
                if any("mcp_server.py" in arg or "settings_ui.py" in arg for arg in cmdline):
                    logger.info(
                        f"Terminating LogicHive python script: {cmdline} (PID: {proc.info['pid']})"
                    )
                    proc.terminate()

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # 終了を少し待つ
    psutil.wait_procs(psutil.process_iter(), timeout=3)


def remove_data_directory() -> bool:
    """
    ユーザーデータディレクトリ (~/.logichive) を削除します。

    Returns:
        bool: 削除が成功したか（ディレクトリが存在しなかった場合も True）
    """
    data_dir = get_logic_hive_home()
    if not data_dir.exists():
        logger.info(f"Data directory does not exist: {data_dir}")
        return True

    try:
        logger.warning(f"Removing LogicHive data directory: {data_dir}")
        shutil.rmtree(data_dir)
        return True
    except Exception as e:
        logger.error(f"Failed to remove data directory {data_dir}: {e}")
        return False


def execute_kamikaze_script(executables_to_delete: list[Path] = None) -> None:
    """
    自身（および関連する EXE）を削除するための一時バッチファイルを生成し、実行します。
    呼び出し元は、この関数を実行した直後にプロセスを終了させる必要があります。

    Args:
        executables_to_delete: 削除対象のファイルのリスト。None の場合は sys.executable のみ。
    """
    if executables_to_delete is None:
        executables_to_delete = [Path(sys.executable)]

    # 実際に存在するファイルだけを対象にする
    targets = [str(p.absolute()) for p in executables_to_delete if p.exists()]
    if not targets:
        logger.info("No executables found to delete via kamikaze script.")
        return

    # バッチファイルの内容
    # 1. ping で数秒待機 (プロセスが完全に終了するのを待つため)
    # 2. 対象ファイルを削除 (ループ)
    # 3. 自分自身(バッチファイル)を削除
    bat_content = "@echo off\n"
    bat_content += "echo Uninstalling LogicHive...\n"
    # timeout コマンドはリダイレクト環境などで失敗することがあるため、古典的な ping ループを使用
    bat_content += "ping 127.0.0.1 -n 3 > nul\n"

    for target in targets:
        bat_content += f'del /F /Q "{target}"\n'

    bat_content += 'del "%~f0"\n'

    # Tempディレクトリにバッチを作成
    fd, bat_path = tempfile.mkstemp(suffix=".bat", prefix="logichive_uninstall_", text=True)
    with os.fdopen(fd, "w") as f:
        f.write(bat_content)

    logger.warning(f"Executing kamikaze script at {bat_path} to delete: {targets}")

    # 別プロセスとしてバッチを実行 (親プロセスから切り離す)
    # CREATE_NO_WINDOW (0x08000000) を指定して黒いコンソール画面を出さないようにする
    creationflags = 0x08000000

    subprocess.Popen(
        ["cmd.exe", "/c", bat_path],
        creationflags=creationflags,
        close_fds=True,
    )
