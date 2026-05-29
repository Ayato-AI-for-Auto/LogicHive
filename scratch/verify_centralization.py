import os
from pathlib import Path
from core.config import DATA_DIR, SQLITE_DB_PATH, FAISS_INDEX_PATH, POOL_BASE_DIR

print(f"DATA_DIR: {DATA_DIR}")
print(f"SQLITE_DB_PATH: {SQLITE_DB_PATH}")
print(f"FAISS_INDEX_PATH: {FAISS_INDEX_PATH}")
print(f"POOL_BASE_DIR: {POOL_BASE_DIR}")

expected_home = Path.home() / ".logichive"
expected_data = expected_home / "data"
expected_pools = expected_home / "pools"

assert str(DATA_DIR) == str(expected_data)
assert str(POOL_BASE_DIR) == str(expected_pools)
assert ".logichive" in str(SQLITE_DB_PATH)

print("\nSUCCESS: All paths are centralized in ~/.logichive")
