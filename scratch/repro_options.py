import httpx
import asyncio


async def test():
    url = "http://127.0.0.1:10880/messages/"
    print(f"OPTIONS to {url}")
    try:
        r = httpx.options(
            url, headers={"Origin": "http://example.com", "Access-Control-Request-Method": "POST"}
        )
        print(f"Status: {r.status_code}")
        print(f"Allow: {r.headers.get('allow')}")
    except Exception as e:
        print(f"Error: {e}")


asyncio.run(test())
