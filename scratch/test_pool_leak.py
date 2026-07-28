import asyncio
import os
import shutil
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from core.execution.pool import pool_manager
import core.config


async def run_functional_test():
    print("=== Starting Pool Manager Functional Test ===")

    # 1. Force enable pooling and setup environment
    core.config.ENABLE_ENV_POOLING = True
    core.config.POOL_MAX_SIZE = 1  # Keep it small for test

    # Target directory resolution
    pool_base = Path(core.config.POOL_BASE_DIR)
    parent_dir = pool_base.parent
    print(f"Pool base directory: {pool_base}")
    print(f"Parent directory: {parent_dir}")

    # Clean up parent cleanup directories first to start fresh
    if parent_dir.exists():
        for item in parent_dir.iterdir():
            if item.is_dir() and item.name.startswith("pools_cleanup_"):
                shutil.rmtree(item, ignore_errors=True)

    # 2. Initialize Pool Manager
    print("\n[Step 1] Initializing pool manager...")
    await pool_manager.initialize()

    # Wait dynamically for the pool to be filled (up to 90 seconds)
    print("Waiting for initial environment to be prepared (installing packages)...")
    for i in range(90):
        await asyncio.sleep(1)
        sizes = [q.qsize() for q in pool_manager.pools.values()]
        if any(size > 0 for size in sizes):
            print(f"Pool prepared successfully after {i + 1} seconds!")
            break
    else:
        print("Timeout waiting for initial pool replenishment.")

    print(f"Active pool sizes: {[q.qsize() for q in pool_manager.pools.values()]}")

    # 3. Test Acquire and Release
    print("\n[Step 2] Testing normal acquire and release...")
    env = await pool_manager.acquire("torch-cpu")
    if env:
        print(f"Successfully acquired: {env.path}")
        print(f"Path exists before release: {env.path.exists()}")
        await pool_manager.release(env)
        print(f"Path exists after release: {env.path.exists()}")
    else:
        print("Failed to acquire env.")

    # 4. Wait for replenishment again so we can test the fallback
    print("\nWaiting for pool to replenish after release...")
    for i in range(90):
        await asyncio.sleep(1)
        sizes = [q.qsize() for q in pool_manager.pools.values()]
        if any(size > 0 for size in sizes):
            print(f"Pool replenished successfully after {i + 1} seconds!")
            break

    # 5. Test Deletion Failure / Windows Lock Fallback
    print("\n[Step 3] Testing locked environment fallback...")
    # Acquire a new env
    env = await pool_manager.acquire("torch-cpu")
    if env:
        print(f"Acquired: {env.path}")
        # Lock the folder by opening a file in it
        dummy_file = env.path / "locked_file.txt"
        dummy_file.write_text("lock me")

        # Simulate locking by opening and keeping it open
        with open(dummy_file, "r") as lock_handle:
            # Try to release. On Windows, shutil.rmtree will fail because the file is open.
            print("Releasing env while file handle is open (simulating lock)...")
            await pool_manager.release(env)

        print(f"Env path exists immediately after locked release: {env.path.exists()}")
        print("Sleeping 7 seconds to let delayed cleanup background task execute...")
        await asyncio.sleep(7)
        print(f"Env path exists after delayed retry: {env.path.exists()}")

        # Check if any renamed pools_cleanup_fail_* directory was created
        cleanup_dirs = [
            p
            for p in parent_dir.iterdir()
            if p.is_dir() and p.name.startswith("pools_cleanup_fail_")
        ]
        print(f"Orphaned/Renamed cleanup directories found: {[p.name for p in cleanup_dirs]}")
    else:
        print("Failed to acquire second env")

    # Clean up background tasks
    print("\n[Step 4] Shutting down pool manager...")
    await pool_manager.shutdown()
    print("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(run_functional_test())
