"""The local half of the bridge: serve the prompts, watch for the clips.

The browser extension is the other half. It cannot reach your filesystem and
this cannot reach your logged-in Google session, so they meet over loopback:

    GET  /prompts   the topic list, each with its prompt and negative
    POST /status    the extension saying where it has got to
    GET  /health    build handshake, used by setup.sh and by the panel

Nothing here talks to Google. The extension drives the real browser you are
already signed into, which is the entire point: Flow is covered by a Google AI
subscription but is UI-only, and the API bills separately.

WHY THE BUILD NUMBER
--------------------
A Chrome extension has no hot reload. An extension left running from before an
edit fails exactly like a Flow redesign — wrong element, no error, nothing in
the log — and two whole debugging sessions were lost to that before this
handshake existed. `EXPECTED_BUILD` here must match `BRIDGE_BUILD` in
`extension/background.js`; bump both whenever the protocol between them changes.
"""
from __future__ import annotations

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .briefs import Brief
from .deliver import deliver, summarise

EXPECTED_BUILD = 1          # must match BRIDGE_BUILD in extension/background.js

# A file is considered finished once its size has held still for this long.
# Chrome writes the .crdownload first, but a same-name overwrite can still be
# caught mid-write, and a truncated mp4 keys to garbage rather than failing.
SETTLE_S = 1.5
POLL_S = 2.0


class Job:
    """The briefs being served, and what has come back so far."""

    def __init__(self, briefs: list[Brief], inbox: Path, delivery: Path,
                 *, make_preview: bool = True, similarity: float | None = None):
        self.briefs = briefs
        self.by_id = {b.id: b for b in briefs}
        self.inbox = inbox
        self.delivery = delivery
        self.make_preview = make_preview
        self.similarity = similarity
        self.seen: dict[str, tuple[int, float]] = {}
        self.done: list[str] = []
        self.lock = threading.Lock()

    def payload(self) -> dict:
        return {
            "build": EXPECTED_BUILD,
            "count": len(self.briefs),
            "delivery": str(self.delivery),
            "inbox_name": self.inbox.name,
            "topics": [
                {"index": i + 1, **b.as_dict()} for i, b in enumerate(self.briefs)
            ],
        }

    # -- resolving a downloaded file back to the topic that asked for it ------
    def match(self, filename: str) -> Brief | None:
        """`BIO-C1-LA-01.mp4`, `BIO-C1-LA-01 (1).mp4` and `clip_03.mp4` all resolve.

        Chrome appends ` (1)` when a name is taken and the extension cannot stop
        it, so the suffix is stripped rather than fought. `clip_NN` is the
        fallback the panel uses when a download arrives without a topic name.
        """
        stem = Path(filename).stem
        if stem.endswith(")") and " (" in stem:
            stem = stem[:stem.rindex(" (")]
        if stem in self.by_id:
            return self.by_id[stem]
        if stem.startswith("clip_"):
            try:
                n = int(stem[5:])
            except ValueError:
                return None
            if 1 <= n <= len(self.briefs):
                return self.briefs[n - 1]
        return None


class Handler(BaseHTTPRequestHandler):
    job: Job = None            # set on the server instance below

    def _send(self, code: int, body: bytes, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # The extension is exempt from CORS through its own host_permissions;
        # this is here so a plain browser tab can hit /health while debugging.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, b"")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/prompts", "/topics"):
            self._send(200, json.dumps(self.job.payload(), ensure_ascii=False).encode())
        elif path == "/health":
            self._send(200, json.dumps({
                "ok": True, "build": EXPECTED_BUILD,
                "topics": len(self.job.briefs),
                "delivered": len(self.job.done),
            }).encode())
        else:
            self._send(200, b"flow-animator bridge", "text/plain")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            msg = {"raw": raw[:200].decode("utf-8", "replace")}
        if msg.get("build") not in (None, EXPECTED_BUILD):
            print(f"[bridge] ! extension is build {msg.get('build')}, this bridge "
                  f"expects {EXPECTED_BUILD} — reload the extension at "
                  f"chrome://extensions and hard-reload the Flow tab.")
        state = msg.get("state", "?")
        who = msg.get("topic") or msg.get("id") or ""
        print(f"[panel]  {state} {who}".rstrip())
        self._send(200, b"{}")

    def log_message(self, *a):
        pass                                   # the panel messages are the log


def _stable(path: Path) -> bool:
    try:
        a = path.stat()
        time.sleep(SETTLE_S)
        b = path.stat()
    except OSError:
        return False
    return a.st_size == b.st_size and b.st_size > 4096


def watch(job: Job, *, once: bool = False) -> None:
    job.inbox.mkdir(parents=True, exist_ok=True)
    job.delivery.mkdir(parents=True, exist_ok=True)
    print(f"[watch]  {job.inbox}  →  {job.delivery}")
    while True:
        for f in sorted(job.inbox.iterdir()):
            if f.suffix.lower() not in (".mp4", ".webm", ".mov"):
                continue
            brief = job.match(f.name)
            if brief is None:
                continue
            try:
                st = f.stat()
            except OSError:
                continue
            fingerprint = (st.st_size, st.st_mtime)
            with job.lock:
                if job.seen.get(f.name) == fingerprint:
                    continue
            if not _stable(f):
                continue
            with job.lock:
                job.seen[f.name] = fingerprint
            print(f"[watch]  {f.name} → {brief.id}, keying…")
            try:
                rec = deliver(f, brief, job.delivery,
                              make_preview=job.make_preview,
                              similarity=job.similarity)
            except Exception as e:                       # keep the watcher alive
                print(f"[watch]  ! {brief.id} failed: {e}")
                continue
            with job.lock:
                if brief.id not in job.done:
                    job.done.append(brief.id)
                n = len(job.done)
            print(summarise(rec))
            print(f"[watch]  {n}/{len(job.briefs)} delivered → {job.delivery}")
            if n >= len(job.briefs):
                print(f"[watch]  ✓ every topic delivered. "
                      f"Hand {job.delivery} to the video project.")
                if once:
                    return
        time.sleep(POLL_S)


def serve(job: Job, port: int) -> None:
    handler = type("BoundHandler", (Handler,), {"job": job})
    threading.Thread(target=watch, args=(job,), daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"[bridge] {len(job.briefs)} topics at http://127.0.0.1:{port}/prompts "
          f"(build {EXPECTED_BUILD})")
    print("[bridge] open Flow, then press Connect in the extension panel. Ctrl-C to stop.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[bridge] stopped")
    finally:
        srv.server_close()


def clear_inbox(inbox: Path, ids: list[str]) -> int:
    """Remove stale clips so a previous run's downloads are not re-delivered."""
    inbox.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in inbox.iterdir():
        if f.suffix.lower() in (".mp4", ".webm", ".mov"):
            stem = f.stem.split(" (")[0]
            if stem in ids or stem.startswith("clip_"):
                os.remove(f)
                n += 1
    return n
