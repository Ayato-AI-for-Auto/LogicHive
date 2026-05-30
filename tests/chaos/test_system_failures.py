import asyncio
import pytest
from mcp_server import save_function, get_verification_status

@pytest.mark.asyncio
async def test_syntax_error_rejection(test_db):
    """CHAOS: Verify that immediate syntax errors are rejected with rich detail."""
    bad_code = "def broken_syntax(:" # Missing closing paren and indent
    res = await save_function(name="bad_syntax", code=bad_code, project="chaos")
    assert "IMMEDIATE REJECTION" in res
    assert "Syntax Error" in res

@pytest.mark.asyncio
async def test_timeout_enforcement(test_db):
    """CHAOS: Verify that code with infinite loops is terminated."""
    slow_code = "def infinite():\n    while True: pass"
    test_code = "res = infinite()\nassert res is None"

    # We set a short timeout
    res = await save_function(
        name="slow_func", 
        code=slow_code, 
        test_code=test_code, 
        timeout=1, # 1 second limit
        project="chaos",
        dependencies=[]
    )
    assert "accepted and saved" in res

    # Wait for timeout to trigger in background
    await asyncio.sleep(2.5)

    report = await get_verification_status(name="slow_func", project="chaos")
    # Timeout is considered a system/infrastructure 'ERROR' or 'FAILED'
    report_lower = report.lower()
    assert "error" in report_lower or "failed" in report_lower
    # The detail report should mention timeout (it says 'timed out')
    assert "timed out" in report_lower or "timeout" in report_lower or "terminated" in report_lower

@pytest.mark.asyncio
async def test_sandbox_network_block(test_db):
    """CHAOS: Verify that network access is blocked or fails gracefully in the sandbox."""
    evil_code = "import socket\ndef dial_home(): socket.create_connection(('8.8.8.8', 53))"
    test_code = "res = dial_home()\nassert res is None"

    await save_function(name="evil_func", code=evil_code, test_code=test_code, project="chaos", dependencies=[])
    await asyncio.sleep(1.0)

    status = await get_verification_status(name="evil_func", project="chaos")
    # In restricted environments, this will result in FAILED (exec error) or ERROR
    assert "FAILED" in status or "ERROR" in status
    # Check for some indication of network failure or denylist
    assert any(k in status.lower() for k in ["denied", "failure", "timeout", "offline", "unreachable", "error"])

@pytest.mark.asyncio
async def test_quality_theater_rejection(test_db):
    """CHAOS: Verify that 'pass' methods or trivial code are rejected by AI Auditor."""
    # We trigger the fake auditor's theater check via keywords
    theater_code = "def do_nothing():\n    pass # pass keyword triggers fake"
    test_code = "do_nothing()"
    
    await save_function(
        name="theater_func", 
        code=theater_code, 
        test_code=test_code, 
        description="Just a pass method", 
        project="chaos"
    )
    await asyncio.sleep(0.5)
    
    status = await get_verification_status(name="theater_func", project="chaos")
    # In fake intel, 'pass' triggers low score
    assert "FAILED" in status or "DRAFT" in status or "Quality Gate" in status
