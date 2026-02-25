import sys
from pathlib import Path

# Add backend to path to allow importing core
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root / "backend"))

from core.setup import generate_config

def main():
    generate_config(is_frozen=False)

if __name__ == "__main__":
    main()
