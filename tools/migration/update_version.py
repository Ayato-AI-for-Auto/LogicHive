import re
import sys
from pathlib import Path


def update_version(version):
    # 1. Update pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        new_content = re.sub(r'version = "[^"]+"', f'version = "{version}"', content, count=1)
        pyproject_path.write_text(new_content, encoding="utf-8")
        print(f"Updated pyproject.toml to {version}")

    # 2. Update src/core/__init__.py
    init_path = Path("src/core/__init__.py")
    if init_path.exists():
        content = init_path.read_text(encoding="utf-8")
        if "__version__" in content:
            new_content = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{version}"', content)
        else:
            new_content = content + f'\n__version__ = "{version}"\n'
        init_path.write_text(new_content, encoding="utf-8")
        print(f"Updated src/core/__init__.py to {version}")
    else:
        init_path.parent.mkdir(parents=True, exist_ok=True)
        init_path.write_text(f'__version__ = "{version}"\n', encoding="utf-8")
        print(f"Created src/core/__init__.py with version {version}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_version.py <version>")
        sys.exit(1)
    update_version(sys.argv[1])
