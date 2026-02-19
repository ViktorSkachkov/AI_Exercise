"""
Step 2 of the app: JSON → marketing summary + image prompt.

Run after Step 1 (ui_json_generation.py). Select the JSON file you saved from Step 1;
Gemini returns a short marketing summary and an image prompt. Save these (e.g. summary.txt,
image_prompt.txt) and use the image prompt in Step 3: ui_image_generation.py.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

from enrich_from_json import generate_summary_and_prompt, load_json


def main() -> None:
    root = tk.Tk()
    root.title("Enrich from JSON")
    root.minsize(500, 450)
    root.geometry("700x600")

    selected_path: tk.StringVar = tk.StringVar(value="")

    def choose_file() -> None:
        path = filedialog.askopenfilename(
            title="Select menu+event JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            selected_path.set(path)

    def do_generate() -> None:
        path_str = selected_path.get().strip()
        if not path_str:
            messagebox.showwarning("No file", "Please select a JSON file first.")
            return
        path = Path(path_str)
        if not path.exists():
            messagebox.showerror("Error", f"File not found: {path}")
            return
        try:
            summary_text.delete("1.0", tk.END)
            summary_text.insert(tk.END, "Generating…")
            prompt_text.delete("1.0", tk.END)
            root.update()
            data = load_json(path)
            result = generate_summary_and_prompt(data)
            summary_text.delete("1.0", tk.END)
            summary_text.insert(tk.END, result["marketing_summary"])
            prompt_text.delete("1.0", tk.END)
            prompt_text.insert(tk.END, result["image_prompt"])
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def do_save() -> None:
        summary = summary_text.get("1.0", tk.END).strip()
        image_prompt = prompt_text.get("1.0", tk.END).strip()
        if not summary and not image_prompt:
            messagebox.showwarning("Nothing to save", "Generate first.")
            return
        dir_path = filedialog.askdirectory(title="Choose folder to save summary.txt and image_prompt.txt")
        if not dir_path:
            return
        out = Path(dir_path)
        if summary:
            (out / "summary.txt").write_text(summary, encoding="utf-8")
        if image_prompt:
            (out / "image_prompt.txt").write_text(image_prompt, encoding="utf-8")
        messagebox.showinfo("Saved", f"Saved to {out}")

    # Step 2: select the JSON from Step 1, then generate summary + image prompt for Step 3
    frame = tk.Frame(root, padx=10, pady=10)
    frame.pack(fill=tk.X)
    tk.Button(frame, text="Select JSON…", command=choose_file).pack(side=tk.LEFT, padx=(0, 8))
    tk.Label(frame, textvariable=selected_path, foreground="gray").pack(side=tk.LEFT, fill=tk.X, expand=True)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=(0, 8))
    tk.Button(btn_frame, text="Generate summary & image prompt", command=do_generate).pack(side=tk.LEFT, padx=(0, 8))
    tk.Button(btn_frame, text="Save to files…", command=do_save).pack(side=tk.LEFT)

    # Two output areas
    content = tk.Frame(root, padx=10, pady=10)
    content.pack(fill=tk.BOTH, expand=True)

    tk.Label(content, text="Marketing summary", font=("", 10, "bold")).pack(anchor=tk.W)
    summary_text = scrolledtext.ScrolledText(content, wrap=tk.WORD, height=5, padx=6, pady=6)
    summary_text.pack(fill=tk.X, pady=(0, 12))

    tk.Label(content, text="Image prompt", font=("", 10, "bold")).pack(anchor=tk.W)
    prompt_text = scrolledtext.ScrolledText(content, wrap=tk.WORD, height=8, padx=6, pady=6)
    prompt_text.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
