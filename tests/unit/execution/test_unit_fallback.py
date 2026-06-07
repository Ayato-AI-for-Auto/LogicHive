from unittest.mock import AsyncMock, patch

import pytest

from core.execution.c import EphemeralCExecutor
from core.execution.html import StrictHTMLParser
from core.execution.java import EphemeralJavaExecutor
from core.execution.javascript import EphemeralJavaScriptExecutor
from core.execution.php import EphemeralPhpExecutor


@pytest.mark.asyncio
async def test_javascript_is_node_available_mock():
    executor = EphemeralJavaScriptExecutor()

    # Test Node available
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"v22.0.0", b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc

        assert await executor._is_node_available() is True

    # Test Node missing
    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
        assert await executor._is_node_available() is False


@pytest.mark.asyncio
async def test_java_is_java_available_mock():
    executor = EphemeralJavaExecutor()

    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"javac 17", b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc

        assert await executor._is_java_available() is True


@pytest.mark.asyncio
async def test_php_is_php_available_mock():
    executor = EphemeralPhpExecutor()

    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"PHP 8.2", b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc

        assert await executor._is_php_available() is True


@pytest.mark.asyncio
async def test_c_find_compiler_mock():
    executor = EphemeralCExecutor()

    # Simulates gcc is found, clang/cl not checked or missing
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"gcc 11", b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc

        compiler = await executor._find_compiler()
        assert compiler == "gcc"


def test_html_strict_parser_nesting():
    # Valid nesting
    parser = StrictHTMLParser()
    parser.feed("<div><p>hello</p></div>")
    parser.close()
    assert len(parser.errors) == 0
    assert len(parser.tags) == 0

    # Unclosed tag
    parser = StrictHTMLParser()
    parser.feed("<div><p>hello</div>")
    parser.close()
    assert len(parser.errors) > 0  # Mismatched tags

    # Unexpected close tag
    parser = StrictHTMLParser()
    parser.feed("</span>")
    parser.close()
    assert len(parser.errors) == 1
    assert parser.errors[0] == "Unexpected closing tag: </span>"
