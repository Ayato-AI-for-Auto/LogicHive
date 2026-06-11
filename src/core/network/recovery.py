# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import sys

import psutil

from core.config import save_config
from core.logging_config import get_logger
from core.network.diagnostics import (
    find_available_port,
    get_conflicting_process,
    wait_on_error,
)

logger = get_logger(__name__)


def handle_port_conflict(current_port: int, host_val: str) -> int:
    """Handles network bind errors (port conflict) by offering interactive recovery or auto-finding a port."""
    import mcp_server
    import core.config

    # Diagnostics
    proc = mcp_server.get_conflicting_process(current_port)
    proc_info = ""
    if proc:
        try:
            proc_info = f"Conflicting process found: {proc.name()} (PID: {proc.pid})"
            logger.error(proc_info)
        except Exception:
            proc_info = "Conflicting process detected, but failed to retrieve details."
            logger.error(proc_info)

    if sys.stdin.isatty():
        print("\n" + "=" * 60)
        print(f"PORT CONFLICT: Port {current_port} is already in use.")
        if proc_info:
            print(proc_info)
        else:
            print("No conflicting process could be identified.")
        print("=" * 60)
        print("Please choose a recovery option:")
        print("1. [Retry] Re-attempt binding (manually free the port first)")
        print("2. [Kill] Terminate the conflicting process")
        print("3. [Auto-find] Automatically search for the next available port")
        print("4. [Exit] Exit the application")
        print("=" * 60)

        try:
            choice = input("Enter choice (1-4): ").strip()
        except (KeyboardInterrupt, EOFError):
            logger.info("Cancelled by user. Exiting.")
            mcp_server.wait_on_error()
            sys.exit(1)

        if choice == "1":
            logger.info("Retrying port binding...")
            return current_port
        elif choice == "2":
            if proc:
                try:
                    logger.info(f"Attempting to terminate process {proc.name()} (PID: {proc.pid})...")
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                        logger.info("Process terminated successfully. Retrying port binding...")
                    except psutil.TimeoutExpired:
                        logger.warning("Process did not terminate in time. Forcing kill...")
                        proc.kill()
                        proc.wait(timeout=2)
                        logger.info("Process killed successfully. Retrying port binding...")
                except Exception as kill_err:
                    logger.error(f"Failed to resolve conflicting process: {kill_err}")
            else:
                logger.warning("No conflicting process identified to terminate. Retrying anyway...")
            return current_port
        elif choice == "3":
            new_port = mcp_server.find_available_port(current_port + 1, host_val)
            if new_port == current_port:
                logger.error("No available ports could be found.")
                mcp_server.wait_on_error()
                sys.exit(1)
            logger.info(f"Auto-found available port: {new_port}")
            try:
                save_choice = input("Would you like to save this port as the default in your config? (y/N): ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                save_choice = "n"
            if save_choice in ("y", "yes"):
                if core.config.save_config({"PORT": new_port}):
                    logger.info(f"Port {new_port} successfully saved to config.")
                else:
                    logger.error("Failed to save configuration.")
            return new_port
        else:
            logger.info("Exiting application...")
            mcp_server.wait_on_error()
            sys.exit(1)
    else:
        logger.warning("Non-interactive run detected. Port binding failed.")
        new_port = mcp_server.find_available_port(current_port + 1, host_val)
        if new_port == current_port:
            logger.error("No available ports could be found.")
            mcp_server.wait_on_error()
            sys.exit(1)
        logger.info(f"Auto-finding port in non-interactive mode. Selected: {new_port}")
        return new_port
