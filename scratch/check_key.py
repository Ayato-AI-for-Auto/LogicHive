import asyncio
import os

from dotenv import load_dotenv
from google import genai


async def test_key():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"Testing API Key: {api_key[:10]}...")

    client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
    try:
        client.models.embed_content(model="text-embedding-004", contents="Hello World")
        print("Success! Response received.")
    except Exception as e:
        print(f"Failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_key())
