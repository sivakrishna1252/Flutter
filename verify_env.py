from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(r"c:\Users\ShivakrishnaDuddukur\OneDrive - Apparatus Solutions\Desktop\Flutter")
load_dotenv(BASE_DIR / "config" / ".env")

key = os.getenv("OPENAI_API_KEY")
if key:
    print("OPENAI_API_KEY found")
    print(f"Key length: {len(key)}")
    if len(key) > 5:
        print(f"Key starts with: {key[:5]}...")
else:
    print("OPENAI_API_KEY NOT found")
