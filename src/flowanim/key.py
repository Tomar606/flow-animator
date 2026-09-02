"""Turn a clip generated on a chroma field into a clip with a real alpha channel.

The field is synthetic — Veo painted it, no lamp ever shone on it — which makes
this far easier than keying a filmed green screen. A single `chromakey` at a
sampled reference colour is enough, where footage of a lit screen needs two
hue keys at different value references to span the brightness range.

WHAT THIS CHECKS, AND WHY IT IS NOT OPTIONAL
--------------------------------------------
The expensive failure is not a bad key, it is a key that looks fine in the
thumbnail. `reference/biology/ovule/rejected_green_field_sac_keyed_out.png` is
the case: the embryo sac was drawn in the same green as the field, so keying
removed the middle of the ovule and left a diagram with a hole in it. Nothing
about the raw clip says so, and the alpha channel is invisible in most players.

So every clip is measured after keying:

  coverage        how much of the frame survived. Very low means the key ate the
                  drawing; very high means it did not fire at all.
  interior holes  transparent pixels enclosed by opaque ones on BOTH axes. This
                  is the sac-shaped failure, and it is the one worth stopping for.
  edge contact    opaque pixels touching the frame border, i.e. the drawing runs
                  off the edge — the framing clause in the brief was not obeyed
                  and the clip cannot be scaled or placed freely.

A clip that fails is still written out. You are told, you look, and you decide —
regenerating costs a credit and a false alarm is cheaper than a silent discard.
"""
from __future__ import annotations

import io
import json
import shutil
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from PIL import Image

# A pixel counts as opaque above this. The key's own `blend` produces a soft
# edge a few pixels wide; anything in between is edge, not subject.
OPAQUE = 160

# WHY `colorkey` AND NOT `chromakey`
# ---------------------------------
# `chromakey` compares only the chroma (U/V) components, which is right for a
# filmed green screen where the subject is lit unevenly. It is wrong here.
# These drawings are pastel and frequently share the field's HUE — a mint-green
# cell on a green field differs from it mainly in LUMA — and chromakey removed
# the entire drawing at the default tolerance while reporting nothing amiss.
# Measured on BIO-C2-LA-03: chromakey at 0.16 left a maximum alpha of 101 across
# the whole frame; colorkey at 0.22 keeps 17% of it opaque, which is the cells.
#
# `colorkey` compares full RGB distance, so luma counts. The field is synthetic
# and perfectly flat, which is exactly the case where an RGB-distance key is
# safe — the objection to it (an uneven screen needs a tolerance so wide it eats
# skin tones) does not apply to a colour Veo painted.
SIMILARITY = 0.16
BLEND = 0.06


class KeyError_(RuntimeError):
    """ffmpeg failed, or was not there to fail."""


def ffmpeg_or_die() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise KeyError_(
            "ffmpeg is not on PATH. Install it — macOS: `brew install ffmpeg`, "
            "Debian/Ubuntu: `sudo apt install ffmpeg`, Windows: `winget install "
            "Gyan.FFmpeg` — then run ./setup.sh again.")
    return exe


def _run(args: list[str], *, capture: bool = False) -> bytes:
    p = subprocess.run(args, capture_output=True)
    if p.returncode != 0:
        tail = p.stderr.decode("utf-8", "replace").strip().splitlines()[-6:]
        raise KeyError_("ffmpeg failed:\n  " + "\n  ".join(tail))
    return p.stdout if capture else b""


