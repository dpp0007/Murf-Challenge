"""List available Gemini models."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env.local")

import google.generativeai as genai

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

print("Available models:")
for model in genai.list_models():
    print(f"  - {model.name}")
    if hasattr(model, 'display_name'):
        print(f"    Display: {model.display_name}")
    if hasattr(model, 'supported_generation_methods'):
        print(f"    Methods: {model.supported_generation_methods}")
