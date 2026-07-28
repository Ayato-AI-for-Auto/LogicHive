import re
from typing import Tuple

SECRET_PATTERNS = [r"AIza[0-9A-Za-z-_]{35}"]


def _contains_secrets(code: str) -> Tuple[bool, str]:
    """Scans code for potential API keys or secrets using regex."""
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, code)
        if matches:
            return True, matches[0]
    return False, ""
