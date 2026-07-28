import asyncio
import os
import sqlite3
from unittest.mock import patch

import pytest

from orchestrator import do_get_verification_status, do_save_async, do_search_async


@pytest.mark.asyncio
async def test_system_multi_language_flow(test_db):
    """
    System E2E test verifying the lifecycle of different language assets:
    1. JavaScript asset compiles, runs successfully, is verified, and saved to SQLite.
    2. HTML asset has syntax validation error, fails verification, and gets score penalty in DB.
    3. PHP asset is saved, but because PHP CLI is missing, gets verified with score 0.0 and saved.
    4. Performs direct SQLite db inspection (裏取り) to verify recorded states.
    5. Performs hybrid search and verifies RAG priority results.
    """
    project = "multi_lang_proj"

    with patch("core.execution.php.EphemeralPhpExecutor._is_php_available", return_value=False):
        # ==========================================
        # 1. JavaScript E2E (Succeeds)
        # ==========================================
        js_name = "js_multiplier"
        js_code = "module.exports = { multiply: (a, b) => a * b };"
        js_test = "assert.strictEqual(solution.multiply(4, 5), 20);"

        saved_js = await do_save_async(
            name=js_name,
            code=js_code,
            description="multiplies two numbers in javascript",
            test_code=js_test,
            project=project,
            language="javascript",
        )
        assert saved_js is True

        # Wait for JS verification
        for _ in range(30):
            status_js = await do_get_verification_status(js_name, project=project)
            if status_js["status"] != "pending":
                break
            await asyncio.sleep(0.1)

        assert status_js["status"] == "verified"

        # ==========================================
        # 2. HTML E2E (Fails Tag Nesting Validation)
        # ==========================================
        html_name = "html_bad_snippet"
        html_code = "<div><p>unclosed tags"

        saved_html = await do_save_async(
            name=html_name,
            code=html_code,
            description="bad html page",
            test_code="",
            project=project,
            language="html",
        )
        assert saved_html is True

        for _ in range(30):
            status_html = await do_get_verification_status(html_name, project=project)
            if status_html["status"] != "pending":
                break
            await asyncio.sleep(0.1)

        assert status_html["status"] == "failed"

        # ==========================================
        # 3. PHP E2E (Fails due to missing runtime)
        # ==========================================
        php_name = "php_helper"
        php_code = "function add($a, $b) { return $a + $b; }"
        php_test = "assert(add(2, 2) === 4);"

        saved_php = await do_save_async(
            name=php_name,
            code=php_code,
            description="adds numbers in PHP",
            test_code=php_test,
            project=project,
            language="php",
        )
        assert saved_php is True

        for _ in range(30):
            status_php = await do_get_verification_status(php_name, project=project)
            if status_php["status"] != "pending":
                break
            await asyncio.sleep(0.1)

        # Verification should fail because PHP is not on PATH (returns 0.0 score)
        assert status_php["status"] == "failed"

        # ==========================================
        # 4. Direct SQLite DB Verification (裏取り)
        # ==========================================
        db_path = os.environ["SQLITE_DB_PATH"]
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query JS record
        cursor.execute(
            "SELECT * FROM logichive_functions WHERE name = ? AND project = ?", (js_name, project)
        )
        js_row = cursor.fetchone()
        assert js_row is not None
        assert js_row["verification_status"] == "verified"
        assert js_row["reliability_score"] > 80.0
        assert js_row["language"] == "javascript"

        # Query HTML record
        cursor.execute(
            "SELECT * FROM logichive_functions WHERE name = ? AND project = ?", (html_name, project)
        )
        html_row = cursor.fetchone()
        assert html_row is not None
        assert html_row["verification_status"] == "failed"
        assert html_row["reliability_score"] == 0.0  # Vetoed due to nesting error

        # Query PHP record
        cursor.execute(
            "SELECT * FROM logichive_functions WHERE name = ? AND project = ?", (php_name, project)
        )
        php_row = cursor.fetchone()
        assert php_row is not None
        assert php_row["verification_status"] == "failed"
        assert "php cli is not installed" in php_row["verification_report"].lower()

        conn.close()

        # ==========================================
        # 5. Hybrid RAG Search Sorting
        # ==========================================
        # Search for "multiplies", should return js_multiplier first
        search_res = await do_search_async(query="multiplies", project=project, limit=5)
        assert len(search_res) >= 1
        assert search_res[0]["name"] == js_name
