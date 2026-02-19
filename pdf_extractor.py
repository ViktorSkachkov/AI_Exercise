"""
PDF text extraction using pymupdf4llm.

Used in Step 1 (ui_json_generation.py): extracts content from PDF files as Markdown,
preserving structure (headings, tables, lists) for downstream LLM/JSON extraction.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

import pymupdf4llm


def extract_text(
    pdf_path: str | Path,
    *,
    output_path: Optional[str | Path] = None,
    page_separators: bool = False,
    show_progress: bool = False,
) -> str:
    """
    Extract text from a PDF file as Markdown (all pages).

    Args:
        pdf_path: Path to the PDF file.
        output_path: If set, write the extracted text to this file (UTF-8).
        page_separators: If True, insert "--- end of page=n ---" between pages.
        show_progress: If True, show a progress bar during extraction.

    Returns:
        The extracted text as a single Markdown string.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If the path is not a file or not a PDF.
    """
    path = Path(pdf_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF (extension: {path.suffix}): {path}")

    text = pymupdf4llm.to_markdown(
        str(path),
        page_separators=page_separators,
        show_progress=show_progress,
    )

    if output_path is not None:
        out = Path(output_path).resolve()
        out.write_text(text, encoding="utf-8")

    return text


def main() -> int:
    """CLI entry point. Run with: python -m pdf_extractor <input.pdf> [options]"""
    parser = argparse.ArgumentParser(
        description="Extract text from a PDF file as Markdown using pymupdf4llm.",
        epilog="Example: python -m pdf_extractor document.pdf -o output.md",
    )
    parser.add_argument(
        "input_pdf",
        type=Path,
        help="Path to the input PDF file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        metavar="FILE",
        help="Write extracted text to FILE (default: print to stdout)",
    )
    parser.add_argument(
        "--page-separators",
        action="store_true",
        help="Insert '--- end of page=n ---' between pages",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Show progress bar",
    )

    args = parser.parse_args()

    try:
        text = extract_text(
            args.input_pdf,
            output_path=args.output,
            page_separators=args.page_separators,
            show_progress=args.progress,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.output is None:
        print(text, end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
