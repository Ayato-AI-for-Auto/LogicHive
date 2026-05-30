import httpx
import asyncio


async def test():
    # Try to POST to the message endpoint WITHOUT trailing slash
    url = "http://127.0.0.1:10880/messages"
    print(f"POST to {url}")
    try:
        r = httpx.post(url, json={"jsonrpc": "2.0", "method": "initialize", "params": {}})
        print(f"Status: {r.status_code}")
        if r.status_code == 405:
            print("REPRODUCED! 405 on missing trailing slash.")
    except Exception as e:
        print(f"Error: {e}")


asyncio.run(test())
