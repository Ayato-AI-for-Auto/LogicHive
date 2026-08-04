# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Logging configuration for LogicHive - re-exported from shared for backwards compatibility."""

from shared.logging_config import (
    InterceptHandler,
    current_run_id,
    get_logger,
    json_serializer,
    rotate_previous_execution_log,
    setup_logging,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "current_run_id",
    "InterceptHandler",
    "json_serializer",
    "rotate_previous_execution_log",
]
