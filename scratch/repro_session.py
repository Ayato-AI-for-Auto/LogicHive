import httpx
import asyncio

async def test_session():
    # 1. Attempt to list tools to trigger session creation
    url = "http://127.0.0.1:10880/mcp"
    print(f"POST to {url} (tools/list)")
    try:
        # Streamable HTTP requires a specific session handshake
        # Let's try sending a simple JSON-RPC request to the mount point
        r = httpx.post(url, json={"jsonrpc": "2.0", "method": "initialize", "params": {}})
        print(f"Initialize Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_session())
