"""
Step 1 backend: send extracted PDF text to Gemini and get structured JSON.

Called from ui_json_generation.py when the user clicks "Get JSON". Returns
menu_items and event as a dict.
"""

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

import google.generativeai as genai

# Load .env from project root so the API key can be stored there
load_dotenv(Path(__file__).resolve().parent / ".env")


# Pro model for highest-quality structured extraction (paid tier).
MODEL_ID = "gemini-2.5-pro"

STRUCTURED_PROMPT = """You are extracting structured data from a document that contains a menu and one event.

Output only valid JSON, with no markdown, no code fences, and no explanation. Your response must be parseable by json.loads().
Only actual ingredients should be stored in the variable 'ingredients' (this means that, for example, 'sweet banana' should be changed to just 'banana', 'tasty beef' should be changed to 'beef', etc.). However, something like 'apple juice' should remain the same because this is an actual ingredient.
For the 'event, the variable 'description' needs to contain only the most important information and it should be concise but still informative. The people should be informed in short about what the event is about and thethings they need to do.
Use this exact structure (use null for missing fields, omit optional keys if entirely unknown):

{
  "menu_items": [
    {
      "name": "string or null",
      "category": "string or null",
      "price": number or null,
      "ingredients": "string or null",
      "currency": "string or null"
    }
  ],
  "event": {
    "title": "string or null",
    "date": "string or null",
    "time": "string or null",
    "description": "string or null",
    "location": "string or null"
  }
}

Rules:
- Use only information that appears in the document. Do not invent or hallucinate any data.
- For menu items: category should be something like "Cocktails", "Food", etc. if present; otherwise a reasonable category or null.
- For price: use a number only (e.g. 14 for "14 EUR"). Use null if price is missing or non-numeric (e.g. "price varies").
- For date: prefer YYYY-MM-DD when possible; otherwise keep the original format as string.
- If there is no event in the document, set "event" to {"title": null, "date": null, "description": null, "location": null}.
- If there are no menu items, set "menu_items" to [].
- If there is a word in the final JSON which looks incomplete like it was cut off, you can complete that specific word

Document text:

"""


def _get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "Gemini API key not set. Set GEMINI_API_KEY in your environment."
        )
    return key.strip()


def _strip_json_block(raw: str) -> str:
    """Remove markdown code fence if the model wrapped JSON in ```json ... ```."""
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        return match.group(1).strip()
    return raw


def extract_structured_data(cleaned_text: str) -> dict[str, Any]:
    """
    Send cleaned extracted text to Gemini and return structured JSON (menu_items + event).

    Args:
        cleaned_text: Text from PDF after extraction and normalize_for_llm().

    Returns:
        Dict with keys "menu_items" (list) and "event" (dict). Valid JSON structure.

    Raises:
        ValueError: If API key is missing or response is not valid JSON.
    """
    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel(MODEL_ID)
    generation_config = {"response_mime_type": "application/json"}
    prompt = STRUCTURED_PROMPT + cleaned_text
    response = model.generate_content(prompt, generation_config=generation_config)

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    text = _strip_json_block(response.text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini response was not valid JSON: {e}") from e
