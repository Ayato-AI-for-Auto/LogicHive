import httpx
import asyncio


async def test_session():
    url = "http://127.0.0.1:10880/mcp"
    print(f"POST to {url} with Accept headers")
    try:
        # Client needs to accept both to initiate the session
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        r = httpx.post(
            url,
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            },
            headers=headers,
        )
        print(f"Initialize Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")


asyncio.run(test_session())
