import time
from html.parser import HTMLParser

from core.logging_config import get_logger

from .base import (
    BaseExecutor,
    ExecutionError,
    ExecutionLogs,
    ExecutionResult,
    ExecutionStatus,
    Result,
)
from .factory import ExecutorFactory

logger = get_logger(__name__)


class StrictHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        # Void/self-closing tags in HTML5
        void_tags = {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }
        if tag not in void_tags:
            self.tags.append(tag)

    def handle_endtag(self, tag):
        void_tags = {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }
        if tag in void_tags:
            return
        if not self.tags:
            self.errors.append(f"Unexpected closing tag: </{tag}>")
            return
        expected = self.tags.pop()
        if expected != tag:
            self.errors.append(f"Mismatched tag: expected </{expected}>, got </{tag}>")


class EphemeralHtmlExecutor(BaseExecutor):
    """
    Executes structural evaluation on HTML files using Python's html.parser.
    """

    def __init__(self):
        self.name = "html"

    async def execute(
        self,
        code: str,
        test_code: str = "",
        dependencies: list[str] | None = None,
        timeout: int = 10,
        memory_limit_mb: int = 256,
        **kwargs,
    ) -> ExecutionResult:
        logger.info("HTML Executor: Starting validation")
        start_time = time.perf_counter()

        parser = StrictHTMLParser()
        try:
            parser.feed(code)
            parser.close()
        except Exception as e:
            err_msg = f"HTML Parsing Error: {e}"
            return ExecutionResult(
                status=ExecutionStatus.FAILURE,
                logs=ExecutionLogs(stderr=err_msg),
                error=ExecutionError(name="HTMLParserError", value=err_msg, traceback=""),
                duration=time.perf_counter() - start_time,
            )

        if parser.errors:
            err_msg = "\n".join(parser.errors)
            return ExecutionResult(
                status=ExecutionStatus.FAILURE,
                logs=ExecutionLogs(stderr=err_msg),
                error=ExecutionError(name="HTMLValidationError", value=err_msg, traceback=""),
                duration=time.perf_counter() - start_time,
            )

        if parser.tags:
            unclosed = ", ".join([f"<{t}>" for t in reversed(parser.tags)])
            err_msg = f"Unclosed HTML tags detected: {unclosed}"
            return ExecutionResult(
                status=ExecutionStatus.FAILURE,
                logs=ExecutionLogs(stderr=err_msg),
                error=ExecutionError(name="HTMLValidationError", value=err_msg, traceback=""),
                duration=time.perf_counter() - start_time,
            )

        # Basic verification: Check if test_code (regex or tag asserts) passes
        # E.g. test_code contains strings of tags that should be present
        if test_code:
            for line in test_code.split("\n"):
                term = line.strip()
                if term and term not in code:
                    err_msg = f"HTML Assertion failed: Could not find '{term}' in the markup."
                    return ExecutionResult(
                        status=ExecutionStatus.FAILURE,
                        logs=ExecutionLogs(stderr=err_msg),
                        error=ExecutionError(name="AssertionError", value=err_msg, traceback=""),
                        duration=time.perf_counter() - start_time,
                    )

        duration = time.perf_counter() - start_time
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            logs=ExecutionLogs(stdout="HTML structural validation successful."),
            results=[Result(data="All HTML parsing tests passed successfully.")],
            duration=duration,
        )


# Auto-register
ExecutorFactory.register("html", EphemeralHtmlExecutor())
