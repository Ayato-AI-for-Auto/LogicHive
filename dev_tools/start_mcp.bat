@echo off
set PYTHONPATH=C:/Users/saiha/My_Service/programing/MCP/function_store_mcp/backend
uv run --with duckdb --with fastmcp python -m edge.mcp_server
