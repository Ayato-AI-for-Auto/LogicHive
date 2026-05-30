import inspect
import mcp.server.fastmcp.server as fastmcp_server
print('CORSMiddleware' in inspect.getsource(fastmcp_server.FastMCP.sse_app))
