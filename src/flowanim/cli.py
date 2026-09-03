"""`python -m flowanim <command>` — everything the local half can do.

    run       drive Flow and deliver every clip that comes back  (the one you want)
    serve     just the bridge, so the extension stays connected between runs
    route     the gate: which topics belong here and which belong in Manim/SVG
    list      what is in the topics file, and which field each will use
    prompts   print the assembled prompts, for pasting into Flow by hand
    key       key a clip you already have, without the browser at all
    doctor    check this machine before you spend a credit finding out
"""
from __future__ import annotations

import argparse
import shutil
import socket
import sys
import time
from pathlib import Path

from . import __version__, config
from .briefs import BriefError, load as load_briefs
from .deliver import deliver, summarise
from .key import KeyError_
from .bridge import EXPECTED_BUILD, FlowBridge, FlowError
from .drive import DriveError, load_selectors
from .drive import run as drive_run


ROUTE_GATE = """
  Before you spend a credit, answer this about the topic:

      Can the mark be stated as a COUNT, a RATIO, an ORDER or a DIRECTION?

  If yes, it does not belong here. Generation renders manner reliably and
  quantity unreliably: it knows what a polar body looks like and what a phage
  does, and it does not reliably draw THREE of something when three is the
  answer, or point an arrow the right way when direction is the answer.

  Three topics in the shipped example were regenerated with the number named
  explicitly, stated three ways, and every alternative banned. All three came
  back wrong again. That is a capability boundary, not a wording problem.

      Ask Veo for the verb.  Ask Manim for the number.

  Detailed structure that has to be ACCURATE — base pairing in DNA, a pedigree
  grid, a labelled apparatus, a ratio, anything a student could be marked wrong
  for misreading — is drawn deterministically, in Manim or as an SVG, where it
  comes out identical every time. Mark those topics "route": "manim" (or "svg")
  in the topics file with a "route_why", and this tool will refuse to generate
  them.

  The hybrid is usually the real answer: generate the organic body here on
  chroma, and composite the counts, arrows and labels over it in the video
  project, where they can be checked.
"""


def _briefs(args, cfg):
    path = config.resolve(args.topics or cfg["topics"])
    try:
        briefs = load_briefs(path)
    except BriefError as e:
        raise SystemExit(f"\n  {e}\n")
    if args.only:
        want = {s.strip() for s in args.only.split(",") if s.strip()}
        missing = want - {b.id for b in briefs}
        if missing:
            raise SystemExit(
                f"\n  --only names topics that are not in {path.name}: "
                f"{', '.join(sorted(missing))}\n")
        briefs = [b for b in briefs if b.id in want]
    return path, briefs


def _generable(briefs, *, force: bool):
    """Split off the topics that have been judged unreachable by generation."""
    routed = [b for b in briefs if not b.generable]
    if not routed:
        return briefs
    print("\n  Not generating these — they are routed to deterministic drawing:")
    for b in routed:
        print(f"    · {b.id}  →  {b.route}")
        for line in _wrap(b.route_why or "no reason recorded", 68):
            print(f"        {line}")
    print(f"\n  Ask Veo for the verb. Ask Manim for the number.  (docs/ROUTING.md)")
    if force:
        print("  --force given: generating them anyway.\n")
        return briefs
    keep = [b for b in briefs if b.generable]
    if not keep:
        raise SystemExit(
            "\n  Every topic selected is routed away from generation. Nothing to do.\n"
            "  Pass --force if you want to spend the credits regardless.\n")
    print(f"  Generating the remaining {len(keep)}.\n")
    return keep


def _wrap(text: str, width: int) -> list[str]:
    import textwrap
    return textwrap.wrap(text, width) or [""]


def cmd_list(args, cfg) -> int:
    path, briefs = _briefs(args, cfg)
    n = sum(1 for b in briefs if b.generable)
    print(f"\n{path}  —  {len(briefs)} topic(s), {n} generated here\n")
    for i, b in enumerate(briefs, 1):
        tag = f"[{b.field:<5}]" if b.generable else f"→ {b.route:<5}"
        print(f"  {i:>2}. {b.id:<16} {tag} {b.title}")
        for c in b.checks:
            print(f"        · {c}")
        if not b.generable:
            for line in _wrap(b.route_why, 66):
                print(f"        {line}")
    print()
    return 0