def duration(src: Path) -> float:
    exe = shutil.which("ffprobe")
    if not exe:
        return 0.0
    out = subprocess.run(
        [exe, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "format=duration", "-of", "csv=p=0", str(src)],
        capture_output=True).stdout.decode().strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def size(src: Path) -> tuple[int, int]:
    exe = shutil.which("ffprobe")
    if not exe:
        return (0, 0)
    out = subprocess.run(
        [exe, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0:s=x", str(src)],
        capture_output=True).stdout.decode().strip().split("x")
    try:
        return int(out[0]), int(out[1])
    except (ValueError, IndexError):
        return (0, 0)


def frame(src: Path, t: float, vf: str | None = None) -> Image.Image | None:
    """One frame as a PIL image, optionally through a filtergraph."""
    cmd = [ffmpeg_or_die(), "-v", "error", "-ss", f"{t:.3f}", "-i", str(src),
           "-frames:v", "1"]
    if vf:
        cmd += ["-vf", vf]
    cmd += ["-f", "image2pipe", "-vcodec", "png", "-"]
    raw = _run(cmd, capture=True)
    return Image.open(io.BytesIO(raw)) if raw else None


def sample_field(src: Path, fallback: str) -> str:
    """The field's actual colour, read from the corners of the first frame.

    Taking it from the clip rather than trusting the brief matters because Veo
    does not reproduce a named colour exactly, and a reference two hundred RGB
    units away from the real field leaves a fringe the despill cannot fix.
    """
    img = frame(src, 0.1)
    if img is None:
        return fallback
    a = np.asarray(img.convert("RGB")).astype(float)
    h, w = a.shape[:2]
    box = max(8, min(h, w) // 24)
    patches = [a[:box, :box], a[:box, -box:], a[-box:, :box], a[-box:, -box:]]
    per_corner = np.array([np.median(p.reshape(-1, 3), axis=0) for p in patches])
    med = np.median(per_corner, axis=0)

    # The guard has to measure how far the four CORNERS are from each other, not
    # how far the channels are from each other: a saturated chroma colour has a
    # huge channel spread by definition, and an earlier version of this check
    # rejected every field it was given and silently fell back to the default.
    if np.max(np.linalg.norm(per_corner - med, axis=1)) > 48:
        return fallback                # a title card, a fade-in, a lit corner
    med = med.astype(int)
    return "0x%02X%02X%02X" % tuple(med)


def graph(field_hex: str, despill: str, *,
          similarity: float = SIMILARITY, blend: float = BLEND) -> str:
    return (f"format=rgba,colorkey={field_hex}:{similarity}:{blend},"
            f"despill=type={despill}:mix=0.5:expand=0.3")


@dataclass
class Report:
    coverage: float          # 0..1, share of the frame that is opaque
    interior_holes: float    # 0..1, share of the frame enclosed but transparent
    edge_contact: float      # 0..1, share of the border row/col that is opaque
    verdict: str             # "ok" | one line saying what to do
    severity: str = "ok"     # "ok" | "look" | "fail"
    field_hex: str = ""

    @property
    def ok(self) -> bool:
        return self.severity == "ok"


def _holes(opaque: np.ndarray) -> float:
    """Transparent area that the frame border cannot reach — a real hole.

    The first version of this asked whether a transparent pixel had opaque
    pixels on both sides along its row AND its column. That is cheap and wrong:
    the ovule's stalk curves back alongside its body, and the perfectly ordinary
    background in the crook of that hook satisfies both tests. It reported 18%
    holes on a clip with none.

    A hole is background that is enclosed, and enclosure is connectivity, so
    this floods inward from the border and counts what it cannot reach. The mask
    is shrunk first: a hole worth stopping for is far larger than the shrink,
    and it turns an unbounded flood into a few hundred cheap array shifts.
    """
    h, w = opaque.shape
    step = max(1, max(h, w) // 320)
    bg = ~opaque[::step, ::step]
    if not bg.any():
        return 0.0

    reach = np.zeros_like(bg)
    reach[0, :] = bg[0, :]; reach[-1, :] = bg[-1, :]
    reach[:, 0] = bg[:, 0]; reach[:, -1] = bg[:, -1]
    while True:
        grown = reach.copy()
        grown[1:, :] |= reach[:-1, :]
        grown[:-1, :] |= reach[1:, :]
        grown[:, 1:] |= reach[:, :-1]
        grown[:, :-1] |= reach[:, 1:]
        grown &= bg
        if grown.sum() == reach.sum():
            break
        reach = grown
    return float((bg & ~reach).mean())


def _measure(alpha: np.ndarray) -> tuple[float, float, float]:
    m = alpha >= OPAQUE
    if not m.any():
        return 0.0, 0.0, 0.0
    border = np.concatenate([m[0], m[-1], m[:, 0], m[:, -1]])
    return m.mean(), _holes(m), border.mean()


def inspect(src: Path, field_hex: str, despill: str,
            *, samples: int = 3, **kw) -> Report:
    dur = duration(src) or 10.0
    times = [dur * f for f in (0.12, 0.5, 0.9)][:samples]
    vf = graph(field_hex, despill, **kw) + ",alphaextract"

    cov, hole, edge = [], [], []
    for t in times:
        img = frame(src, t, vf)
        if img is None:
            continue
        c, h, e = _measure(np.asarray(img.convert("L")))
        cov.append(c); hole.append(h); edge.append(e)
    if not cov:
        return Report(0, 0, 0, "could not read any frame back from ffmpeg", field_hex)

    coverage, holes, edges = max(cov), max(hole), max(edge)

    # Only two things are unambiguous from a number, and they are the two that
    # matter: nothing survived, or nothing was removed. Everything else is
    # reported and handed to your eyes.
    if coverage < 0.02:
        return Report(
            round(coverage, 4), round(holes, 4), round(edges, 4),
            "almost nothing survived the key. The drawing is the same colour as "
            "the field — regenerate on the other field.", "fail", field_hex)
    if coverage > 0.97:
        return Report(
            round(coverage, 4), round(holes, 4), round(edges, 4),
            "the key barely fired. The background is not a flat field — check the "
            "raw clip for a floor, a gradient or a fade-in.", "fail", field_hex)

    # Enclosed transparent area is NOT by itself a defect, and treating it as one
    # cries wolf on every clip with a spiral or a ring in it: the gaps between a
    # DNA helix's two backbones are enclosed background and perfectly correct.
    # It is a defect when the enclosed area is a piece of the drawing that was
    # painted in the field colour and has been keyed away — which looks identical
    # to a number and obvious in the preview. So this asks you to look.
    notes = []
    if holes > 0.02:
        notes.append(
            f"{holes:.1%} of the frame is background enclosed by the drawing. "
            f"Normal for a spiral, a ring or a curled tail; a defect if part of "
            f"the drawing was painted in the field colour and has been keyed away")
    if edges > 0.06:
        notes.append(
            f"the drawing touches the frame border ({edges:.0%} of it), so it runs "
            f"off the edge and cannot be scaled or placed freely")
    if notes:
        return Report(round(coverage, 4), round(holes, 4), round(edges, 4),
                      "open the preview — " + "; ".join(notes) + ".",
                      "look", field_hex)
    return Report(round(coverage, 4), round(holes, 4), round(edges, 4),
                  "ok", "ok", field_hex)


def to_alpha(src: Path, dst: Path, field_hex: str, despill: str, **kw) -> Path:
    """VP9 with a real alpha channel — the format the video project composites."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run([ffmpeg_or_die(), "-v", "error", "-y", "-i", str(src),
          "-vf", graph(field_hex, despill, **kw) + ",format=yuva420p",
          "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
          "-b:v", "0", "-crf", "26", "-row-mt", "1",
          "-auto-alt-ref", "0", str(dst)])
    return dst


def preview(src: Path, dst: Path, field_hex: str, despill: str, **kw) -> Path:
    """The keyed clip over flat slate, so a human can see the edge quality."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    w, h = size(src)
    if not w:
        raise KeyError_(f"ffprobe could not read the size of {src.name}")
    # `color` needs a concrete WxH — `s=iw:ih` is not a thing, and the parse
    # error it produces names the wrong filter entirely.
    fc = (f"color=c=0x1E2430:s={w}x{h}:d=1[bg];"
          f"[0:v]{graph(field_hex, despill, **kw)},format=yuva420p[fg];"
          f"[bg][fg]overlay=shortest=1,format=yuv420p")
    _run([ffmpeg_or_die(), "-v", "error", "-y", "-i", str(src),
          "-filter_complex", fc, "-c:v", "libx264", "-crf", "20",
          "-pix_fmt", "yuv420p", str(dst)])
    return dst


def last_frame(src: Path, dst: Path) -> Path:
    """The final frame, kept because it is what a follow-on clip is anchored to.

    A topic that needs more than ten seconds comes back as several generations
    and Veo remembers nothing between them, so the frame one clip ends on is
    what the next one is given as a reference.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    dur = duration(src)
    t = max(0.0, dur - 0.08) if dur else 0.0
    _run([ffmpeg_or_die(), "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(src),
          "-frames:v", "1", "-update", "1", str(dst)])
    return dst


def report_dict(r: Report) -> dict:
    d = asdict(r)
    d["ok"] = r.ok
    return d


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
