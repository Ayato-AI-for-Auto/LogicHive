# Vulnerability Scan - NoneType Error (2026-06-13)

## Problem
Background vulnerability scans were failing with the following error:
`'NoneType' object has no attribute 'get'`

This occurred during the processing of OSV API responses and database-stored function metadata.

## Root Cause
The codebase assumed that API responses (`res_data`) and certain fields within database records (e.g., `verification_report`, `details`) would always be valid dictionaries. When the API returned `null` or when specific fields were missing/`null` in the database, the code attempted to call `.get()` on a `None` value, resulting in a crash.

## Fix
Defensive programming checks were added to ensure type safety before accessing dictionary/list methods:

1.  **`src/core/evaluation/plugins/dependency_vouch.py`**: Added checks to verify `res_data` is a `dict`, `vulns` is a `list`, and each entry `v` is a `dict`.
2.  **`src/core/vulnerability/scanner.py`**: Added checks to verify function objects (`f`) are `dict`s, vulnerability entries (`v`) are `dict`s, and all nested fields in `verification_report` exist and have correct types before access.
3.  **`get_vulnerability_warning_msg`**: Added explicit `None`/type checks to prevent crashing when generating security warning messages for UI/logs.

## Prevention
Future modifications to data ingestion or API interaction must strictly validate the schema/type of external and database-persisted data using `isinstance()` checks before accessing attributes or keys.
