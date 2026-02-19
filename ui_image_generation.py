"""
Step 3 of the app: image prompt → generated image.

Run after Step 2 (ui_enrich.py). Paste the image prompt from Step 2 (or load from
image_prompt.txt), generate the image via Gemini, then view or save it.
"""

import io
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

from image_generation import generate_image


def main() -> None:
    root = tk.Tk()
    root.title("Image generation")
    root.minsize(500, 400)
    root.geometry("700x650")

    # Keep a reference so the image is not garbage-collected.
    current_photo: tk.PhotoImage | None = None
    current_image_bytes: bytes | None = None

    label_image = tk.Label(root, text="Generate an image to see it here.", bg="#e0e0e0")

    def do_generate() -> None:
        nonlocal current_photo, current_image_bytes
        prompt = prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Empty prompt", "Please enter a text prompt.")
            return
        label_image.config(image="", text="Generating…")
        root.update()
        try:
            image_bytes = generate_image(prompt)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            label_image.config(text="Generate an image to see it here.")
            return
        except Exception as e:
            err_msg = str(e)
            title = "Quota exceeded" if ("429" in err_msg or "quota" in err_msg.lower() or "resource_exhausted" in err_msg.lower()) else "Error"
            messagebox.showerror(title, err_msg)
            label_image.config(text="Generate an image to see it here.")
            return
        if not image_bytes:
            messagebox.showinfo("No image", "The model did not return an image (e.g. safety filter).")
            label_image.config(text="Generate an image to see it here.")
            current_photo = None
            current_image_bytes = None
            return
        current_image_bytes = image_bytes
        try:
            from PIL import Image
            image = Image.open(io.BytesIO(image_bytes))
            # Limit display size so the window stays manageable
            max_side = 500
            w, h = image.size
            if max(w, h) > max_side:
                ratio = max_side / max(w, h)
                image = image.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
            from PIL import ImageTk
            current_photo = ImageTk.PhotoImage(image)
            label_image.config(image=current_photo, text="")
        except Exception as e:
            messagebox.showerror("Error", f"Could not display image: {e}")
            label_image.config(text="Generate an image to see it here.")
            current_photo = None
            current_image_bytes = None

    def do_save() -> None:
        if not current_image_bytes:
            messagebox.showwarning("Nothing to save", "Generate an image first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save image",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("JPEG image", "*.jpg"), ("All files", "*.*")],
        )
        if not path:
            return
        Path(path).write_bytes(current_image_bytes)
        messagebox.showinfo("Saved", f"Saved to {path}")

    # Step 3: paste image prompt from Step 2, generate image, then save if desired
    top = tk.Frame(root, padx=10, pady=10)
    top.pack(fill=tk.X)
    tk.Label(top, text="Prompt", font=("", 10, "bold")).pack(anchor=tk.W)
    prompt_text = scrolledtext.ScrolledText(top, wrap=tk.WORD, height=6, padx=6, pady=6)
    prompt_text.pack(fill=tk.X, pady=(0, 8))
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=(0, 8))
    tk.Button(btn_frame, text="Generate image", command=do_generate).pack(side=tk.LEFT, padx=(0, 8))
    tk.Button(btn_frame, text="Save image…", command=do_save).pack(side=tk.LEFT)

    label_image.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