def cmd_route(args, cfg) -> int:
    print(ROUTE_GATE)
    try:
        path, briefs = _briefs(args, cfg)
    except SystemExit:
        return 0
    here = [b for b in briefs if b.generable]
    away = [b for b in briefs if not b.generable]
    print(f"  {path.name}\n")
    print(f"  Generated here ({len(here)}):")
    for b in here:
        print(f"    ✓ {b.id:<16} {b.title}")
    if away:
        print(f"\n  Drawn deterministically ({len(away)}):")
        for b in away:
            print(f"    → {b.id:<16} [{b.route}] {b.title}")
    print()
    return 0


def cmd_prompts(args, cfg) -> int:
    _, briefs = _briefs(args, cfg)
    for b in briefs:
        print("=" * 72)
        print(f"{b.id}  —  {b.title}   (generate on {b.field_word.upper()})")
        print("=" * 72)
        print(b.prompt())
        print(f"\nNEGATIVE:\n{b.negative()}\n")
    return 0


def cmd_key(args, cfg) -> int:
    _, briefs = _briefs(args, cfg)          # keying a clip you already have is
                                            # never blocked by the route gate
    by_id = {b.id: b for b in briefs}
    src = Path(args.clip).expanduser()
    if not src.exists():
        raise SystemExit(f"\n  No clip at {src}\n")
    tid = args.id or src.stem.split(" (")[0]
    if tid not in by_id:
        raise SystemExit(
            f"\n  {tid!r} is not a topic in this file. Pass --id, or name the "
            f"clip after its topic.\n  Known: {', '.join(by_id)}\n")
    out = config.resolve(args.delivery or cfg["delivery"])
    try:
        rec = deliver(src, by_id[tid], out,
                      make_preview=cfg["preview"], similarity=cfg["similarity"])
    except KeyError_ as e:
        raise SystemExit(f"\n  {e}\n")
    print(summarise(rec))
    print(f"\n  → {out / tid}\n")
    return 0 if rec["status"] == "ok" else 2


def cmd_run(args, cfg) -> int:
    path, briefs = _briefs(args, cfg)
    briefs = _generable(briefs, force=args.force)
    inbox = config.resolve(args.inbox or cfg["inbox"])
    delivery = config.resolve(args.delivery or cfg["delivery"])
    port = args.port or cfg["port"]

    try:
        sel = load_selectors(config.ROOT / "selectors.json")
    except (DriveError, ValueError) as e:
        raise SystemExit(f"\n  {e}\n")

    print(f"\n  topics    {path}  ({len(briefs)})")
    print(f"  downloads {inbox}")
    print(f"  delivery  {delivery}\n")

    bridge = FlowBridge(port, inbox).start()
    print(f"[bridge] http://127.0.0.1:{port}  (build {EXPECTED_BUILD})")
    print("[bridge] waiting for the extension — open your Flow project in a tab.")
    print("[bridge] the tab may stay in the background; nothing to press in it.")
    try:
        info = bridge.wait_for_worker(timeout=args.wait)
    except FlowError as e:
        bridge.stop()
        raise SystemExit(f"\n  {e}\n")

    tab = info.get("tab")
    print(f"[bridge] connected — {tab or 'NO FLOW TAB OPEN'}")
    if not tab:
        bridge.stop()
        raise SystemExit(
            "\n  The extension is loaded but no Google Flow tab is open. Open your\n"
            "  project at https://labs.google/fx/tools/flow and run this again.\n")
    if info.get("discarded"):
        print("[bridge] ! that tab is discarded — its renderer is not running. "
              "Click it once to wake it.")

    try:
        return drive_run(briefs, bridge, sel, delivery,
                         make_preview=cfg["preview"], similarity=cfg["similarity"])
    except KeyboardInterrupt:
        print("\n  stopped. Re-run to pick up the topics that did not deliver.")
        return 130
    finally:
        bridge.stop()


def cmd_serve(args, cfg) -> int:
    """Just the bridge. Useful to keep the extension connected while you work."""
    inbox = config.resolve(args.inbox or cfg["inbox"])
    port = args.port or cfg["port"]
    bridge = FlowBridge(port, inbox).start()
    print(f"\n  bridge  http://127.0.0.1:{port}  (build {EXPECTED_BUILD})")
    print(f"  inbox   {bridge.inbox_dir()}\n")
    try:
        info = bridge.wait_for_worker(timeout=args.wait)
        print(f"  extension connected — {info.get('tab') or 'no Flow tab open yet'}")
    except FlowError as e:
        print(f"  waiting for the extension…\n  {e}")
    print("\n  Ctrl-C to stop.")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n  stopped")
    finally:
        bridge.stop()
    return 0


