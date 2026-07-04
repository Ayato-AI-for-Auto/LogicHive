import os
import re
import math
from typing import Tuple, List

# --- LOGIC RETRIEVED FROM LOGICHIVE ---
SECRET_PATTERNS: List[str] = [
    r"(?i)(?:api_key|apikey|key|token|secret)['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9_-]{16,})['\"]"
]

def calculate_entropy(data: str) -> float:
    if not data:
        return 0.0
    entropy = 0
    char_counts = {}
    for char in data:
        char_counts[char] = char_counts.get(char, 0) + 1
    for count in char_counts.values():
        p_x = float(count) / len(data)
        if p_x > 0:
            entropy += - p_x * math.log(p_x, 2)
    return entropy

def contains_secrets_scanner(code: str) -> Tuple[bool, str, float]:
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, code)
        if matches:
            secret = matches[0]
            risk = calculate_entropy(secret)
            return True, secret, risk
    return False, "", 0.0
# --------------------------------------

def run_dogfood_scan(directory: str):
    print(f"🚀 LogicHive Dogfooding: Scanning '{directory}' for secrets...")
    found_count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".py", ".md", ".json", ".bat")):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        found, secret, risk = contains_secrets_scanner(content)
                        if found and risk > 3.0: # Filter for high-risk only
                            print(f"[!] DANGER: High-risk secret found in {path}")
                            print(f"    Secret: {secret[:4]}...{secret[-4:]} (Entropy: {risk:.2f})")
                            found_count += 1
                except Exception:
                    pass

    if found_count == 0:
        print("✅ Scan complete: No high-risk secrets found in source files.")
    else:
        print(f"❌ Scan complete: Found {found_count} potential security risks.")

if __name__ == "__main__":
    # Scan src and tools
    run_dogfood_scan("src")
    run_dogfood_scan("tools")
    # Explicitly exclude .env and .gitignore from this specific scan to avoid noise
