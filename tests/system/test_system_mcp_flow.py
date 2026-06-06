import asyncio

import pytest

from mcp_server import (
    delete_function,
    get_function,
    get_verification_status,
    save_function,
    search_functions,
)


@pytest.mark.asyncio
async def test_system_end_to_end_flow(test_db):
    """SYSTEM: End-to-end user flow across all MCP tools."""
    name = "system_e2e_func"
    code = "def parse_data(data):\n    return data.upper()"
    test_code = "res = parse_data('hello')\nassert res == 'HELLO'"

    # 1. Search (should be empty initially)
    search_res = await search_functions(query="parse_data")
    assert "No matching functions found" in search_res or name not in search_res

    # 2. Save
    save_msg = await save_function(
        name=name,
        code=code,
        description="Parses data to uppercase",
        tags=["parser", "string"],
        test_code=test_code,
        project="sys_test",
    )
    assert "accepted and saved" in save_msg
    assert "Verification is running" in save_msg

    # 3. Wait for verification (Polling)
    max_retries = 10
    verified = False
    status_msg = ""
    for _ in range(max_retries):
        status_msg = await get_verification_status(name=name, project="sys_test")
        if "VERIFIED" in status_msg:
            verified = True
            break
        await asyncio.sleep(1.0)

    assert verified is True, f"Verification timed out or failed. Last status: {status_msg}"

    # 5. Search again (should find it)
    search_res2 = await search_functions(query="parse", project="sys_test")
    assert name in search_res2

    # 6. Retrieve code
    get_res = await get_function(name=name, project="sys_test")
    assert code in get_res
    assert "**Tags:** parser, string" in get_res

    # 7. Check System Integrity Tool
    # Add a small delay to ensure all DB operations (including vector sync) are fully committed
    await asyncio.sleep(0.5)
    from mcp_server import check_integrity
    integrity_res = await check_integrity()
    assert "LogicHive Integrity Report" in integrity_res
    assert "✅ Connected" in integrity_res or "✅ Found on disk" in integrity_res

    # 8. Delete
    del_res = await delete_function(name=name, project="sys_test")
    assert "Successfully deleted" in del_res

    # 8. Verify deletion
    get_res_deleted = await get_function(name=name, project="sys_test")
    assert "not found" in get_res_deleted
