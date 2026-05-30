import httpx
import asyncio

async def test():
    try:
        r = httpx.options("http://127.0.0.1:10885/messages/?session_id=123", headers={"Origin": "http://example.com", "Access-Control-Request-Method": "POST"})
        print(f"Status: {r.status_code}")
        print(f"Headers: {r.headers}")
        print(f"Body: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
