from fastmcp import FastMCP
import inspect
mcp = FastMCP("test")
print(inspect.getsource(mcp.http_app))
