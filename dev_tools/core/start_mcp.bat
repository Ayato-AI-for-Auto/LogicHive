@echo off
set PYTHONPATH=C:/Users/saiha/My_Service/programing/MCP/LogicHive-Edge/backend
uv run --with duckdb --with fastmcp python -m edge.mcp_server
