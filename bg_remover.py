"""
Image Background Remover
========================
A Python tool to remove backgrounds from images using the rembg library.

Supports:
  - Single image processing
  - Batch processing of entire directories
  - Multiple output formats (PNG, WEBP)
  - Optional custom background colour replacement
  - CLI and GUI modes

Usage (CLI):
  python bg_remover.py input.jpg                       # output → input_no_bg.png
  python bg_remover.py input.jpg -o result.png         # explicit output path
  python bg_remover.py ./photos/ -o ./results/         # batch mode
  python bg_remover.py input.jpg --bg-color 255 0 0    # red background
  python bg_remover.py --gui                           # launch GUI

"""

from __future__ import annotations

import argparse
import sys
import time
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image
from rembg import remove, new_session

# Supported image extensions for batch mode
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


# ── Core logic ───────────────────────────────────────────────────────────────


def remove_background(
    input_path: Path,
    output_path: Optional[Path] = None,
    bg_color: Optional[Tuple[int, int, int, int]] = None,
    model_name: str = "u2net",
    session=None,
) -> Path:
    """Remove the background from a single image and save the result.

    Args:
        input_path:  Path to the source image.
        output_path: Where to write the result.  Defaults to
                     ``<stem>_no_bg.png`` next to the original.
        bg_color:    Optional RGBA tuple to composite behind the subject
                     instead of leaving it transparent.
        model_name:  rembg model name (default ``u2net``).
        session:     Pre-created rembg session for batch reuse.

    Returns:
        The resolved *output_path* that was written.
    """
    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_no_bg.png")
    output_path = Path(output_path)

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Read & process
    with open(input_path, "rb") as f:
        input_bytes = f.read()

    if session is None:
        session = new_session(model_name)

    result_bytes = remove(input_bytes, session=session)
    result_image = Image.open(BytesIO(result_bytes)).convert("RGBA")

    # Optionally composite onto a coloured background
    if bg_color is not None:
        bg = Image.new("RGBA", result_image.size, bg_color)
        bg.paste(result_image, mask=result_image)
        result_image = bg

    # Save (choose format based on extension)
    ext = output_path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        result_image = result_image.convert("RGB")
    result_image.save(output_path)

    return output_path


