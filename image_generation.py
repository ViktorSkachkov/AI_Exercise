"""
Step 3 backend: generate an image from a text prompt using the Gemini API.

Called from ui_image_generation.py. Input: image prompt from Step 2 (enrich_from_json).
Uses gemini-3-pro-image-preview.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL_ID = "gemini-3-pro-image-preview"


def _get_api_key() -> str:
    """Read API key from env; used to create the genai client."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "Gemini API key not set. Set GEMINI_API_KEY in your environment or .env."
        )
    return key.strip()


def generate_image(prompt: str) -> Optional[bytes]:
    """
    Send a text prompt to the Gemini image model and return the generated image as PNG bytes.

    Returns None if the model produced no image (e.g. safety block). Raises on API/key errors.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt must be non-empty.")

    # Request image generation; response_modalities=["IMAGE"] asks for image output instead of text.
    client = genai.Client(api_key=_get_api_key())
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[prompt.strip()],
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    if not response.candidates:
        return None
    # Extract raw image bytes from the first candidate’s inline_data (e.g. PNG).
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            raw = getattr(part.inline_data, "data", None)
            if raw:
                return raw
    return None
