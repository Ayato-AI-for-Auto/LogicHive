# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Exception classes for LogicHive."""


class LogicHiveError(Exception):
    """Base exception for LogicHive."""

    pass


class ValidationError(LogicHiveError):
    """Raised when code validation or quality gate fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}


class StorageError(LogicHiveError):
    """Raised when storage operations fail."""

    pass


class AIProviderError(LogicHiveError):
    """Raised when AI provider (Gemini/Ollama) fails."""


class DependencyExtractionError(LogicHiveError):
    """Raised when dependency extraction fails critically."""

    pass


class QualityGateError(ValidationError):
    """Raised when a code asset fails the Quality Gate check."""

    pass


class SyntaxValidationError(QualityGateError):
    """Raised specifically for syntax errors detected during pre-save validation."""

    pass
