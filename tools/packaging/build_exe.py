import os
import shutil
import subprocess
from pathlib import Path


def build():
    # Correctly identify project root (three levels up from tools/packaging/build_exe.py)
    project_root = Path(__file__).parent.parent.parent.resolve()
    os.chdir(project_root)

    print(f"Building LogicHive.exe in {project_root}...")

    # Clean old builds
    for folder in ["build", "dist", "release"]:
        if os.path.exists(folder):
            print(f"Cleaning {folder}...")
            shutil.rmtree(folder, ignore_errors=True)

    # Run PyInstaller
    try:
        spec_path = Path("tools/packaging/LogicHive.spec")
        if not spec_path.exists():
            print(f"[ERROR] Spec file not found at {spec_path}")
            return

        # Run PyInstaller using the spec file
        # Use sys.executable to ensure we use the same python environment
        import sys
        subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec_path)], check=True)
        print("\n[SUCCESS] Build complete! You can find the executable in the 'dist' folder.")

        # Move to a 'release' folder for distribution if needed
        # (For now, let's just keep it in dist/ for simplicity as per MVP)

    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed: {e}")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")


if __name__ == "__main__":
    build()
