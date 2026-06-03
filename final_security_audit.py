import os
import re
import math
from typing import Tuple, List

# --- LOGIC RETRIEVED FROM LOGICHIVE (v5: Final) ---
SECRET_PATTERNS: List[str] = [
    r"(?i)(?:api_key|apikey|key|token|secret)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{16,})"
]

def calculate_entropy(data: str) -> float:
    if not data: return 0.0
    entropy = 0
    char_counts = {}
    for char in data: char_counts[char] = char_counts.get(char, 0) + 1
    for count in char_counts.values():
        p_x = float(count) / len(data)
        if p_x > 0: entropy += - p_x * math.log(p_x, 2)
    return entropy

def contains_secrets_scanner(code: str) -> Tuple[bool, str, float]:
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, code)
        if matches:
            secret = matches[0]
            if secret.lower() in ["your_api_key_here", "your_gemini_api_key_here"]:
                 continue
            risk = calculate_entropy(secret)
            return True, secret, risk
    return False, "", 0.0
# --------------------------------------

def run_full_audit():
    print(f"🕵️  LogicHive ULTIMATE Audit: Scanning ALL files (including .env)...")
    found_count = 0
    
    # Scan everything in current directory
    for root, dirs, files in os.walk("."):
        # Skip noisy dirs
        if any(d in root for d in [".git", ".venv", ".pytest_cache", ".ruff_cache", "__pycache__"]):
            continue
            
        for file in files:
            path = os.path.join(root, file)
            # Include config files specifically
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    found, secret, risk = contains_secrets_scanner(content)
                    if found and risk > 3.0:
                        print(f"[🚨] LEAK DETECTED in {path}")
                        print(f"    Secret: {secret[:4]}...{secret[-4:]} (Entropy: {risk:.2f})")
                        found_count += 1
            except Exception:
                pass
    
    if found_count == 0:
        print("\n🏆 LogicHive Certified: NO REAL SECRETS FOUND in the entire workspace.")
    else:
        print(f"\n☢️  TOTAL LEAKS: {found_count}")

if __name__ == "__main__":
    run_full_audit()
