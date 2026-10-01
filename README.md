# Image Background Remover

A Python tool to remove backgrounds from images using rembg and U2-Net deep learning models. Supports CLI, GUI, and batch processing.

---

## Installation

```bash
pip install -r requirements.txt
```

*Note: On first execution, the model weights (~170 MB) will download automatically to `~/.u2net/`.*

---

## Quick Start

- **Launch GUI**: Double-click `run_gui.bat` or run:
  ```bash
  python bg_remover.py --gui
  ```
- **Run CLI**:
  ```bash
  python bg_remover.py input.jpg
  ```

---

## CLI Usage

### Syntax

```bash
python bg_remover.py [input] [-o OUTPUT] [--bg-color R G B] [--model MODEL] [--gui]
```

### Arguments

| Parameter | Description |
|---|---|
| `input` | Path to an image file or a directory of images |
| `-o`, `--output` | Destination file or directory path (default: `<name>_no_bg.png`) |
| `--bg-color R G B` | Replace background with RGB color (e.g. `255 255 255`) |
| `--model MODEL` | Model name (default: `u2net`) |
| `--gui` | Launch graphical interface |

### Examples

**Single image (transparent PNG output):**
```bash
python bg_remover.py photo.jpg
```

**Specify custom output path:**
```bash
python bg_remover.py photo.jpg -o result.png
```

**Replace background with solid white:**
```bash
python bg_remover.py photo.jpg --bg-color 255 255 255
```

**Batch process all images in a folder:**
```bash
python bg_remover.py ./photos/ -o ./results/
```

**Use a lightweight model for faster processing:**
```bash
python bg_remover.py photo.jpg --model u2netp
```

---

## GUI Usage

1. Run `python bg_remover.py --gui` or double-click `run_gui.bat`.
2. Click **Browse File** for a single image, or **Browse Folder** for batch mode.
3. Choose the output destination (optional; defaults to the source directory).
4. Select the background style:
   - **Transparent**
   - **White**
   - **Custom hex** (e.g., `#FFFFFF` or `#00FF00`)
5. Click **Remove Background**.

---

## Python API

You can import and use the tool directly in Python scripts:

```python
from pathlib import Path
from bg_remover import remove_background, batch_remove_background

# Single image
remove_background(
    input_path=Path("input.jpg"),
    output_path=Path("output.png"),
    bg_color=None  # Set (R, G, B, 255) for solid background
)

# Batch directory
batch_remove_background(
    input_dir=Path("./photos"),
    output_dir=Path("./results"),
    model_name="u2net"
)
```

---

## Available Models

| Model | Size | Best For |
|---|---|---|
| `u2net` | ~170 MB | Best overall quality (default) |
| `u2netp` | ~4 MB | Low-resource systems, high speed |
| `u2net_human_seg` | ~170 MB | Human portraits and hair detail |
| `isnet-general-use` | ~175 MB | General salient object segmentation |
| `silueta` | ~43 MB | Lightweight alternative for general use |

---

## Supported Formats

- **Input**: PNG, JPG, JPEG, BMP, TIFF, WEBP
- **Output**: PNG, WEBP (for transparency), JPG (when using `--bg-color`)

---

## Troubleshooting

- **GUI does not open when started remotely:** Run `python bg_remover.py --gui` directly from an interactive Windows Command Prompt / PowerShell window, or double-click `run_gui.bat`.
- **First run is slow:** The model weights are downloading from GitHub. Subsequent runs process images locally in 1-3 seconds.
- **Black background on JPG output:** JPG files do not support transparency. To keep transparency, save as `.png` or provide `--bg-color`.
