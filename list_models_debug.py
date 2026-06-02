from google import genai
import os
from dotenv import load_dotenv

# Try loading from multiple possible locations to ensure we get the key
load_dotenv()
load_dotenv(os.path.join(os.path.expanduser("~"), ".logichive", ".env"))

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment.")
    exit(1)

client = genai.Client(api_key=api_key)

print("--- Available Gemma 4 Models ---")
try:
    for model in client.models.list():
        if "gemma-4" in model.name.lower():
            print(f"Name: {model.name}, Display Name: {model.display_name}")
except Exception as e:
    print(f"Error listing models: {e}")
