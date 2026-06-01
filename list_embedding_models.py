from google import genai
import os

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("--- Available Models ---")
for model in client.models.list():
    if "embedding" in model.name.lower():
        print(f"Name: {model.name}, Display Name: {model.display_name}")
