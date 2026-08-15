"""
Regenerates the app's square logo assets from logo.png.

logo.png is the only properly cut-out source: logo_rect.png is the same
image, and everything else shipped as an opaque tile, which is why the
tray and the title bar showed a coloured square behind Sid.

Run from the project root:

    python tools/make_logos.py

Outputs (overwritten): logo.ico, logo_sq.png.
"""

import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "logo.png")

# Windows picks a different one per context: 16 in the title bar, 32 in the
# taskbar, 256 in Explorer's large view. Shipping them all avoids Windows
# rescaling a wrong-sized frame into something blurry.
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
PNG_SIZE = 512


def square(image):
    """Crops to the visible pixels, then centres them on a transparent
    square — the logo is wider than it is tall, and every icon slot is
    square, so without this the image gets stretched."""
    image = image.convert("RGBA")
    bbox = image.getchannel("A").getbbox() or image.getbbox()
    image = image.crop(bbox)

    side = max(image.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas


def main():
    if not os.path.exists(SOURCE):
        print(f"Source introuvable : {SOURCE}", file=sys.stderr)
        return 1

    base = square(Image.open(SOURCE))

    ico_path = os.path.join(ROOT, "logo.ico")
    base.resize((256, 256), Image.LANCZOS).save(
        ico_path, format="ICO", sizes=[(s, s) for s in ICO_SIZES]
    )
    print(f"écrit {ico_path} ({', '.join(str(s) for s in ICO_SIZES)})")

    png_path = os.path.join(ROOT, "logo_sq.png")
    base.resize((PNG_SIZE, PNG_SIZE), Image.LANCZOS).save(png_path)
    print(f"écrit {png_path} ({PNG_SIZE}x{PNG_SIZE})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
