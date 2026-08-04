# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Exception classes for LogicHive - re-exported from shared for backwards compatibility."""

from shared.exceptions import (
    AIProviderError,
    DependencyExtractionError,
    LogicHiveError,
    QualityGateError,
    StorageError,
    SyntaxValidationError,
    ValidationError,
)

__all__ = [
    "LogicHiveError",
    "ValidationError",
    "StorageError",
    "AIProviderError",
    "DependencyExtractionError",
    "QualityGateError",
    "SyntaxValidationError",
]
