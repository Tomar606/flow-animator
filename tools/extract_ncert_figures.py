"""Extract every captioned figure from the NCERT Biology chapter PDFs.

    ./.venv/bin/pip install pymupdf          # not in requirements.txt: this is a
                                             # one-off, and its output is committed
    ./.venv/bin/python tools/extract_ncert_figures.py <pdf-dir> <out-dir>

WHY IT RENDERS REGIONS INSTEAD OF PULLING THE EMBEDDED IMAGES
-------------------------------------------------------------
`pdfimages` on these files returns a mixture of page-sized background rasters,
decorative rules, and figure fragments, with no way to tell which is which — and
it misses everything drawn as vector art, which is most of the line diagrams. It
also drops the labels, because those are live text sitting on top of the artwork.

So this finds the CAPTION and renders the page region above it. What comes out is
exactly what is printed, labels and all.

FINDING THE CAPTION IN A FONT THAT IS NOT UNICODE
-------------------------------------------------
These PDFs predate Unicode Devanagari — they were set in PageMaker with a legacy
8-bit font, so the text layer is mojibake and `"चित्र"` does not appear anywhere
in it. It comes out as `fp=k`, which is what the caption pattern matches. If a
future NCERT PDF is properly encoded, add the Unicode spelling to CAPTION.

The same encoding is why captions are not used as filenames: the bytes are not
text in any meaningful sense until they are rendered.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pymupdf

# "चित्र 1.5" in the legacy encoding, with either a dot or a hyphen separator.
CAPTION = re.compile(r"^(?:fp=k|चित्र)\s*(\d+)\s*[-.]\s*(\d+)")

MIN_ART_AREA = 400          # pt², below this it is a bullet or a rule
MAX_ART_FRACTION = 0.80     # above this it is a page background
FURNITURE_WIDTH = 0.92      # a box this wide is a banner, not a figure
HEADER_BAND = 95            # pt from the top: running head
FOOTER_BAND = 55            # pt from the bottom: folio
CONTIGUOUS_GAP = 28         # pt of white a figure may contain and stay one figure
LABEL_GAP = 20              # pt within which a short text block is a label
LABEL_CHARS = 80            # longer than this and it is body text, not a label
DPI = 200


def captions(page) -> list[tuple[str, pymupdf.Rect]]:
    out = []
    for b in page.get_text("blocks"):
        text = b[4].strip()
        m = CAPTION.match(text)
        rect = pymupdf.Rect(b[:4])
        # A body paragraph may open with a cross-reference to a figure. A real
        # caption is short and shallow; the paragraph is neither.
        if m and rect.height < 100 and len(text) < 400:
            out.append((f"{m.group(1)}.{m.group(2)}", rect))
    return out


def artwork(page) -> list[pymupdf.Rect]:
    pr = page.rect
    area = pr.get_area()
    rects = [pymupdf.Rect(i["bbox"]) for i in page.get_image_info()]
    rects += [pymupdf.Rect(d["rect"]) for d in page.get_drawings()]
    keep = []
    for r in rects:
        r = r & pr
        if r.is_empty or not (MIN_ART_AREA < r.get_area() < MAX_ART_FRACTION * area):
            continue
        if r.width > FURNITURE_WIDTH * pr.width:
            continue
        if r.y1 < HEADER_BAND or r.y0 > pr.height - FOOTER_BAND:
            continue
        keep.append(r)
    return keep


def labels(page) -> list[pymupdf.Rect]:
    return [pymupdf.Rect(b[:4]) for b in page.get_text("blocks")
            if len(b[4].strip()) <= LABEL_CHARS]


def grow(seed: pymupdf.Rect, parts: list[pymupdf.Rect], gap: float) -> pymupdf.Rect:
    """Absorb every part that touches the region, until nothing more does."""
    u = pymupdf.Rect(seed)
    changed = True
    while changed:
        changed = False
        for r in parts:
            if u.intersects(r) or (
                    min(u.x1, r.x1) - max(u.x0, r.x0) > 8 and
                    -gap < u.y0 - r.y1 < gap and r.y1 <= u.y1 + 2):
                merged = u | r
                if merged != u:
                    u, changed = merged, True
    return u


def region(page, caption: pymupdf.Rect) -> pymupdf.Rect | None:
    above = [r for r in artwork(page) if r.y1 <= caption.y1 + 2]
    if not above:
        return None
    above.sort(key=lambda r: -r.y1)              # nearest the caption first
    art_u = grow(above[0], above, CONTIGUOUS_GAP)

    # Labels sit on and around the artwork and are clipped off without this.
    # They are absorbed sideways only: every line of a body paragraph is also a
    # short text block, so letting them extend the region UPWARD chains straight
    # up the page and swallows the prose above the figure.
    near = [r for r in labels(page)
            if r.y1 <= caption.y1 + 2
            and r.x1 > art_u.x0 - 30 and r.x0 < art_u.x1 + 30
            and r.y1 > art_u.y0 - LABEL_GAP and r.y0 < art_u.y1 + LABEL_GAP]
    u = grow(art_u, near, LABEL_GAP)
    u.y0 = max(u.y0, art_u.y0 - 24)

    # A figure's image bbox is often padded with transparency far above the
    # drawing itself, and the body prose is laid out INSIDE that padding and
    # shows through it. The bbox is honest and useless. So the region is clamped
    # to start below the last paragraph it would otherwise contain: whatever
    # else a figure is, it is not three inches of running text.
    prose_bottom = 0.0
    for b in page.get_text("blocks"):
        r = pymupdf.Rect(b[:4])
        if (len(b[4].strip()) > LABEL_CHARS
                and r.width > 0.45 * page.rect.width
                and r.y1 < caption.y0
                and r.y1 > u.y0 and r.y0 < u.y1):
            prose_bottom = max(prose_bottom, r.y1)
    if prose_bottom and caption.y0 - prose_bottom > 60:
        u.y0 = max(u.y0, prose_bottom + 6)

    u |= caption
    u += (-8, -8, 8, 8)
    return u & page.rect


def chapter_number(pdf: Path) -> str:
    m = re.search(r"(\d{2})(\d)\.pdf$", pdf.name)      # lhbo1<NN>.pdf
    return m.group(0)[1:3].lstrip("0") or "0" if m else pdf.stem


def extract(pdf: Path, out: Path) -> list[str]:
    doc = pymupdf.open(pdf)
    made, seen = [], {}
    for pno in range(doc.page_count):
        page = doc[pno]
        for num, crect in captions(page):
            r = region(page, crect)
            if r is None or r.get_area() < 5000:
                continue
            # The same number can caption two panels; keep the larger render.
            name = f"fig-{num}.png"
            if name in seen and seen[name] >= r.get_area():
                continue
            seen[name] = r.get_area()
            dest = out / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            page.get_pixmap(clip=r, dpi=DPI).save(dest)
            made.append(f"{name}  p{pno + 1}  {int(r.width)}x{int(r.height)}pt")
    return made


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = Path(argv[1]).expanduser(), Path(argv[2]).expanduser()
    pdfs = sorted(src.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs in {src}")
        return 1
    total = 0
    for pdf in pdfs:
        ch = re.search(r"(\d+)\.pdf$", pdf.name)
        folder = dst / f"chapter-{int(ch.group(1)) % 100:02d}" if ch else dst / pdf.stem
        made = extract(pdf, folder)
        total += len(made)
        print(f"{pdf.name}  →  {folder.name}  ({len(made)} figures)")
    print(f"\n{total} figures from {len(pdfs)} chapters → {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
