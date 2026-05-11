import asyncio

import pytest

from orchestrator import do_get_verification_status, do_save_async, do_search_async


@pytest.mark.asyncio
async def test_full_agent_workflow(test_db):
    """
    System Test: Simulates a complete user flow:
    1. Register a valid function.
    2. Wait for verification.
    3. Search for it semantically.
    """
    name = "prime_checker"
    code = """
def is_prime(n):
    if n <= 1: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True
"""
    test_code = "assert is_prime(7) is True; assert is_prime(4) is False"
    description = "Checks if a number is prime using trial division."

    # 1. Register
    await do_save_async(
        name=name, code=code, description=description, test_code=test_code, tags=["math", "primes"]
    )

    # 2. Polling for verification
    verified = False
    for _ in range(10):
        await asyncio.sleep(1)
        status = await do_get_verification_status(name)
        if status["status"] == "verified":
            verified = True
            break

    assert verified is True, f"Verification failed or timed out: {status}"

    # 3. Semantic Search
    # Note: Search depends on the vector store being updated in the background task.
    # We might need a small wait for the FAISS index to catch up.
    await asyncio.sleep(0.5)

    results = await do_search_async(query="How to check if a number is prime?", limit=1)

    assert len(results) > 0
    assert results[0]["name"] == name
    print(f"\n[SYSTEM TEST] Agent workflow completed successfully. Found: {results[0]['name']}")
