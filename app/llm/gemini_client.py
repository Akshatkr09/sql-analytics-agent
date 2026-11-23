"""Gemini API client factory."""
import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai

load_dotenv()


@lru_cache(maxsize=2)
def get_gemini_client():
    """Create a cached Gemini client using GEMINI_API_KEY from .env."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key":
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add your Gemini API key to the local .env file."
        )
    return genai.Client(api_key=api_key)


def get_gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
