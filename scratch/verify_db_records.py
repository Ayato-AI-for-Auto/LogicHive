import asyncio
import os
import sqlite3
import tempfile
from pathlib import Path

# Set PYTHONPATH and setup environment for the local imports
import sys
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Setup temporary database path for validation
temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
temp_db_path = temp_db.name
temp_db.close()
os.environ["SQLITE_DB_PATH"] = temp_db_path

from core.db import get_db_connection, close_db_connection
from orchestrator import do_save_async, do_get_verification_status

async def main():
    print("=============================================================")
    print("LogicHive DB Record Verification & Fallback Inspection Script")
    print("=============================================================")
    print(f"Database target: {temp_db_path}")

    # Let the DB manager initialize the database connection and schema
    conn = await get_db_connection()

    project = "verify_test_project"

    # Test cases:
    # 1. Javascript (Expected to succeed using Node.js)
    print("\n1. Registering Javascript multiplier...")
    js_saved = await do_save_async(
        name="js_mult",
        code="module.exports = { multiply: (a, b) => a * b };",
        description="Multiplies numbers",
        test_code="assert.strictEqual(solution.multiply(2, 3), 6);",
        project=project,
        language="javascript"
    )
    print(f"JS Save Status: {js_saved}")

    # 2. HTML with nesting/unclosed tags (Expected to fail HTML static parser validation with score 0.0)
    print("\n2. Registering HTML with unclosed tags...")
    html_saved = await do_save_async(
        name="html_unclosed",
        code="<div class='main'><p>Missing end tags",
        description="Broken layout",
        test_code="",
        project=project,
        language="html"
    )
    print(f"HTML Save Status: {html_saved}")

    # 3. PHP with missing host runtime (Expected to return failed status and score 0.0 with fallback warning logs)
    print("\n3. Registering PHP with missing runtime...")
    php_saved = await do_save_async(
        name="php_add",
        code="function add($a, $b) { return $a + $b; }",
        description="Adds numbers in PHP",
        test_code="assert(add(2, 3) === 5);",
        project=project,
        language="php"
    )
    print(f"PHP Save Status: {php_saved}")

    # Wait for verification pipeline to complete
    print("\nWaiting for verification pipeline to finish...")
    for _ in range(50):
        await asyncio.sleep(0.1)
        # Check if any are still pending
        check_conn = sqlite3.connect(temp_db_path)
        cursor = check_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logichive_functions WHERE verification_status = 'pending'")
        pending_count = cursor.fetchone()[0]
        check_conn.close()
        if pending_count == 0:
            break

    # Direct DB Inspection (裏取り)
    print("\n================ Direct SQLite Table Content ================")
    check_conn = sqlite3.connect(temp_db_path)
    check_conn.row_factory = sqlite3.Row
    cursor = check_conn.cursor()
    cursor.execute("SELECT name, language, verification_status, reliability_score, verification_report FROM logichive_functions")
    rows = cursor.fetchall()

    for row in rows:
        print(f"\n[Asset: {row['name']} | Language: {row['language']}]")
        print(f"  - Verification Status: {row['verification_status']}")
        print(f"  - Reliability Score  : {row['reliability_score']}")
        print(f"  - Report / Log Excerpt:")
        report_text = row['verification_report'] or ""
        print(f"    {report_text[:200]}...")
    
    check_conn.close()

    # Clean up DB connection and file
    await close_db_connection()
    try:
        os.remove(temp_db_path)
    except OSError:
        pass

if __name__ == "__main__":
    asyncio.run(main())
