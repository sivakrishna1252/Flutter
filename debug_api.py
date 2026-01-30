
import os
import requests
import json
from dotenv import load_dotenv
from pathlib import Path

# Manually load .env
base_dir = Path(__file__).resolve().parent
env_file = base_dir / 'config' / '.env'
print(f"Loading env from {env_file}")
load_dotenv(env_file)

api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key: {api_key}")

if not api_key:
    print("NO API KEY FOUND")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
#    "HTTP-Referer": "http://localhost:8000", # Optional for auth/key?
#    "X-Title": "Diet Planner"
}

print("Checking auth/key...")
try:
    resp = requests.get("https://openrouter.ai/api/v1/auth/key", headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")

print("\nChecking generation...")
headers["HTTP-Referer"] = "http://localhost:8000"
headers["X-Title"] = "Diet Planner"
headers["Content-Type"] = "application/json"

data = {
    "model": "google/gemini-2.0-flash-exp:free",
    "messages": [{"role": "user", "content": "hi"}]
}

try:
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
