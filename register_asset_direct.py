import asyncio
import json
import uuid
import os
import sys
# Ensure src is in path for imports
sys.path.append(os.path.abspath("src"))

from storage.sqlite_api import SqliteStorage

async def register():
    storage = SqliteStorage()
    
    function_data = {
        "name": "contains_secrets_scanner",
        "project": "default",
        "code": """import re
from typing import Tuple, List

# Example patterns for scanning
SECRET_PATTERNS: List[str] = [
    r"(?i)(?:api_key|apikey|key|token|secret)['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9_-]{16,})['\"]"
]

def contains_secrets_scanner(code: str) -> Tuple[bool, str]:
    \"\"\"
    Scans code for potential API keys or secrets using regex.
    Returns (True, secret) if found, (False, "") otherwise.
    \"\"\"
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, code)
        if matches:
            return True, matches[0]
    return False, ""
""",
        "description": "Security utility to identify potential API keys or secrets embedded in source code using regex patterns.",
        "language": "python",
        "tags": ["security", "secrets-detection", "regex"],
        "reliability_score": 1.0,
        "dependencies": ["re", "typing"],
        "test_code": """
def test_contains_secrets_scanner():
    is_found, secret = contains_secrets_scanner("print('hello')")
    assert is_found is False
    assert secret == ""
    code_with_secret = 'api_key = "AIzaSyAxjKoHJoZRuVV9e_WcI6FGV5wIIPdu0v8"'
    is_found, secret = contains_secrets_scanner(code_with_secret)
    assert is_found is True
    assert secret == "AIzaSyAxjKoHJoZRuVV9e_WcI6FGV5wIIPdu0v8"
test_contains_secrets_scanner()
"""
    }
    
    success = await storage.upsert_function(function_data)
    if success:
        print("Successfully registered asset directly to DB.")
    else:
        print("Failed to register asset.")

if __name__ == "__main__":
    asyncio.run(register())
