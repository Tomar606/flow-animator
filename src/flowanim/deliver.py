"""What lands in the delivery folder, and the shape the video project reads.

One directory per topic, named by the topic id, holding everything that topic
produced plus the record of how it was produced. The video project should read
`manifest.json` and never guess at filenames.

    delivery/
      manifest.json               every topic, its status and its files
      BIO-C1-LA-01/
        BIO-C1-LA-01_alpha.webm   ← composite THIS. VP9, real alpha channel.
        BIO-C1-LA-01_raw.mp4      what Flow returned, chroma field and all
        BIO-C1-LA-01_last.png     final frame, for anchoring a follow-on clip
        BIO-C1-LA-01_preview.mp4  the keyed clip over slate, for eyeballing
        BIO-C1-LA-01.json         brief, prompt, key report, checks to confirm

The raw clip is kept deliberately. Keying is cheap and repeatable; a Flow
generation is a credit and a wait. If the key needs retuning later, retune it
from the raw rather than generating the topic again.
"""
from __future__ import annotations

import datetime as _dt
import json
import shutil
from pathlib import Path

from .briefs import Brief
from . import key as keyer

MANIFEST = "manifest.json"


def _now() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def deliver(raw: Path, brief: Brief, outdir: Path, *,
            make_preview: bool = True, similarity: float | None = None) -> dict:
    """Key one raw clip and write the topic's whole delivery directory."""
    d = outdir / brief.id
    d.mkdir(parents=True, exist_ok=True)
    kw = {} if similarity is None else {"similarity": similarity}

    raw_dst = d / f"{brief.id}_raw.mp4"
    if raw.resolve() != raw_dst.resolve():
        shutil.copy2(raw, raw_dst)

    despill = brief.field_word                      # "green" or "blue"
    field_hex = keyer.sample_field(raw_dst, brief.field_hex)

    report = keyer.inspect(raw_dst, field_hex, despill, **kw)
    alpha = keyer.to_alpha(raw_dst, d / f"{brief.id}_alpha.webm", field_hex, despill, **kw)
    last = keyer.last_frame(raw_dst, d / f"{brief.id}_last.png")
    prev = (keyer.preview(raw_dst, d / f"{brief.id}_preview.mp4", field_hex, despill, **kw)
            if make_preview else None)

    record = {
        "id": brief.id,
        "title": brief.title,
        "generated": _now(),
        "field": brief.field,
        "field_hex_sampled": field_hex,
        "aspect": brief.aspect,
        "duration_s": round(keyer.duration(raw_dst), 2),
        "status": {"ok": "ok", "look": "check", "fail": "regenerate"}[report.severity],
        "key_report": keyer.report_dict(report),
        # Confirm these against the preview before the clip goes in a video.
        # They are the per-topic version of "what would make this wrong", and
        # they are the only part of the process a model cannot do for you.
        "checks": brief.checks,
        "notes": brief.notes,
        "files": {
            "alpha": alpha.name,
            "raw": raw_dst.name,
            "last_frame": last.name,
            "preview": prev.name if prev else None,
        },
        "prompt": brief.prompt(),
        "negative": brief.negative(),
    }
    keyer.write_json(d / f"{brief.id}.json", record)
    update_manifest(outdir, record)
    return record


def update_manifest(outdir: Path, record: dict) -> Path:
    path = outdir / MANIFEST
    data = {"schema": 1, "updated": _now(), "topics": {}}
    if path.exists():
        try:
            data.update(json.loads(path.read_text()))
        except json.JSONDecodeError:
            pass                       # a corrupt manifest is rebuilt, not fatal
    data["updated"] = _now()
    data.setdefault("topics", {})[record["id"]] = {
        k: record[k] for k in
        ("title", "status", "field", "duration_s", "generated", "files", "checks")
    }
    data["topics"][record["id"]]["dir"] = record["id"]
    keyer.write_json(path, data)
    return path


def summarise(record: dict) -> str:
    r = record["key_report"]
    head = f"{record['id']}  {record['title']}"
    body = (f"    coverage {r['coverage']:.1%}  holes {r['interior_holes']:.2%}  "
            f"edge {r['edge_contact']:.0%}")
    if record["status"] == "ok":
        return f"  ✓ {head}\n{body}"
    mark = "?" if record["status"] == "check" else "✗"
    return f"  {mark} {head}\n{body}\n    {r['verdict']}"
