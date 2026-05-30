from fastmcp import FastMCP
import inspect
mcp = FastMCP("test")
print(f"File: {inspect.getfile(mcp.http_app)}")
