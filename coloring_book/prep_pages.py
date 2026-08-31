#!/usr/bin/env python3
"""Print-prep for the Animal Coloring Book pages 1-10.

Input : coloring_book/raw/pageNN.png (AI-generated line art)
Output: coloring_book/final/pageNN.png  (A4 @ 300 DPI, pure black/white, framed)
        coloring_book/Animal_Coloring_Book_Pages_1-10.pdf (print-ready PDF, no cover)
"""
import glob, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

RAW = "raw"
OUT = "final"
W, H = 2480, 3508  # A4 @ 300 DPI
THRESHOLD = 160    # everything darker becomes black, lighter becomes white
FRAME_INSET = 45
FRAME_WIDTH = 12
SAFE = 95          # keep artwork at least this far from the page edges (inside the frame)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PAGE_FONT_SIZE = 110

os.makedirs(OUT, exist_ok=True)


def dilate(mask, k):
    """Grow the black mask by k 1-px layers (8-connectivity) via numpy shifts."""
    m = mask
    for _ in range(k):
        p = np.pad(m, 1, mode="constant", constant_values=False)
        m = (p[1:-1, 1:-1] | p[0:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, 0:-2] |
             p[1:-1, 2:] | p[0:-2, 0:-2] | p[0:-2, 2:] | p[2:, 0:-2] | p[2:, 2:])
    return m


def prepare(page_path, page_num):
    im = Image.open(page_path).convert("L")
    w, h = im.size
    scale = min(W / w, H / h, (W - 2 * SAFE) / w, (H - 2 * SAFE) / h)  # fit fully inside frame
    im = im.resize((int(round(w * scale)), int(round(h * scale))), Image.LANCZOS)
    a = np.array(im)

    black = a < THRESHOLD
    # remove isolated specks (median 3x3 on the binary mask)
    bimg = Image.fromarray((black * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(size=3))
    black = np.array(bimg) > 127
    # thicken thin/faint lines slightly so they survive printing with crayons/markers
    black = dilate(black, 2)

    # center on a pure-white A4 canvas
    canvas = np.ones((H, W), dtype=bool)
    hh, ww = black.shape
    y0, x0 = (H - hh) // 2, (W - ww) // 2
    canvas[y0:y0 + hh, x0:x0 + ww] = ~black

    img = Image.fromarray((canvas * 255).astype(np.uint8), mode="L")
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    # thin black border frame (classic coloring-book page frame)
    d.rectangle([FRAME_INSET, FRAME_INSET, W - FRAME_INSET - 1, H - FRAME_INSET - 1],
                outline=0, width=FRAME_WIDTH)
    # page number, centered in the bottom margin of the frame
    font = ImageFont.truetype(FONT_PATH, PAGE_FONT_SIZE)
    label = str(page_num)
    bbox = d.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (W - tw) / 2 - bbox[0]
    ty = H - FRAME_INSET - FRAME_WIDTH - th - 40 - bbox[1]
    d.text((tx, ty), label, font=font, fill=0)

    # final hard threshold: eliminate any anti-aliasing from text/frame drawing
    arr = np.array(img.convert("L"))
    arr = np.where(arr >= 128, 255, 0).astype(np.uint8)
    img = Image.fromarray(arr, mode="L").convert("RGB")
    img.info["dpi"] = (300, 300)
    out_path = os.path.join(OUT, f"page{page_num:02d}.png")
    img.save(out_path)
    return img, out_path, black


def main():
    finals = []
    print(f"{'page':6s} {'black%':>7s} {'ink bbox (x0,y0,x1,y1)':>30s}")
    for p in sorted(glob.glob(os.path.join(RAW, "page*.png"))):
        n = int(os.path.basename(p)[4:6])
        img, out_path, black = prepare(p, n)
        finals.append(img)
        nz = np.argwhere(black)
        bbox = (nz[:, 1].min(), nz[:, 0].min(), nz[:, 1].max(), nz[:, 0].max()) if len(nz) else None
        print(f"page{n:02d}  {black.mean()*100:6.2f}%  {bbox}")
    # assemble print-ready PDF (A4 pages, 300 DPI, no cover)
    pdf_path = "Animal_Coloring_Book_Pages_1-10.pdf"
    finals[0].save(pdf_path, save_all=True, append_images=finals[1:], resolution=300.0)
    print("PDF written:", pdf_path, os.path.getsize(pdf_path), "bytes")


if __name__ == "__main__":
    sys.exit(main())
