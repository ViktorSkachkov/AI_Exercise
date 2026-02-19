"""
Normalize extracted PDF text for LLM consumption.

Used in Step 1 after pdf_extractor.extract_text(): handles messy or imperfect
formatting (encoding glitches, HTML remnants, inconsistent currency, whitespace)
before sending text to the LLM for structured JSON extraction.
"""

import re

# Unicode replacement character often appears when € or — is mis-encoded
REPLACEMENT_CHAR = "\uFFFD"


def normalize_for_llm(raw: str) -> str:
    """
    Clean extracted PDF text so an LLM can parse it more reliably.

    - Fixes replacement-character mojibake (e.g. for € or —)
    - Converts HTML line breaks to newlines
    - Normalizes currency to " EUR" (eur, EUR, € after amounts → " EUR")
    - Merges table continuation lines so Ingredients/Notes (and any overflow) stay on one row
    - Collapses excess whitespace and strips lines

    Use after extract_text() and before sending the string to an LLM.
    """
    if not raw:
        return raw

    text = raw

    # 1. HTML line breaks → real newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

    # 2. Fix replacement character () heuristics
    # Between words → em dash (e.g. "available reservations")
    text = re.sub(
        rf"(\w)\s*{re.escape(REPLACEMENT_CHAR)}\s*(\w)",
        r"\1 — \2",
        text,
    )
    # After digits (price) → euro (e.g. "15" or "7")
    text = re.sub(
        rf"(\d)\s*{re.escape(REPLACEMENT_CHAR)}\s*",
        r"\1€ ",
        text,
    )
    # Standalone in table cell or before/after space → em dash (e.g. "||" or "Paloma||")
    text = re.sub(
        rf"\s*{re.escape(REPLACEMENT_CHAR)}\s*",
        " — ",
        text,
    )

    # 3. Normalize currency: everything → " EUR" after amounts (so eur, EUR, € all match)
    text = re.sub(r"\beur\b", "EUR", text, flags=re.IGNORECASE)
    # Number + optional space + € → number + " EUR" (e.g. "15€", "7 €" → "15 EUR", "7 EUR")
    text = re.sub(r"(\d+(?:[.,]\d+)?)\s*€\s*", r"\1 EUR ", text)

    # 4. Merge table cell continuations (e.g. Ingredients/Notes split across lines)
    #    Lines that end with | but don't start with | are the rest of the previous row's last cell
    lines = text.split("\n")
    merged: list[str] = []
    for line in lines:
        stripped = line.strip()
        if (
            stripped.endswith("|")
            and not stripped.startswith("|")
            and merged
        ):
            # Continuation of previous row (e.g. "(served chilled) |" or overflow text)
            merged[-1] = merged[-1] + " " + stripped
        else:
            merged.append(line)

    # 5. Whitespace: strip each line, collapse 3+ newlines to 2
    lines = [line.rstrip() for line in merged]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove leading/trailing blank lines
    text = text.strip("\n")

    return text
