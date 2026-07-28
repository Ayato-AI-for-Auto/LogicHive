import glob
import os
import shutil


def cleanup_pools():
    target_dirs = glob.glob("storage/data/pools*")
    for p in target_dirs:
        print(f"Cleaning up {p}...")
        shutil.rmtree(p, ignore_errors=True)
        if os.path.exists(p):
            print(f"Warning: Could not fully delete {p}")
        else:
            print(f"Successfully deleted {p}")


if __name__ == "__main__":
    cleanup_pools()
