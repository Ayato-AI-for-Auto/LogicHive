import asyncio
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Optional

MIN_DISK_SPACE_GB = 3  # Minimum free disk space required to create a venv

from core.config import (
    DEFAULT_POOL_SPECS,
    ENABLE_ENV_POOLING,
    POOL_BASE_DIR,
    POOL_MAX_SIZE,
)
from core.logging_config import get_logger

logger = get_logger(__name__)


class PreWarmedEnv:
    """Represents a single ready-to-go virtual environment."""

    def __init__(self, spec_name: str, path: Path, python_executable: Path):
        self.spec_name = spec_name
        self.path = path
        self.python_executable = python_executable
        self.created_at = asyncio.get_event_loop().time()


class PoolManager:
    """
    Manages pools of pre-warmed virtual environments to eliminate 'Cold Start' latency.
    """

    _instance: Optional["PoolManager"] = None

    def __init__(self):
        self.base_dir = Path(POOL_BASE_DIR)
        self.pools: dict[str, asyncio.Queue[PreWarmedEnv]] = {
            spec: asyncio.Queue() for spec in DEFAULT_POOL_SPECS
        }
        self.managed_envs: set[Path] = set()
        self.has_gpu = self._detect_gpu()
        self._worker_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._in_progress_replenishments: dict[str, int] = {
            spec: 0 for spec in DEFAULT_POOL_SPECS
        }

    @classmethod
    def get_instance(cls) -> "PoolManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _check_disk_space(self) -> float:
        """Returns free disk space in GB for the drive containing base_dir."""
        try:
            usage = shutil.disk_usage(str(self.base_dir))
            free_gb = usage.free / (1024 ** 3)
            return free_gb
        except Exception:
            return float("inf")

    def _detect_gpu(self) -> bool:
        """Detects if an NVIDIA GPU is available and functional."""
        try:
            # Quick check using nvidia-smi
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"PoolManager: GPU detection skipped/failed: {e}")
            return False

    async def initialize(self):
        """Prepares the pool directory and starts the background worker."""
        if not ENABLE_ENV_POOLING:
            logger.info("PoolManager: Pooling is disabled in config.")
            return

        def _async_cleanup_orchestrator():
            """
            Synchronous cleanup logic moved to a thread.
            Uses a 'rename-then-delete' strategy to make startup near-instant.
            """
            try:
                # 1. Clean up any leftover orphaned cleanup directories from previous runs
                if self.base_dir.parent.exists():
                    for item in self.base_dir.parent.iterdir():
                        if item.is_dir() and item.name.startswith("pools_cleanup_"):
                            try:
                                shutil.rmtree(item)
                            except OSError:
                                # Locked - skip, will retry in background worker
                                pass

                # 2. Clean up everything inside base_dir during startup (since pools are empty)
                if self.base_dir.exists():
                    for item in self.base_dir.iterdir():
                        if item.is_dir():
                            cleanup_path = self.base_dir.parent / f"pools_cleanup_{uuid.uuid4().hex[:8]}"
                            try:
                                item.rename(cleanup_path)
                                shutil.rmtree(cleanup_path)
                            except OSError:
                                # Locked - skip, will retry in background worker
                                pass

                self.base_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"PoolManager: Initial cleanup failed: {e}", exc_info=True)

        # Fire and forget the heavy cleanup in a separate thread
        # so it doesn't block FastMCP lifespan
        import threading

        cleanup_thread = threading.Thread(target=_async_cleanup_orchestrator, daemon=True)
        cleanup_thread.start()

        logger.info(f"PoolManager: Initialized at {self.base_dir} (GPU Detected: {self.has_gpu})")
        # Initialize semaphore to limit concurrent 'uv' calls
        self._uv_semaphore = asyncio.Semaphore(2)
        self._worker_task = asyncio.create_task(self._background_worker())

    async def shutdown(self):
        """Stops the worker and cleans up all environments."""
        if self._worker_task:
            self._worker_task.cancel()

        # Cleanup directories
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir, ignore_errors=True)
        logger.info("PoolManager: Shutdown and cleaned up.")

    async def acquire(self, spec_name: str, timeout: float = 5.0) -> PreWarmedEnv | None:
        """Safely takes an environment from the pool."""
        if not ENABLE_ENV_POOLING:
            return None

        if spec_name not in self.pools:
            logger.warning(f"PoolManager: Requested unknown pool spec: {spec_name}")
            return None

        # Skip GPU pool if no GPU detected, fallback to CPU
        if spec_name == "torch-gpu" and not self.has_gpu:
            logger.debug("PoolManager: No GPU detected, falling back to torch-cpu.")
            spec_name = "torch-cpu"

        try:
            # We use wait_for to avoid hanging forever if the pool is empty
            env = await asyncio.wait_for(self.pools[spec_name].get(), timeout=timeout)
            logger.info(f"PoolManager: Acquired {spec_name} environment: {env.path.name}")
            return env
        except asyncio.TimeoutError:
            logger.warning(
                f"PoolManager: Timeout waiting for {spec_name} pool. Falling back to cold start."
            )
            # Trigger immediate replenishment if pool is empty
            asyncio.create_task(self._prepare_env(spec_name))
            return None

    async def release(self, env: PreWarmedEnv):
        """Discards a used environment."""

        def cleanup():
            if not env.path.exists():
                return
            try:
                shutil.rmtree(env.path)
            except OSError:
                # Locked or disk full - try rename for background cleanup
                try:
                    fallback = self.base_dir.parent / f"pools_cleanup_fail_{uuid.uuid4().hex[:8]}"
                    env.path.rename(fallback)
                except Exception:
                    pass

        async def retry_cleanup_task(attempt: int = 0):
            # Exponential backoff: 2s, 4s, 8s, 16s (max 3 retries)
            delay = min(2 ** (attempt + 1), 16)
            await asyncio.sleep(delay)
            try:
                await asyncio.to_thread(cleanup)
                self.managed_envs.discard(env.path)
                if not env.path.exists():
                    logger.info(f"PoolManager: Delayed cleanup of {env.path.name} succeeded (attempt {attempt + 1})")
                else:
                    # Still locked - retry if we haven't exhausted attempts
                    if attempt < 2:
                        logger.debug(f"PoolManager: Retry {attempt + 1} for {env.path.name}, scheduling next...")
                        asyncio.create_task(retry_cleanup_task(attempt + 1))
                    else:
                        logger.warning(f"PoolManager: Failed to cleanup {env.path.name} after {attempt + 1} attempts")
            except Exception as e:
                logger.debug(f"PoolManager: Retry cleanup error for {env.path.name}: {e}")

        try:
            await asyncio.to_thread(cleanup)
            self.managed_envs.discard(env.path)
            if not env.path.exists():
                logger.debug(f"PoolManager: Released and deleted {env.path.name}")
            else:
                logger.debug(f"PoolManager: Initial cleanup failed for {env.path.name}, scheduling delayed retry...")
                asyncio.create_task(retry_cleanup_task())
        except Exception:
            asyncio.create_task(retry_cleanup_task())

    async def _background_worker(self):
        """Keeps pools filled up to POOL_MAX_SIZE."""
        logger.info("PoolManager: Background worker STARTED.")

        # Initial burst to fill pools on start
        self._trigger_initial_burst()

        while True:
            try:
                if ENABLE_ENV_POOLING:
                    self._check_and_replenish_pools()
                    # Periodically clean up any orphaned cleanup directories
                    def cleanup_orphaned():
                        # 1. Clean old cleanup dirs (with retry on locked files)
                        if self.base_dir.parent.exists():
                            for item in self.base_dir.parent.iterdir():
                                if item.is_dir() and item.name.startswith("pools_cleanup_"):
                                    try:
                                        shutil.rmtree(item)
                                    except OSError:
                                        # Locked - skip, will retry next cycle
                                        pass
                        # 2. Sweep active pools directory for orphaned folders (not in managed_envs)
                        if self.base_dir.exists():
                            for item in self.base_dir.iterdir():
                                if item.is_dir() and item not in self.managed_envs:
                                    try:
                                        cleanup_path = self.base_dir.parent / f"pools_cleanup_{uuid.uuid4().hex[:8]}"
                                        item.rename(cleanup_path)
                                        shutil.rmtree(cleanup_path)
                                    except OSError:
                                        pass
                    await asyncio.to_thread(cleanup_orphaned)
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                logger.info("PoolManager: Background worker cancelled.")
                break
            except Exception as e:
                logger.error(f"PoolManager: Worker error: {e}", exc_info=True)
                await asyncio.sleep(10)

    def _trigger_initial_burst(self):
        from core.config import ENABLE_GPU

        for spec_name in self.pools:
            if spec_name == "torch-gpu" and not ENABLE_GPU:
                continue
            for _ in range(POOL_MAX_SIZE):
                self._in_progress_replenishments[spec_name] = self._in_progress_replenishments.get(spec_name, 0) + 1
                asyncio.create_task(self._prepare_env(spec_name))

    def _check_and_replenish_pools(self):
        from core.config import ENABLE_GPU

        # Skip replenishment if disk space is low
        free_gb = self._check_disk_space()
        if free_gb < MIN_DISK_SPACE_GB:
            logger.debug(f"PoolManager: Skipping replenish - low disk space ({free_gb:.1f}GB)")
            return

        for spec_name, queue in self.pools.items():
            current_size = queue.qsize()
            in_progress = self._in_progress_replenishments.get(spec_name, 0)
            needed = POOL_MAX_SIZE - (current_size + in_progress)
            if needed > 0:
                if spec_name == "torch-gpu" and not ENABLE_GPU:
                    continue
                logger.debug(f"PoolManager: Replenishing {spec_name} (size: {current_size}, in_progress: {in_progress}, needed: {needed})")
                for _ in range(needed):
                    self._in_progress_replenishments[spec_name] = self._in_progress_replenishments.get(spec_name, 0) + 1
                    asyncio.create_task(self._prepare_env(spec_name))

    async def _prepare_env(self, spec_name: str):
        """Creates a new venv and installs dependencies using uv."""
        try:
            # Disk space check before doing anything
            free_gb = self._check_disk_space()
            if free_gb < MIN_DISK_SPACE_GB:
                logger.warning(
                    f"PoolManager: Skipping {spec_name} preparation - "
                    f"only {free_gb:.1f}GB free (minimum: {MIN_DISK_SPACE_GB}GB)"
                )
                return

            async with self._uv_semaphore:
                env_id = str(uuid.uuid4())[:8]
                env_path = self.base_dir / f"{spec_name}_{env_id}"

                # Path to uv.exe (absolute path for reliability on Windows)
                uv_path = r"C:\Users\saiha\.local\bin\uv.exe"
                if not os.path.exists(uv_path):
                    uv_path = "uv"  # fallback

                # Determine python executable path (Windows specific)
                python_exe = (
                    env_path / "Scripts" / "python.exe"
                    if os.name == "nt"
                    else env_path / "bin" / "python"
                )

                logger.info(f"PoolManager: Preparing {spec_name} ({env_id}) using {uv_path}...")

                def run_cmd(cmd):
                    return subprocess.run(
                        cmd, capture_output=True, text=True, shell=True, encoding="utf-8"
                    )

                try:
                    # 1. Create venv (Lightweight via system-site-packages)
                    vcmd = f'"{uv_path}" venv --system-site-packages "{env_path}"'
                    res = await asyncio.to_thread(run_cmd, vcmd)

                    if res.returncode != 0:
                        logger.error(f"PoolManager: uv venv failed: {res.stderr}")
                        raise RuntimeError(f"uv venv failed for {spec_name}")

                    # 2. Install packages (try hardlink first, fallback to copy)
                    packages = DEFAULT_POOL_SPECS.get(spec_name, [])
                    if packages:
                        pkg_str = " ".join(packages)
                        python_exe_str = str(python_exe)

                        # First attempt: hardlink (saves disk space)
                        icmd = (
                            f'"{uv_path}" pip install --link-mode=hardlink '
                            f'--python "{python_exe_str}" {pkg_str}'
                        )
                        res = await asyncio.to_thread(run_cmd, icmd)

                        if res.returncode != 0:
                            # Fallback: copy mode (works when hardlink fails)
                            logger.warning(
                                f"PoolManager: hardlink failed, falling back to copy mode: {res.stderr[:200]}"
                            )
                            icmd = (
                                f'"{uv_path}" pip install --link-mode=copy '
                                f'--python "{python_exe_str}" {pkg_str}'
                            )
                            res = await asyncio.to_thread(run_cmd, icmd)

                        if res.returncode != 0:
                            logger.error(f"PoolManager: uv pip install failed: {res.stderr}")
                            raise RuntimeError(f"uv pip install failed for {spec_name}")

                    # 3. Add to pool
                    new_env = PreWarmedEnv(spec_name, env_path, python_exe)
                    self.managed_envs.add(env_path)
                    await self.pools[spec_name].put(new_env)
                    logger.info(f"PoolManager: {spec_name} ({env_id}) is READY.")

                except Exception as e:
                    logger.error(f"PoolManager: Failed to prepare {spec_name}: {e}", exc_info=True)
                    if env_path.exists():
                        try:
                            shutil.rmtree(env_path)
                        except OSError:
                            # Disk full or locked - try rename for later cleanup
                            try:
                                fallback = self.base_dir.parent / f"pools_cleanup_fail_{env_id}"
                                env_path.rename(fallback)
                            except Exception:
                                pass
        finally:
            self._in_progress_replenishments[spec_name] = max(0, self._in_progress_replenishments.get(spec_name, 0) - 1)

    async def check_health(self) -> dict[str, Any]:
        """Checks if the pooling system is active and pools have environments."""
        if not ENABLE_ENV_POOLING:
            return {"status": "Warning", "message": "Pooling is disabled in config."}

        status_map = {}
        for spec, queue in self.pools.items():
            status_map[spec] = queue.qsize()

        is_healthy = any(q.qsize() > 0 for q in self.pools.values())
        return {
            "status": "Healthy" if is_healthy else "Warning",
            "message": f"Pools active. Current sizes: {status_map}",
            "details": status_map,
        }


# Singleton instance
pool_manager = PoolManager.get_instance()
