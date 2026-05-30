import os
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
import uvicorn

mcp = FastMCP("test")


@mcp.tool()
def hello() -> str:
    return "Hello"


app = mcp.sse_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    print("Testing uvicorn run with cors...")
    uvicorn.run(app, host="127.0.0.1", port=10885)
