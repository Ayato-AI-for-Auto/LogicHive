"""
LogicHive Bootstrapper: ユーザー環境に Hub 実行用の Python 仮想環境を動的構築・管理します。
ADR-0018 (Thin Client + Dynamic Engine) に基づく実装。
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from loguru import logger

from src.core.config import get_logic_hive_home


class LogicHiveBootstrapper:
    def __init__(self):
        self.home_dir = get_logic_hive_home()
        self.venv_dir = self.home_dir / ".venv"
        self.persistent_engine_dir = self.home_dir / "engine"

        # 開発環境か EXE 環境かによって pyproject.toml の場所を特定
        if getattr(sys, "frozen", False):
            # PyInstaller の一時展開先 (sys._MEIPASS)
            self.bundled_root = Path(sys._MEIPASS)
            self.root_dir = self.persistent_engine_dir
        else:
            self.bundled_root = None
            self.root_dir = Path(__file__).parent.parent.parent.parent.resolve()

        self.pyproject_path = self.root_dir / "pyproject.toml"

    def _ensure_engine_source(self):
        """EXE 同梱のソースを永続ディレクトリに展開・更新します (frozen 時のみ)"""
        if not getattr(sys, "frozen", False) or not self.bundled_root:
            return

        logger.info(f"Checking engine source in {self.persistent_engine_dir}")
        bundled_engine = self.bundled_root / "engine"
        bundled_pyproject = self.bundled_root / "pyproject.toml"

        if not bundled_engine.exists():
            logger.error("Critical: Bundled engine source not found inside EXE.")
            return

        # 同期または上書きコピー
        try:
            self.persistent_engine_dir.mkdir(parents=True, exist_ok=True)

            # src ディレクトリのコピー (engine/src -> ~/.logichive/engine/src)
            target_src = self.persistent_engine_dir / "src"
            if target_src.exists():
                shutil.rmtree(target_src)
            shutil.copytree(bundled_engine / "src", target_src)

            # pyproject.toml のコピー (pyproject.toml -> ~/.logichive/engine/pyproject.toml)
            shutil.copy2(bundled_pyproject, self.persistent_engine_dir / "pyproject.toml")

            logger.info("Engine source updated successfully from bundle.")
        except Exception as e:
            logger.error(f"Failed to extract engine source: {e}")

    def is_venv_ready(self) -> bool:
        """仮想環境が構築済みで、python.exe が存在するかチェック"""
        python_exe = self.get_venv_python()
        # 開発環境でない場合は、ソース自体の存在もチェック
        if getattr(sys, "frozen", False) and not self.pyproject_path.exists():
            return False
        return python_exe.exists()

    def get_venv_python(self) -> Path:
        """仮想環境内の Python 実行ファイルのパスを返す"""
        if sys.platform == "win32":
            return self.venv_dir / "Scripts" / "python.exe"
        return self.venv_dir / "bin" / "python"

    def _find_uv(self) -> str:
        """システム上の uv コマンドを探す。無ければ例外。"""
        uv_path = shutil.which("uv")
        if not uv_path:
            # ユーザーにインストールを促すか、将来的に uv 自体も同梱することを検討
            raise FileNotFoundError(
                "uv command not found. Please install 'uv' to bootstrap LogicHive."
            )
        return uv_path

    async def setup_environment(
        self, progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        ~/.logichive/.venv を構築し、依存関係をインストールします。

        Args:
            progress_callback: 進行状況（メッセージ）を通知するコールバック関数
        """
        uv = self._find_uv()

        try:
            # 0. ソースの展開 (frozen の場合のみ)
            if progress_callback:
                progress_callback("Extracting engine source...")
            self._ensure_engine_source()

            if progress_callback:
                progress_callback("Creating virtual environment in ~/.logichive/.venv...")

            self.home_dir.mkdir(parents=True, exist_ok=True)

            # 1. venv の作成
            # --system-site-packages を使わないクリーンな環境を作る
            subprocess.run(
                [uv, "venv", str(self.venv_dir)],
                check=True,
                capture_output=True,
                text=True,
                creationflags=0x08000000 if sys.platform == "win32" else 0,
            )

            # 2. 依存関係のインストール (pyproject.toml を使用)
            if progress_callback:
                progress_callback("Installing Hub Engine dependencies (ChromaDB, etc.)...")

            if not self.pyproject_path.exists():
                logger.error(f"pyproject.toml not found at {self.pyproject_path}")
                return False

            # uv pip install -r pyproject.toml 的な挙動
            # 実際には uv sync の方が早いが、ここではシンプルに pip install を使う
            subprocess.run(
                [uv, "pip", "install", "-e", str(self.root_dir)],
                env={**os.environ, "VIRTUAL_ENV": str(self.venv_dir)},
                check=True,
                capture_output=True,
                text=True,
                creationflags=0x08000000 if sys.platform == "win32" else 0,
            )

            if progress_callback:
                progress_callback("Hub Engine is ready.")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Bootstrapper: Subprocess failed: {e.stderr}")
            if progress_callback:
                progress_callback(f"Error: {e.stderr}")
            return False
        except Exception as e:
            logger.exception("Bootstrapper: Unexpected error during setup")
            if progress_callback:
                progress_callback(f"Unexpected Error: {e}")
            return False

    def run_hub_background(self) -> Optional[subprocess.Popen]:
        """構築した venv を使って Hub (mcp_server.py) をバックグラウンドで起動する"""
        python_exe = self.get_venv_python()
        server_script = self.root_dir / "src" / "mcp_server.py"

        if not python_exe.exists() or not server_script.exists():
            logger.error("Cannot start Hub: Python or server script missing.")
            return None

        logger.info(f"Starting LogicHive Hub using venv: {python_exe}")

        # ログを ~/.logichive/logs/hub.log に出すように設定
        log_dir = self.home_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "hub.log"

        with open(log_file, "a") as f:
            proc = subprocess.Popen(
                [str(python_exe), str(server_script)],
                stdout=f,
                stderr=f,
                cwd=str(self.root_dir),
                creationflags=0x08000000 if sys.platform == "win32" else 0,
                start_new_session=True,  # 親(Settings)が閉じても死なないようにする
            )
        return proc
