import os
import re
import math
import concurrent.futures
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
            if secret.lower() in ["your_api_key_here", "your_gemini_api_key_here", "your_github_token", "your_personal_access_token"]:
                 continue
            risk = calculate_entropy(secret)
            return True, secret, risk
    return False, "", 0.0
# --------------------------------------

# Fast-path: Exclude binary and large files
EXCLUDED_EXTS = {".exe", ".dll", ".so", ".pyc", ".pyd", ".png", ".jpg", ".pdf", ".zip", ".tar"}
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB limit

def scan_file(path: str) -> Tuple[str, bool, str, float]:
    """Scans a single file and returns the result."""
    try:
        # Fast path size check
        if os.path.getsize(path) > MAX_FILE_SIZE:
            return path, False, "", 0.0
            
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            found, secret, risk = contains_secrets_scanner(content)
            return path, found, secret, risk
    except Exception:
        return path, False, "", 0.0

def run_full_audit():
    print(f"🕵️  LogicHive ULTIMATE Audit: Scanning workspace (Concurrent Fast-path)...")
    found_count = 0
    target_files = []
    
    # 1. Collect target files
    EXCLUDED_DIRS = {".git", ".venv", "storage", "build", "dist", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules"}
    for root, dirs, files in os.walk("."):
        # Modify dirs in-place to prevent os.walk from descending into excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            
        for file in files:
            # Fast path extension check
            if any(file.endswith(ext) for ext in EXCLUDED_EXTS):
                continue
            target_files.append(os.path.join(root, file))
            
    print(f"📄 Found {len(target_files)} relevant files to scan.")
    
    # 2. Concurrent scanning
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(scan_file, path): path for path in target_files}
        for future in concurrent.futures.as_completed(futures):
            path, found, secret, risk = future.result()
            if found and risk > 3.0:
                print(f"[🚨] LEAK DETECTED in {path}")
                print(f"    Secret: {secret[:4]}...{secret[-4:]} (Entropy: {risk:.2f})")
                found_count += 1
    
    if found_count == 0:
        print("\n🏆 LogicHive Certified: NO REAL SECRETS FOUND in the workspace.")
    else:
        print(f"\n☢️  TOTAL LEAKS: {found_count}")

if __name__ == "__main__":
    run_full_audit()
