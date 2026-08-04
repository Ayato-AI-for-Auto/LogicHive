# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Shared data types for LogicHive."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class VerificationStatus(str, Enum):
    """Verification status of a code asset."""

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    ERROR = "error"
    DRAFT = "draft"


class Language(str, Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    C = "c"
    CPP = "cpp"
    JAVA = "java"


@dataclass
class CodeAsset:
    """Represents a stored code asset."""

    id: str
    name: str
    code: str
    description: str = ""
    language: str = "python"
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    test_code: str = ""
    project: str = "default"
    reliability_score: float = 0.0
    verification_status: str = "pending"
    verification_report: dict[str, Any] | None = None
    code_hash: str = ""
    env_fingerprint: dict[str, Any] | None = None


@dataclass
class SearchResult:
    """Represents a search result from the vault."""

    name: str
    project: str
    description: str
    language: str
    tags: list[str]
    reliability_score: float
    similarity: float
    is_draft: bool = False
    env_fingerprint: dict[str, Any] | None = None


@dataclass
class EvaluationResult:
    """Result from a quality gate evaluation."""

    score: float
    reason: str
    details: dict[str, Any] = field(default_factory=dict)
    is_system_error: bool = False
