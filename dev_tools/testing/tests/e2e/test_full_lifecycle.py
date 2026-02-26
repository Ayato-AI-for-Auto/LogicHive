import os
import sys
import time

# Setup paths
# Current file: c:\Users\saiha\My_Service\programing\MCP\function_store_mcp\dev_tools\tests\e2e\test_full_lifecycle.py
# Project root: c:\Users\saiha\My_Service\programing\MCP\function_store_mcp
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
backend_path = os.path.join(project_root, "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

from hub.orchestrator import (  # noqa: E402
    do_delete_impl,
    do_save_impl,
    do_search_impl,
)


def test_full_save_search_delete_lifecycle():
    ts = int(time.time() * 1000)
    name = f"e2e_lifecycle_{ts}"
    code = f'def {name}():\n    """This is an E2E test function."""\n    return \'life cycle\''

    # 1. Save
    print(f"Step 1: Saving {name}")
    save_res = do_save_impl(
        asset_name=name, code=code, description="E2E Lifecycle Test"
    )
    assert "SUCCESS" in save_res

    # 2. Search
    print("Step 2: Searching (polling for background embedding)")
    found = False
    for _ in range(120):  # Max 60 seconds
        search_res = do_search_impl("E2E Lifecycle Test")
        if any(r["name"] == name for r in search_res):
            found = True
            break
        time.sleep(0.5)
    assert found, f"Function {name} not found in search results after save"

    # 3. Delete
    print("Step 3: Deleting")
    del_res = do_delete_impl(name)
    assert "SUCCESS" in del_res

    # 6. Final Search (Should be gone)
    print("Step 6: Final availability check")
    final_search = do_search_impl(name)
    # Filter for exact match just in case of similar names
    exact_match = [r for r in final_search if r["name"] == name]
    assert len(exact_match) == 0
