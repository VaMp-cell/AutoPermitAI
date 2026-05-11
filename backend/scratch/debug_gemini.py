import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

print(f"Using API Key: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

try:
    genai.configure(api_key=api_key)
    print("Listing models...")
    models = list(genai.list_models())
    print(f"Total models found: {len(models)}")
    model_list = [m.name for m in models]
    print(f"Available models: {model_list}")
except Exception as e:
    print(f"Error type: {type(e)}")
    print(f"Error: {e}")
