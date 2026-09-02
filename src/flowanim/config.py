"""Where things live. `config.json` overrides the defaults; the CLI overrides both."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DEFAULTS = {
    "topics": "topics/biology_class12.py",
    "delivery": "delivery",
    "inbox": "~/Downloads/flow_inbox",
    "port": 8765,
    "preview": True,
    "similarity": None,          # None = the tuned default in key.py
}


def load(path: Path | None = None) -> dict:
    cfg = dict(DEFAULTS)
    path = path or ROOT / "config.json"
    if path.exists():
        try:
            cfg.update(json.loads(path.read_text()))
        except json.JSONDecodeError as e:
            raise SystemExit(f"{path} is not valid JSON: {e}")
    return cfg


def resolve(value: str, *, base: Path = ROOT) -> Path:
    """Repo-relative unless absolute or under ~."""
    p = Path(value).expanduser()
    return p if p.is_absolute() else (base / p)
