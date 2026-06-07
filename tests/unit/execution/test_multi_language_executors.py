import pytest

from core.execution.base import ExecutionStatus
from core.execution.c import EphemeralCExecutor
from core.execution.html import EphemeralHtmlExecutor
from core.execution.java import EphemeralJavaExecutor
from core.execution.javascript import EphemeralJavaScriptExecutor
from core.execution.php import EphemeralPhpExecutor


@pytest.mark.asyncio
async def test_javascript_executor():
    executor = EphemeralJavaScriptExecutor()
    # Simple JS execution
    code = "module.exports = { add: (a, b) => a + b };"
    test_code = "assert.strictEqual(solution.add(2, 3), 5);"
    result = await executor.execute(code, test_code=test_code, language="javascript")

    assert result.status == ExecutionStatus.SUCCESS
    assert len(result.results) > 0
    assert "passed" in result.results[0].data.lower()


@pytest.mark.asyncio
async def test_typescript_executor():
    executor = EphemeralJavaScriptExecutor()
    # Node 22 supports --experimental-strip-types
    code = "export function multiply(a: number, b: number): number { return a * b; }"
    test_code = "assert.strictEqual(solution.multiply(3, 4), 12);"
    result = await executor.execute(code, test_code=test_code, language="typescript")

    assert result.status == ExecutionStatus.SUCCESS
    assert len(result.results) > 0


@pytest.mark.asyncio
async def test_java_executor():
    executor = EphemeralJavaExecutor()

    # We define helper method inside Harness class
    code = "public static int add(int a, int b) { return a + b; }"
    test_code = "if (add(5, 5) != 10) throw new AssertionError(\"add failed\");"

    result = await executor.execute(code, test_code=test_code)

    # If Java is not installed, result will be FAILURE stating JDK missing, which is a success fallback
    # Otherwise it succeeds.
    if result.status == ExecutionStatus.FAILURE:
        assert "jdk" in result.logs.stderr.lower() or "javac" in result.logs.stderr.lower()
    else:
        assert result.status == ExecutionStatus.SUCCESS
        assert len(result.results) > 0


@pytest.mark.asyncio
async def test_php_executor_missing():
    executor = EphemeralPhpExecutor()
    # Verify php executor handles lack of php gracefully
    code = "function test() { return 1; }"
    result = await executor.execute(code, test_code="assert(test() === 1);")

    # Since php is not on path, it should fail gracefully with missing runtime warning
    assert result.status == ExecutionStatus.FAILURE
    assert "php cli is not installed" in result.logs.stderr.lower()


@pytest.mark.asyncio
async def test_c_executor_missing():
    executor = EphemeralCExecutor()
    code = "int test() { return 1; }"
    result = await executor.execute(code, test_code="assert_c(test() == 1, \"error\");")

    assert result.status == ExecutionStatus.FAILURE
    assert "c compiler" in result.logs.stderr.lower()


@pytest.mark.asyncio
async def test_html_executor_success():
    executor = EphemeralHtmlExecutor()
    code = "<div><p>Hello LogicHive</p></div>"
    test_code = "Hello LogicHive"
    result = await executor.execute(code, test_code=test_code)

    assert result.status == ExecutionStatus.SUCCESS
    assert len(result.results) > 0


@pytest.mark.asyncio
async def test_html_executor_mismatched_tag():
    executor = EphemeralHtmlExecutor()
    code = "<div><p>Unclosed HTML"
    result = await executor.execute(code)

    assert result.status == ExecutionStatus.FAILURE
    assert "unclosed" in result.logs.stderr.lower()
