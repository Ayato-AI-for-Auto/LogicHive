import re
from typing import Tuple, List

# 本番と同じロジック
SECRET_PATTERNS: List[str] = [
    r"(?i)(?:api_key|apikey|key|token|secret)['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9_-]{16,})['\"]"
]

def contains_secrets_scanner_v2(code: str) -> Tuple[bool, str]:
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, code)
        if matches:
            return True, matches[0]
    return False, ""

# テスト
is_found, secret = contains_secrets_scanner_v2('api_key = "AIzaSyAxjKoHJoZRuVV9e_WcI6FGV5wIIPdu0v8"')
assert is_found is True
print("OK")
