"""
Step 1 of the app: PDF → structured JSON.

Run this first. Select a PDF (menu + event), extract text, then get structured JSON via Gemini.
Save the JSON (e.g. with "Save JSON…") and use it as input for Step 2: ui_enrich.py.
"""

import json
import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog, messagebox, scrolledtext

from pdf_extractor import extract_text
from text_cleaner import normalize_for_llm


def _apply_heading_styles(widget: scrolledtext.ScrolledText) -> None:
    """Style lines that look like Markdown headings (e.g. ## Title) with distinct fonts."""
    base = tkfont.nametofont("TkDefaultFont")
    base_family = base.cget("family")
    base_size = base.cget("size")
    for level in range(1, 7):
        size = base_size + (7 - level)
        widget.tag_configure(f"h{level}", font=(base_family, size, "bold"))

    content = widget.get("1.0", tk.END)
    for i, line in enumerate(content.split("\n"), start=1):
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            continue
        level = 0
        for c in stripped:
            if c == "#":
                level += 1
            else:
                break
        if 1 <= level <= 6 and level < len(stripped) and stripped[level] == " ":
            widget.tag_add(f"h{level}", f"{i}.0", f"{i}.end")


def main() -> None:
    # App run order: 1. ui_json_generation.py → 2. ui_enrich.py → 3. ui_image_generation.py
    root = tk.Tk()
    root.title("PDF Text Extractor")
    root.minsize(500, 400)
    root.geometry("700x500")

    selected_path: tk.StringVar = tk.StringVar(value="")

    def choose_file() -> None:
        path = filedialog.askopenfilename(
            title="Select a PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if path:
            selected_path.set(path)

    def do_extract() -> None:
        path = selected_path.get().strip()
        if not path:
            messagebox.showwarning("No file", "Please select a PDF file first.")
            return
        try:
            result_text.delete("1.0", tk.END)
            result_text.insert(tk.END, "Extracting…")
            root.update()
            text = extract_text(path, show_progress=False)
            text = normalize_for_llm(text)
            result_text.delete("1.0", tk.END)
            result_text.insert(tk.END, text)
            _apply_heading_styles(result_text)
        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e))
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def do_get_json() -> None:
        text = result_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning(
                "No text",
                "Extract text from a PDF first, then click Get JSON.",
            )
            return
        try:
            from receive_json import extract_structured_data

            data = extract_structured_data(text)
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            # Show in a new window with save option
            win = tk.Toplevel(root)
            win.title("Structured JSON")
            win.geometry("600x500")

            def save_json() -> None:
                path = filedialog.asksaveasfilename(
                    title="Save JSON as",
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                )
                if path:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(area.get("1.0", tk.END))
                    messagebox.showinfo("Saved", f"Saved to {path}")

            btn_save = tk.Button(win, text="Save JSON…", command=save_json)
            btn_save.pack(pady=(8, 4))

            area = scrolledtext.ScrolledText(win, wrap=tk.WORD, padx=8, pady=8)
            area.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
            area.insert(tk.END, json_str)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Step 1: select PDF, extract text, then "Get JSON" and save the JSON for Step 2
    frame = tk.Frame(root, padx=10, pady=10)
    frame.pack(fill=tk.X)

    tk.Button(frame, text="Select PDF…", command=choose_file).pack(side=tk.LEFT, padx=(0, 8))
    tk.Label(frame, textvariable=selected_path, foreground="gray").pack(side=tk.LEFT, fill=tk.X, expand=True)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=(0, 8))
    tk.Button(btn_frame, text="Extract text", command=do_extract).pack(side=tk.LEFT, padx=(0, 8))
    tk.Button(btn_frame, text="Get JSON", command=do_get_json).pack(side=tk.LEFT)

    # Result area
    result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, padx=8, pady=8)
    result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    root.mainloop()


if __name__ == "__main__":
    main()
