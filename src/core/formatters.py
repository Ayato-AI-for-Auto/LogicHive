# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import json

from core.exceptions import SyntaxValidationError, ValidationError


def format_syntax_error(e: SyntaxValidationError) -> str:
    """Format a syntax validation error into a user-friendly markdown report."""
    details = e.details or {}
    eval_details = details.get("eval_details", {}).get("static_analysis", {})
    inner_details = eval_details.get("details", {})

    line = inner_details.get("line", "?")
    offset = inner_details.get("offset", "?")
    text = inner_details.get("text", "N/A")

    md = [
        "### ❌ IMMEDIATE REJECTION: Syntax Error",
        f"**Message**: {str(e)}",
        f"- **Line**: {line}",
        f"- **Offset**: {offset}",
        f"\n**Context**:\n```python\n{text.strip()}\n```",
        "\nPlease correct the syntax before attempting to save again.",
    ]
    return "\n".join(md)


def format_validation_error(e: ValidationError) -> str:
    """Format a quality gate validation error into a user-friendly markdown report."""
    details = e.details or {}
    score = details.get("score", 0)
    reason = details.get("reason", str(e))
    eval_details = details.get("eval_details", {})

    # Build a helpful report
    report = [f"Quality Gate REJECTED: {reason}", f"Final Score: {score:.1f}/100"]

    if eval_details:
        report.append("\nBreakdown:")
        for tool_name, res in eval_details.items():
            tool_score = res.get("score", 0)
            tool_reason = res.get("reason", "N/A")
            report.append(f"- {tool_name}: {tool_score:.1f} ({tool_reason})")

            # Show traceback or stderr if available (Crucial for debugging)
            inner_details = res.get("details", {}) or {}
            if inner_details.get("traceback"):
                report.append(f"  [TRACEBACK]\n{inner_details['traceback']}")
            elif inner_details.get("stderr"):
                report.append(f"  [STDERR]\n{inner_details['stderr']}")

    return "\n".join(report)


def get_status_description(status: str) -> str:
    """Get markdown description for verification status."""
    mapping = {
        "verified": "Quality Gate passed. Asset is active in the vault.\n",
        "pending": "Verification is still in progress. Please check back shortly.\n",
        "failed": "Quality Gate rejected the asset. Review the report below for details.\n",
        "error": "A system error occurred during verification. Infrastructure might be unstable.\n",
    }
    return mapping.get(status, "")


def format_report(report) -> str:
    """Format verification report into markdown."""
    if not isinstance(report, dict):
        return f"```json\n{report}\n```"

    if "error" in report:
        return f"**Error Details**: {report['error']}\n"

    if "reason" in report:
        md = f"- **Reason**: {report.get('reason', 'N/A')}\n"
        details = report.get("details", {})
        for tool, res in details.items():
            md += f"- **{tool.title()}**: {res.get('score', 0):.1f} ({res.get('reason', 'N/A')})\n"
        return md

    return f"```json\n{json.dumps(report, indent=2)}\n```"
