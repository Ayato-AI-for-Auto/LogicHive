# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""API contract types for MCP Server <-> Verification Server communication."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VerificationRequest:
    """Request to verify a code asset."""

    code: str
    test_code: str = ""
    language: str = "python"
    dependencies: list[str] = field(default_factory=list)
    timeout: int = 20
    memory_limit_mb: int = 256


@dataclass
class VerificationResult:
    """Result of a verification execution."""

    status: str  # pass, fail, error, timeout, memory_limit
    stdout: str = ""
    stderr: str = ""
    traceback: str = ""
    duration: float = 0.0
    exit_code: int = 0


@dataclass
class VerificationResponse:
    """Response from the Verification Server."""

    success: bool
    result: VerificationResult | None = None
    error: str | None = None


@dataclass
class HealthResponse:
    """Health check response from Verification Server."""

    status: str
    version: str
    active_tasks: int = 0
    max_concurrent: int = 4
