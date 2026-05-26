import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=api_key)
print("Listing all available Gemini models:")
try:
    for model in client.models.list():
        print(f"- {model.name} (displayName: {model.display_name})")
except Exception as e:
    print(f"Error: {e}")
