"""
Step 2 backend: JSON → marketing summary + image prompt via Gemini.

Called from ui_enrich.py. Input: menu+event JSON from Step 1. Output:
marketing_summary (2–4 sentences) and image_prompt for Step 3 image generation.
CLI: python enrich_from_json.py [path/to/file.json] [-o output_dir]; omit path for file picker.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

import google.generativeai as genai

load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL_ID = "gemini-2.5-pro"

# Prompt sent to Gemini: we append the menu+event JSON and ask for JSON back (summary + image_prompt).
ENRICH_PROMPT = """You are given a JSON object describing a menu and an event (e.g. for a bar or restaurant).

Generate two things. Output only valid JSON, no markdown or explanation:

{
  "marketing_summary": "A short marketing-style summary in 2–4 sentences that promotes the venue, menu, and event. Engaging and concise.",
  "image_prompt": "A detailed image prompt suitable for an image generation model (e.g. for a poster or social media card). Describe the scene, style, mood, and key elements (food, drinks, event) in one paragraph. The prompt should be informative but at the same time it shouldn't include unnecessary details."
}

Rules:
- Base everything only on the provided JSON. Do not invent menu items or event details.
- marketing_summary: 2–4 sentences, promotional tone.
- image_prompt: One paragraph, concrete and visual (style, colors, composition, key items).

Input JSON:

"""


def _get_api_key() -> str:
    """Read API key from env; used to configure genai before calling the model."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "Gemini API key not set. Set GEMINI_API_KEY in your environment or .env."
        )
    return key.strip()


def _strip_json_block(raw: str) -> str:
    """If the model wrapped JSON in ```json ... ```, return only the inner content."""
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        return match.group(1).strip()
    return raw


def load_json(path: Path) -> dict:
    """Load and validate JSON has at least menu_items and event."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Require the schema expected by the enrich prompt.
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object.")
    if "menu_items" not in data or "event" not in data:
        raise ValueError("JSON must contain 'menu_items' and 'event'.")
    return data


def generate_summary_and_prompt(json_data: dict) -> dict:
    """Send JSON to Gemini; return dict with marketing_summary and image_prompt."""
    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel(MODEL_ID)
    config = {"response_mime_type": "application/json"}
    # Append the input JSON so the model has full context; ask for JSON back.
    prompt = ENRICH_PROMPT + json.dumps(json_data, indent=2, ensure_ascii=False)
    response = model.generate_content(prompt, generation_config=config)

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    # Handle optional markdown code fence, then parse and validate keys.
    text = _strip_json_block(response.text)
    out = json.loads(text)
    if "marketing_summary" not in out or "image_prompt" not in out:
        raise ValueError("Response must contain 'marketing_summary' and 'image_prompt'.")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate marketing summary and image prompt from menu+event JSON via Gemini.",
    )
    parser.add_argument(
        "json_file",
        type=Path,
        nargs="?",
        default=None,
        help="Path to the JSON file (output from Get JSON). If omitted, a file picker opens.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory to write summary.txt and image_prompt.txt.",
    )
    args = parser.parse_args()

    # If no JSON path given, open a file picker (requires tkinter).
    json_path = args.json_file
    if json_path is None:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path_str = filedialog.askopenfilename(
                title="Select menu+event JSON file",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )
            root.destroy()
            if not path_str:
                print("No file selected.", file=sys.stderr)
                return 1
            json_path = Path(path_str)
        except ImportError:
            print("Error: json_file is required when tkinter is not available.", file=sys.stderr)
            return 1

    if not json_path.exists():
        print(f"Error: file not found: {json_path}", file=sys.stderr)
        return 1

    try:
        data = load_json(json_path)
        result = generate_summary_and_prompt(data)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    summary = result["marketing_summary"]
    image_prompt = result["image_prompt"]

    # Print both outputs to stdout.
    print("--- Marketing summary ---")
    print(summary)
    print("\n--- Image prompt ---")
    print(image_prompt)

    # Optionally write summary and image prompt to files in the given directory.
    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "summary.txt").write_text(summary, encoding="utf-8")
        (args.output_dir / "image_prompt.txt").write_text(image_prompt, encoding="utf-8")
        print(f"\nSaved to {args.output_dir / 'summary.txt'} and {args.output_dir / 'image_prompt.txt'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
