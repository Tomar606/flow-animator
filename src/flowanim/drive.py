"""The run loop: submit each brief, wait for the clip, key it, file it.

This is the half that used to live in the browser. It runs here so that a run
survives you looking at something else — the extension drives its tab over the
debugger protocol, which does not care whether the tab is visible.

ONE CLIP AT A TIME, DELIBERATELY
--------------------------------
Several prompts could be queued at once and the finished clips matched up
afterwards by reversing DOM order. That is fine when every clip is the same
subject; here it would mean filing the wrong animation under a topic id, and a
wrong clip that is confidently labelled is worse than a missing one. So each
prompt is submitted alone and the clip is whichever media key Flow did not have
a moment ago.

WHAT COUNTS AS "THE CLIP"
-------------------------
Not "a new media key". Flow mints a key as soon as a generation is QUEUED and
renders it as an <img> while the render runs — it appears within seconds, far
too early to be a finished clip. Treating a new key as the clip does not merely
risk the wrong file, it reliably returns a still of a video that does not exist
yet. So the wait is for a key rendered by a <video>.
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from .briefs import Brief
from .bridge import FlowBridge, FlowError, settled
from .deliver import deliver, summarise

GENERATE_TIMEOUT = 900.0   # Flow takes minutes; a stuck queue takes forever
POLL_EVERY = 10.0
SETTLE_AFTER_SUBMIT = 3.0
DOWNLOAD_TIMEOUT = 600.0


class DriveError(RuntimeError):
    """A topic could not be generated. The run moves on to the next one."""


def load_selectors(path: Path) -> dict:
    """Read selectors.json, dropping the `_comment` documentation blocks.

    Flow is a Radix SPA with hashed class names and it WILL move. Every place
    the run touches its UI is in that one file so there is a single thing to
    edit when it does.
    """
    if not path.is_file():
        raise DriveError(
            f"no selectors file at {path}. It records every control this touches "
            f"in Flow's UI; without it there is nothing to click.")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


# ------------------------------------------------------------------- media --
def _media(bridge: FlowBridge) -> list[dict]:
    return bridge.call("list_media", timeout=60).get("media", [])


def _keys(bridge: FlowBridge) -> set[str]:
    return {m["key"] for m in _media(bridge)}


def _new_video(bridge: FlowBridge, before: set[str]) -> tuple[list[str], list[str]]:
    """New keys since `before`, split into playable videos and stills."""
    fresh = [m for m in _media(bridge) if m["key"] not in before]
    return (sorted(m["key"] for m in fresh if m.get("video")),
            sorted(m["key"] for m in fresh if not m.get("video")))


def _url(bridge: FlowBridge, key: str) -> str:
    for m in _media(bridge):
        if m["key"] == key:
            return m["url"]
    raise DriveError(f"media {key} vanished from the page before it could be downloaded")


# ------------------------------------------------------------- one generate --
def generate(bridge: FlowBridge, brief: Brief, sel: dict) -> str:
    """Submit one brief and block until Flow has a clip that was not there before."""
    bridge.call("attach", timeout=60)

    time.sleep(1.5)
    before = _keys(bridge)

    # Flow has no separate negative field, so the negative rides inside the
    # prompt under its own heading — the form the briefs were tuned against.
    text = f"{brief.prompt()}\n\nNEGATIVE: {brief.negative()}"

    bridge.set_status(stage="typing the prompt", detail=brief.title)
    bridge.call("set_prompt", text=text, selector=sel["prompt"], timeout=120)
    time.sleep(1.0)

    bridge.set_status(stage="submitting", detail=brief.title)
    if sel.get("generate_selector"):
        bridge.call("click", selector=sel["generate_selector"], timeout=60)
    else:
        # 'arrow_forward', the icon ligature — NOT 'create'. Two visible
        # controls contain the word Create and the shortest match is the
        # 'Add media' dialog trigger, which opens a dialog and submits nothing.
        bridge.call("click", text=sel["generate_text"], timeout=60)

    time.sleep(SETTLE_AFTER_SUBMIT)
    deadline = time.time() + GENERATE_TIMEOUT
    stills: list[str] = []
    while time.time() < deadline:
        left = int(deadline - time.time())
        bridge.set_status(stage="waiting for Flow to render",
                          detail=f"{brief.id} — up to {left // 60}m {left % 60}s left")
        vids, stills = _new_video(bridge, before)
        if vids:
            # Several at once means Flow returned variants; they are all this
            # prompt's output, so the first is as good as any.
            return vids[0]
        time.sleep(POLL_EVERY)

    if stills:
        raise DriveError(
            f"Flow queued {brief.id} but never produced a playable clip within "
            f"{GENERATE_TIMEOUT / 60:.0f} minutes — {len(stills)} placeholder(s) "
            f"appeared and none became a video. Check the tab: a generation that "
            f"fails part-way leaves its placeholder behind.")
    raise DriveError(
        f"Flow produced nothing for {brief.id} within {GENERATE_TIMEOUT / 60:.0f} "
        f"minutes. Check the tab: a generation that failed its own safety or quota "
        f"check shows an error in the UI and never emits a media URL.")


def fetch(bridge: FlowBridge, key: str, name: str) -> Path:
    """Download one media key through the browser session, into the inbox."""
    url = _url(bridge, key)

    # Clear the target name FIRST. Two things go wrong otherwise, and both file
    # a previous run's clip under this run's topic id: the browser appends
    # " (1)" rather than overwriting, and the wait below would find the stale
    # file already sitting there and return it as this generation's output —
    # instantly, and with nothing anywhere saying it was the wrong video.
    stale = [bridge.inbox_dir() / name, bridge.download_dir / name]
    for f in stale:
        try:
            f.unlink()
            print(f"        cleared stale {f}")
        except FileNotFoundError:
            pass
        except OSError as e:
            raise DriveError(f"could not clear {f} before downloading: {e}")

    bridge.set_status(stage="downloading", detail=name)
    got = bridge.call("download", url=url, filename=bridge.inbox_rel(name),
                      timeout=DOWNLOAD_TIMEOUT)

    # Where the browser says it put the file beats where we asked it to. Chrome
    # drops the subdirectory from `filename` some of the time — the same
    # relative path landed in the inbox on one call and in ~/Downloads on the
    # next — and waiting at the path we asked for turns a download that
    # completed perfectly into "the download never landed".
    candidates = []
    if got.get("path"):
        candidates.append(Path(got["path"]))
    candidates += [bridge.inbox_dir() / name, bridge.download_dir / name]

    for _ in range(30):
        src = next((c for c in candidates if c.is_file() and settled(c)), None)
        if src is not None:
            return src
        time.sleep(1.0)
    raise DriveError("the download never landed. Looked in:\n  "
                     + "\n  ".join(str(c) for c in candidates))


# ----------------------------------------------------------------- the run --
def run(briefs: list[Brief], bridge: FlowBridge, sel: dict, delivery: Path, *,
        make_preview: bool = True, similarity: float | None = None) -> int:
    """Generate every brief in turn. Returns a process exit code."""
    delivery.mkdir(parents=True, exist_ok=True)
    bridge.set_status(total=len(briefs), done=0)

    ok: list[str] = []
    failed: list[tuple[str, str]] = []

    for n, brief in enumerate(briefs, 1):
        print(f"\n  [{n}/{len(briefs)}] {brief.id}  —  {brief.title}")
        print(f"        on {brief.field_word}, up to {GENERATE_TIMEOUT / 60:.0f} min")
        bridge.set_status(topic=brief.id, stage="starting", detail=brief.title)
        try:
            key = generate(bridge, brief, sel)
            raw = fetch(bridge, key, f"{brief.id}.mp4")
            bridge.set_status(stage="keying", detail=brief.id)
            print(f"        keying {raw.name}…")
            rec = deliver(raw, brief, delivery,
                          make_preview=make_preview, similarity=similarity)
        except (DriveError, FlowError) as e:
            print(f"        ✗ {e}")
            failed.append((brief.id, str(e).split("\n")[0]))
            bridge.set_status(stage="failed", detail=f"{brief.id}: {e}")
            continue
        except Exception as e:                       # keep the run alive
            print(f"        ✗ unexpected: {e}")
            failed.append((brief.id, f"unexpected: {e}"))
            continue
        print(summarise(rec))
        ok.append(brief.id)
        bridge.set_status(done=len(ok), stage="delivered", detail=brief.id)

    print(f"\n  {len(ok)}/{len(briefs)} delivered → {delivery}")
    if failed:
        print("\n  Did not come back:")
        for tid, why in failed:
            print(f"    ✗ {tid:<16} {why}")
        print("\n  Re-run just those with:  ./run.sh run --only "
              + ",".join(t for t, _ in failed))
    else:
        print(f"  ✓ every topic delivered. Hand {delivery} to the video project.")
    bridge.set_status(stage="finished", topic=None,
                      detail=f"{len(ok)}/{len(briefs)} delivered")
    return 0 if not failed else 2
