"""
Generates the 10 local placeholder tower images used by the Tower 1-10 cards.

The project's real YOLO dataset (data/raw -> data/interim/annotation/images)
is not present on this machine, so these stand in as clearly-synthetic
placeholders. They are drawn locally with Pillow -- nothing is downloaded and
no external URL is used. Re-run this script once the real dataset is
available to swap in actual samples.

Each image is a flat, on-theme backdrop with a two-tone tower silhouette and
a dashed YOLO-style bounding box, so the cards read as detection output.
"""
import os
from PIL import Image, ImageDraw

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "img", "opt")

# matches the light-theme tokens in src/app/globals.css
BG_TOP = (237, 232, 223)      # --backgroundTexture
BG_BOTTOM = (255, 253, 250)   # --surface
INK = (16, 29, 70)            # --cta / --onbackground
ACCENT = (72, 87, 200)        # --accent
MUTED = (120, 132, 175)

W, H = 828, 480
W_SMALL = 640


def monopole(draw, cx, base, top):
    """Single tapered shaft with a head platform."""
    half_base, half_top = 26, 9
    draw.polygon(
        [(cx - half_base, base), (cx + half_base, base),
         (cx + half_top, top + 46), (cx - half_top, top + 46)],
        fill=INK,
    )
    draw.rectangle([cx - 46, top + 40, cx + 46, top + 50], fill=INK)
    draw.line([cx, top + 50, cx, top], fill=INK, width=7)
    draw.ellipse([cx - 9, top - 6, cx + 9, top + 10], fill=INK)


def supporting(draw, cx, base, top):
    """Wide base with a central body and cross bracing."""
    half_base, half_top = 44, 15
    draw.polygon(
        [(cx - half_base, base), (cx + half_base, base),
         (cx + half_top, top + 60), (cx - half_top, top + 60)],
        fill=INK,
    )
    # cross bracing
    steps = 6
    for i in range(steps):
        y0 = base - (base - (top + 60)) * (i / steps)
        y1 = base - (base - (top + 60)) * ((i + 1) / steps)
        span0 = half_base - (half_base - half_top) * (i / steps)
        span1 = half_base - (half_base - half_top) * ((i + 1) / steps)
        draw.line([cx - span0, y0, cx + span1, y1], fill=MUTED, width=5)
        draw.line([cx + span0, y0, cx - span1, y1], fill=MUTED, width=5)
    draw.rectangle([cx - 58, top + 54, cx + 58, top + 64], fill=INK)
    draw.line([cx, top + 64, cx, top], fill=INK, width=7)
    draw.ellipse([cx - 9, top - 6, cx + 9, top + 10], fill=INK)


DRAWERS = [monopole, supporting]


def render(index, width):
    img = Image.new("RGB", (width, int(H * width / W)), BG_BOTTOM)
    d = ImageDraw.Draw(img)
    h = img.height

    # vertical gradient backdrop
    for y in range(h):
        t = y / max(h - 1, 1)
        d.line(
            [(0, y), (width, y)],
            fill=tuple(round(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)),
        )

    # faint survey grid
    for gx in range(0, width, 60):
        d.line([(gx, 0), (gx, h)], fill=(231, 226, 217))
    for gy in range(0, h, 60):
        d.line([(0, gy), (width, gy)], fill=(231, 226, 217))

    cx = width // 2 + ((index % 3) - 1) * (width // 6)
    base = int(h * 0.88)
    top = int(h * 0.10)
    DRAWERS[index % 2](d, cx, base, top)

    # dashed YOLO-style detection box
    pad_x, pad_y = 54, 34
    x0, y0, x1, y1 = cx - pad_x, top - pad_y, cx + pad_x, base + 18
    dash, gap = 16, 10
    for x in range(x0, x1, dash + gap):
        d.line([(x, y0), (min(x + dash, x1), y0)], fill=ACCENT, width=4)
        d.line([(x, y1), (min(x + dash, x1), y1)], fill=ACCENT, width=4)
    for y in range(y0, y1, dash + gap):
        d.line([(x0, y), (x0, min(y + dash, y1))], fill=ACCENT, width=4)
        d.line([(x1, y), (x1, min(y + dash, y1))], fill=ACCENT, width=4)

    # corner ticks
    tick = 26
    for (px, py, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(px, py), (px + dx * tick, py)], fill=INK, width=6)
        d.line([(px, py), (px, py + dy * tick)], fill=INK, width=6)

    return img


if __name__ == "__main__":
    out = os.path.normpath(OUT_DIR)
    os.makedirs(out, exist_ok=True)
    for i in range(1, 11):
        slug = "tower-%02d" % i
        for width in (W_SMALL, W):
            path = os.path.join(out, f"{slug}-{width}.png")
            render(i, width).save(path, "PNG", optimize=True)
            print("wrote", path)
