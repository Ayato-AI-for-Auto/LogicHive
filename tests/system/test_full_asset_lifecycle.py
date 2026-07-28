import asyncio

import pytest

from orchestrator import do_get_async, do_get_verification_status, do_save_async, do_search_async


@pytest.mark.asyncio
async def test_full_asset_lifecycle(test_db):
    """
    SYSTEM: Verify the entire lifecycle of an asset.
    Save -> Verify (Background) -> Search -> Get.
    """
    name = "lifecycle_test_func"
    project = "e2e_system"
    code = "def lifecycle_test_func(a, b): return a + b"
    test_code = "assert lifecycle_test_func(1, 2) == 3"
    description = "A function to test the system lifecycle."

    # 1. Save Asset
    success = await do_save_async(
        name=name,
        code=code,
        description=description,
        test_code=test_code,
        project=project,
        language="python",
    )
    assert success is True

    # 2. Wait for background verification (Mock intelligence is fast)
    # We poll the status
    max_retries = 10
    verified = False
    for _ in range(max_retries):
        status_res = await do_get_verification_status(name, project=project)
        if status_res["status"] == "verified":
            verified = True
            break
        await asyncio.sleep(0.5)

    assert verified is True, f"Verification failed or timed out. Status: {status_res['status']}"

    # 3. Search for the asset
    search_results = await do_search_async(query="system lifecycle test", project=project)
    assert len(search_results) > 0
    assert search_results[0]["name"] == name

    # 4. Get the full asset
    final_asset = await do_get_async(name, project=project)
    assert final_asset is not None
    assert final_asset["code"] == code
    assert final_asset["reliability_score"] > 0
    assert final_asset["embedding"] is not None


@pytest.mark.asyncio
async def test_system_rejection_flow(test_db):
    """
    SYSTEM: Verify that a bad asset (no assertions) is rejected but still stored as 'failed'.
    """
    name = "bad_func"
    project = "e2e_system"
    code = "def bad_func(): pass"
    test_code = ""  # No assertions -> Immediate rejection in real life, but here it's caught in pre-check or facts gate

    # Verification will fail because no test_code is provided
    # However, do_save_async returns success because the 'request' is accepted for processing
    # BUT if test_code is empty, it might fail pre-check.

    success = await do_save_async(name=name, code=code, test_code=test_code, project=project)
    assert success is True

    # Poll for failure
    for _ in range(10):
        status_res = await do_get_verification_status(name, project=project)
        if status_res["status"] in ["failed", "error"]:
            break
        await asyncio.sleep(0.5)

    assert status_res["status"] in ["failed", "error"]

    # Search should NOT return failed assets (depending on search implementation)
    # Usually, search filters for verified=True or score > threshold
    search_results = await do_search_async(query="bad func", project=project)
    # If search filters verified only:
    names = [r["name"] for r in search_results]
    assert name not in names
