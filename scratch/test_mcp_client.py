import asyncio
import os
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def run():
    url = "http://127.0.0.1:10880/sse"
    print(f"Connecting to {url}")
    try:
        async with sse_client(url) as streams:
            print("Connected! Starting session...")
            async with ClientSession(streams[0], streams[1]) as session:
                print("Session created. Initializing...")
                await session.initialize()
                print("Initialized!")
                
                tools = await session.list_tools()
                print(f"Tools: {tools}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(run())