def batch_remove_background(
    input_dir: Path,
    output_dir: Optional[Path] = None,
    bg_color: Optional[Tuple[int, int, int, int]] = None,
    model_name: str = "u2net",
) -> list[Path]:
    """Process every supported image in *input_dir*.

    Returns a list of output paths that were written.
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    if output_dir is None:
        output_dir = input_dir / "no_bg"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(
        p for p in input_dir.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not images:
        print(f"No supported images found in {input_dir}")
        return []

    # Reuse one session across all images for speed
    session = new_session(model_name)
    results: list[Path] = []

    for idx, img_path in enumerate(images, 1):
        out_path = output_dir / f"{img_path.stem}_no_bg.png"
        print(f"  [{idx}/{len(images)}] {img_path.name} → {out_path.name} ...", end=" ", flush=True)
        t0 = time.perf_counter()
        remove_background(img_path, out_path, bg_color=bg_color, session=session)
        elapsed = time.perf_counter() - t0
        print(f"done ({elapsed:.1f}s)")
        results.append(out_path)

    return results


# ── GUI ──────────────────────────────────────────────────────────────────────


def launch_gui() -> None:
    """Launch a minimal Tkinter GUI for interactive background removal."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from threading import Thread

    root = tk.Tk()
    root.title("Image Background Remover")
    root.geometry("600x420")
    root.resizable(False, False)

    # ── State ──
    input_var = tk.StringVar()
    output_var = tk.StringVar()
    bg_color_var = tk.StringVar(value="transparent")
    hex_color_var = tk.StringVar(value="#FFFFFF")
    status_var = tk.StringVar(value="Ready")

    # ── Layout ──
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    # Input
    ttk.Label(frame, text="Input image / folder:").grid(row=0, column=0, sticky="w")
    ttk.Entry(frame, textvariable=input_var, width=50).grid(row=1, column=0, sticky="ew", padx=(0, 5))
    ttk.Button(
        frame, text="Browse File",
        command=lambda: input_var.set(
            filedialog.askopenfilename(
                title="Select Image",
                filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"), ("All", "*.*")],
            )
        ),
    ).grid(row=1, column=1)
    ttk.Button(
        frame, text="Browse Folder",
        command=lambda: input_var.set(filedialog.askdirectory(title="Select Folder")),
    ).grid(row=1, column=2)

    # Output
    ttk.Label(frame, text="Output path (optional):").grid(row=2, column=0, sticky="w", pady=(10, 0))
    ttk.Entry(frame, textvariable=output_var, width=50).grid(row=3, column=0, sticky="ew", padx=(0, 5))
    ttk.Button(
        frame, text="Browse",
        command=lambda: output_var.set(
            filedialog.asksaveasfilename(
                title="Save As",
                defaultextension=".png",
                filetypes=[("PNG", "*.png"), ("WEBP", "*.webp"), ("JPEG", "*.jpg")],
            )
        ),
    ).grid(row=3, column=1)

    # Background colour option
    ttk.Label(frame, text="Background:").grid(row=4, column=0, sticky="w", pady=(10, 0))
    bg_frame = ttk.Frame(frame)
    bg_frame.grid(row=5, column=0, columnspan=3, sticky="w")
    ttk.Radiobutton(bg_frame, text="Transparent", variable=bg_color_var, value="transparent").pack(side="left")
    ttk.Radiobutton(bg_frame, text="White", variable=bg_color_var, value="white").pack(side="left", padx=10)
    ttk.Radiobutton(bg_frame, text="Custom hex:", variable=bg_color_var, value="custom").pack(side="left", padx=10)
    ttk.Entry(bg_frame, textvariable=hex_color_var, width=10).pack(side="left")

    # Progress bar
    progress = ttk.Progressbar(frame, mode="indeterminate")
    progress.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(15, 5))

    # Status
    ttk.Label(frame, textvariable=status_var, foreground="gray").grid(row=7, column=0, columnspan=3, sticky="w")

    def _parse_bg_color():
        choice = bg_color_var.get()
        if choice == "transparent":
            return None
        if choice == "white":
            return (255, 255, 255, 255)
        # custom hex
        h = hex_color_var.get().lstrip("#")
        if len(h) != 6:
            raise ValueError("Hex colour must be 6 characters, e.g. #FF00AA")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r, g, b, 255)

    def _run():
        src = input_var.get().strip()
        dst = output_var.get().strip() or None
        if not src:
            messagebox.showwarning("Missing input", "Please select an input image or folder.")
            return

        try:
            bg = _parse_bg_color()
        except ValueError as exc:
            messagebox.showerror("Invalid colour", str(exc))
            return

        progress.start(10)
        status_var.set("Processing …")
        root.update_idletasks()

        def _work():
            try:
                src_path = Path(src)
                if src_path.is_dir():
                    results = batch_remove_background(src_path, Path(dst) if dst else None, bg_color=bg)
                    root.after(0, lambda: status_var.set(f"Done — {len(results)} images processed."))
                else:
                    out = remove_background(src_path, Path(dst) if dst else None, bg_color=bg)
                    root.after(0, lambda: status_var.set(f"Saved → {out}"))
            except Exception as exc:
                root.after(0, lambda: messagebox.showerror("Error", str(exc)))
                root.after(0, lambda: status_var.set("Error"))
            finally:
                root.after(0, progress.stop)

        Thread(target=_work, daemon=True).start()

    ttk.Button(frame, text="🚀  Remove Background", command=_run).grid(
        row=8, column=0, columnspan=3, pady=(15, 0)
    )

    root.mainloop()


# ── CLI ──────────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove backgrounds from images using AI (rembg / U²-Net)."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to an image file or a directory of images.",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file or directory path. Defaults to <name>_no_bg.png.",
    )
    parser.add_argument(
        "--bg-color",
        nargs=3,
        type=int,
        metavar=("R", "G", "B"),
        help="Replace transparent background with an RGB colour (0-255 each).",
    )
    parser.add_argument(
        "--model",
        default="u2net",
        help="rembg model name (default: u2net). Options include u2net, u2netp, u2net_human_seg, silueta, isnet-general-use, etc.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the graphical interface.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if args.gui:
        launch_gui()
        return

    if args.input is None:
        print("Error: please provide an input path or use --gui.\n")
        parse_args(["--help"])
        sys.exit(1)

    bg_color = None
    if args.bg_color:
        r, g, b = args.bg_color
        bg_color = (r, g, b, 255)

    src = Path(args.input)
    dst = Path(args.output) if args.output else None

    if src.is_dir():
        print(f"Batch mode: processing images in {src} …")
        results = batch_remove_background(src, dst, bg_color=bg_color, model_name=args.model)
        print(f"\n✅ Done — {len(results)} images saved.")
    elif src.is_file():
        print(f"Processing {src.name} …", end=" ", flush=True)
        t0 = time.perf_counter()
        out = remove_background(src, dst, bg_color=bg_color, model_name=args.model)
        elapsed = time.perf_counter() - t0
        print(f"done ({elapsed:.1f}s)")
        print(f"✅ Saved → {out}")
    else:
        print(f"Error: {src} is not a valid file or directory.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
