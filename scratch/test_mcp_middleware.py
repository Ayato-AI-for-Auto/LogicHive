from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
import uvicorn

mcp = FastMCP("test")
mcp.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@mcp.tool()
def hello() -> str:
    return "world"

if __name__ == "__main__":
    # Test if middleware is applied
    app = mcp.http_app(transport="sse")
    print(f"Middleware: {app.user_middleware}")
