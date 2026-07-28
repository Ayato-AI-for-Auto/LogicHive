import asyncio
import os
from dotenv import load_dotenv

# Load config
load_dotenv("C:/Users/saiha/.logichive/.env")
load_dotenv(".env", override=True)  # Project root .env

# Force model override for this test
os.environ["GEMINI_MODEL"] = "models/gemma-4-31b-it"

print(f"DEBUG: GEMINI_MODEL='{os.getenv('GEMINI_MODEL')}'")
print(f"DEBUG: GEMINI_API_KEY={'set' if os.getenv('GEMINI_API_KEY') else 'not set'}")
print(f"DEBUG: GOOGLE_API_KEY={'set' if os.getenv('GOOGLE_API_KEY') else 'not set'}")

from core.evaluation.manager import EvaluationManager


async def run():
    mgr = EvaluationManager()
    code = """
import hashlib

def calculate_code_hash_v5(code: str) -> str:
    \"\"\"
    Calculates a SHA-256 hash for the given source code.
    Normalization: Basic whitespace stripping to avoid trivial mismatches.
    \"\"\"
    # Normalize: strip leading/trailing whitespace and ensure consistent line endings
    normalized_code = code.strip().replace("\\r\\n", "\\n")

    # Generate SHA-256 hash
    return hashlib.sha256(normalized_code.encode("utf-8")).hexdigest()
"""
    test_code = """
def test():
    res = calculate_code_hash_v5("test")
    assert isinstance(res, str)
    assert len(res) == 64
    assert calculate_code_hash_v5(" a ") == calculate_code_hash_v5("a")

test()
"""
    result = await mgr.evaluate_all(
        code, "python", name="calculate_code_hash_v5", test_code=test_code
    )
    print("--- EVALUATION RESULT ---")
    print(result)


if __name__ == "__main__":
    asyncio.run(run())
