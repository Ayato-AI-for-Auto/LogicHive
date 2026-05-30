import httpx
import asyncio

async def test():
    # Try to POST to the SSE endpoint (should return 405)
    url = "http://127.0.0.1:10880/sse"
    print(f"POST to {url}")
    try:
        r = httpx.post(url, json={"jsonrpc": "2.0", "method": "initialize", "params": {}})
        print(f"Status: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # Try to POST to the message endpoint (should return 202 or 404 if no session)
    url = "http://127.0.0.1:10880/messages/"
    print(f"POST to {url}")
    try:
        r = httpx.post(url, json={"jsonrpc": "2.0", "method": "initialize", "params": {}})
        print(f"Status: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
