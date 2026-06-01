import os
from dotenv import load_dotenv
from google import genai

load_dotenv('C:/Users/saiha/.logichive/.env')
load_dotenv('.env', override=True)

api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
client = genai.Client(api_key=api_key)

print(f"Using API Key: {api_key[:10]}...")
for m in client.models.list():
    print(f"- {m.name} (supported: {m.supported_actions})")
