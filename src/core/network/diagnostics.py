# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import socket
import sys

import psutil

from core.logging_config import get_logger

logger = get_logger(__name__)


def wait_on_error():
    """Prevents the terminal window from closing immediately in frozen mode."""
    if getattr(sys, "frozen", False):
        logger.info("=" * 60)
        input("Press Enter to exit...")


def get_conflicting_process(port: int):
    """Identifies the process currently using the specified port."""
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == port and conn.status == "LISTEN":
                return psutil.Process(conn.pid)
    except Exception as e:
        logger.debug(f"Diagnostics: Failed to check for conflicting process on port {port}: {e}")
    return None


def find_available_port(start_port: int, host: str = "0.0.0.0") -> int:
    """Finds the first available port starting from start_port."""
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                port += 1
    return start_port