def cmd_doctor(args, cfg) -> int:
    ok = True

    def check(label: str, good: bool, hint: str = "") -> None:
        nonlocal ok
        print(f"  {'✓' if good else '✗'} {label}")
        if not good:
            ok = False
            if hint:
                print(f"      {hint}")

    print("\nflow-animator doctor\n")
    check(f"Python {sys.version.split()[0]}", sys.version_info >= (3, 10),
          "Python 3.10 or newer is required.")
    for mod in ("numpy", "PIL"):
        try:
            __import__(mod)
            check(f"{mod} importable", True)
        except ImportError:
            check(f"{mod} importable", False, "Run ./setup.sh — the venv is missing deps.")
    for exe in ("ffmpeg", "ffprobe"):
        p = shutil.which(exe)
        check(f"{exe} on PATH", bool(p),
              "macOS: brew install ffmpeg · Ubuntu: sudo apt install ffmpeg")

    ext = config.ROOT / "extension" / "manifest.json"
    check("extension/ present", ext.exists(),
          "Load it at chrome://extensions → Developer mode → Load unpacked.")

    selp = config.ROOT / "selectors.json"
    try:
        sel = load_selectors(selp)
        need = [k for k in ("prompt",) if not sel.get(k)]
        check(f"selectors.json ({len(sel)} entries)", not need,
              f"missing a value for: {', '.join(need)}")
    except Exception as e:
        check("selectors.json", False, str(e).strip())

    try:
        path, briefs = _briefs(args, cfg)
        check(f"topics file parses ({len(briefs)} topics)", True)
    except SystemExit as e:
        check("topics file parses", False, str(e).strip())

    inbox = config.resolve(args.inbox or cfg["inbox"])
    check(f"download folder {inbox}", inbox.parent.exists(),
          f"{inbox.parent} does not exist — set \"inbox\" in config.json to your "
          f"real browser download directory.")

    port = args.port or cfg["port"]
    with socket.socket() as s:
        free = s.connect_ex(("127.0.0.1", port)) != 0
    check(f"port {port} free", free,
          f"Something is already listening on {port}. Stop it, or set a different "
          f'"port" in config.json (and in the panel).')

    print(f"\n  bridge build {EXPECTED_BUILD} — extension/background.js must say the same.")
    print("\n" + ("  All good. Start with:  ./run.sh\n" if ok else
                  "  Fix the ✗ lines above, then run this again.\n"))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    # The shared options are attached to every subcommand as well as to the top
    # level, so `run --topics X` and `--topics X run` both work. Argparse does
    # not do that on its own, and the error it gives when you get the order
    # wrong tells you nothing useful.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-t", "--topics", help="topics file (default: from config.json)")
    common.add_argument("--only", help="comma-separated topic ids to work on")
    common.add_argument("--delivery", help="output folder (default: from config.json)")
    common.add_argument("--inbox", help="browser download folder to watch (default: from config.json)")
    common.add_argument("--port", type=int, help="bridge port (default: from config.json)")
    common.add_argument("--force", action="store_true",
                        help="generate topics that are routed to Manim/SVG anyway")
    common.add_argument("--wait", type=float, default=120.0, metavar="S",
                        help="seconds to wait for the extension to connect (default: 120)")

    p = argparse.ArgumentParser(
        prog="flowanim", parents=[common],
        description="Topic briefs in, keyed animation clips out.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    p.add_argument("--version", action="version", version=f"flow-animator {__version__}")
    sub = p.add_subparsers(dest="cmd", metavar="command")

    sub.add_parser("run", parents=[common],
                   help="drive Flow and deliver the clips")
    sub.add_parser("serve", parents=[common],
                   help="just the bridge, so the extension stays connected")
    sub.add_parser("route", parents=[common],
                   help="the gate: what belongs here and what does not")
    sub.add_parser("list", parents=[common], help="show the topics")
    sub.add_parser("prompts", parents=[common], help="print the assembled prompts")
    sub.add_parser("doctor", parents=[common], help="check this machine")
    k = sub.add_parser("key", parents=[common], help="key a clip you already have")
    k.add_argument("clip")
    k.add_argument("--id", help="topic id, if the filename does not say")

    args = p.parse_args(argv)
    cfg = config.load()
    fn = {"run": cmd_run, "serve": cmd_serve, "list": cmd_list, "prompts": cmd_prompts,
          "route": cmd_route, "key": cmd_key, "doctor": cmd_doctor}.get(args.cmd or "run")
    return fn(args, cfg)
