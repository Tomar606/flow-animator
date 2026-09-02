#!/usr/bin/env bash
#
# setup.sh — sets this up on your machine, then tells you exactly what to do next.
#
# Safe to run more than once: it repairs what is missing and leaves the rest
# alone. It never touches your browser profile, and it never writes outside this
# folder except to create the download inbox the extension needs.
#
set -uo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"

bold=$'\033[1m'; dim=$'\033[2m'; red=$'\033[31m'; grn=$'\033[32m'; ylw=$'\033[33m'; off=$'\033[0m'
ok()   { printf "  ${grn}✓${off} %s\n" "$1"; }
warn() { printf "  ${ylw}!${off} %s\n" "$1"; }
bad()  { printf "  ${red}✗${off} %s\n" "$1"; FAILED=1; }
step() { printf "\n${bold}%s${off}\n" "$1"; }
FAILED=0

printf "\n${bold}flow-animator setup${off}\n${dim}%s${off}\n" "$ROOT"

# ---------------------------------------------------------------- 1. Python --
step "1. Python"
PY=""
for c in python3.13 python3.12 python3.11 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  bad "No Python 3.10+ found."
  echo "      macOS:  brew install python@3.13"
  echo "      Ubuntu: sudo apt install python3 python3-venv"
  echo "      Windows: install from python.org, then run this in Git Bash or WSL."
  echo
  exit 1
fi
ok "$("$PY" --version) at $(command -v "$PY")"

# Python 3.14 shipped a pyexpat that crashes pip on some builds; 3.13 is the
# version this was developed and tested against.
case "$("$PY" -c 'import sys;print("%d.%d"%sys.version_info[:2])')" in
  3.14|3.15) warn "3.13 is the tested version; if pip crashes, install 3.13 and re-run." ;;
esac

# ------------------------------------------------------------------ 2. venv --
step "2. Virtual environment"
if [ ! -d .venv ]; then
  "$PY" -m venv .venv || { bad "Could not create .venv"; exit 1; }
  ok "created .venv"
else
  ok ".venv already there"
fi
./.venv/bin/python -m pip install --quiet --upgrade pip >/dev/null 2>&1
if ./.venv/bin/python -m pip install --quiet -r requirements.txt; then
  ok "numpy and Pillow installed"
else
  bad "pip install failed — scroll up for the reason"
fi

# ---------------------------------------------------------------- 3. ffmpeg --
step "3. ffmpeg"
for exe in ffmpeg ffprobe; do
  if command -v "$exe" >/dev/null 2>&1; then
    ok "$exe — $("$exe" -version 2>/dev/null | head -1 | cut -c1-60)"
  else
    bad "$exe is not on PATH"
    echo "      macOS:   brew install ffmpeg"
    echo "      Ubuntu:  sudo apt install ffmpeg"
    echo "      Windows: winget install Gyan.FFmpeg   (then reopen the terminal)"
  fi
done
# The alpha route needs a VP9 encoder. A stripped ffmpeg build will happily key
# a clip and then fail at the very end, after the slow part.
if command -v ffmpeg >/dev/null 2>&1; then
  if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libvpx-vp9; then
    ok "libvpx-vp9 present (needed for the transparent .webm)"
  else
    bad "this ffmpeg has no libvpx-vp9 encoder — transparent clips cannot be written"
    echo "      Install a full build (Homebrew's and Ubuntu's both have it)."
  fi
fi

# ---------------------------------------------------------------- 4. folders --
step "4. Folders"
DL="$HOME/Downloads"
[ -d "$HOME/Downloads" ] || DL="$HOME"
INBOX="$DL/flow_inbox"
mkdir -p "$INBOX" delivery
ok "download inbox   $INBOX"
ok "delivery folder  $ROOT/delivery"

if [ ! -f config.json ]; then
  cat > config.json <<JSON
{
  "topics": "topics/biology_class12.py",
  "delivery": "delivery",
  "inbox": "$INBOX",
  "port": 8765,
  "preview": true,
  "similarity": null
}
JSON
  ok "wrote config.json"
else
  ok "config.json already there (left alone)"
fi

cat > run.sh <<'RUN'
#!/usr/bin/env bash
# Start the bridge. Leave this running while you work in Flow.
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"
exec ./.venv/bin/python -u -m flowanim "${@:-run}"
RUN
chmod +x run.sh setup.sh
ok "wrote run.sh"

# ------------------------------------------------------------- 5. self-test --
step "5. Self-test"
export PYTHONPATH="$ROOT/src"
if ./.venv/bin/python -m flowanim list >/dev/null 2>&1; then
  N=$(./.venv/bin/python -m flowanim list 2>/dev/null | grep -c '^  *[0-9]*\.')
  ok "topics file parses — $N topic(s)"
else
  bad "the topics file did not parse:"
  ./.venv/bin/python -m flowanim list 2>&1 | sed 's/^/      /' | head -12
fi

# --------------------------------------------------------- 6. what to do next -
EXT="$ROOT/extension"
cat > NEXT-STEPS.md <<MD
# What to do next

Written by \`setup.sh\` on $(date "+%Y-%m-%d %H:%M") for this machine.
Everything below is filled in with your real paths.

## Once, in the browser

1. Open \`chrome://extensions\` (or \`brave://extensions\`).
2. Turn on **Developer mode**, top right.
3. **Load unpacked**, and choose exactly this folder:

       $EXT

4. Note the **ID** the browser shows under the extension's name. You need it
   only if you use Brave — see \`docs/BROWSER-SETUP.md\`, the section about
   Local Network Access. On Brave the bridge fails *silently* without it: the
   connection is made and the request is never delivered, which looks exactly
   like an extension that was never loaded.
5. Check that your browser downloads to **$DL**. If it asks where to save each
   file, turn that off — Settings → Downloads → "Ask where to save each file".

## Every time

    cd $ROOT
    ./run.sh                     # leave this running

Then in Flow (https://labs.google/fx/tools/flow), open your project and:

1. Click the extension's panel (the toolbar icon re-injects it if it is missing).
2. **Teach: prompt box** — click Flow's prompt box.
3. **Teach: Create button** — click Flow's Create button.
   Both are remembered. You only re-teach them if Flow changes its layout.
4. **Connect** — the panel says how many topics it loaded.
5. **Start** — it fills and submits each topic in turn.
6. Wait. Flow takes a few minutes per clip.
7. **Grab finished clips** — scroll first so every finished clip is on screen.

Each clip is keyed as it lands and written to:

    $ROOT/delivery/<TOPIC-ID>/

Watch the terminal running \`./run.sh\`. It tells you, per clip, whether the key
came out clean or whether the clip needs regenerating — and why.

## Your own topics

    cp topics/_template.py topics/my_subject.py
    # edit it, then point config.json at it, or:
    ./run.sh run --topics topics/my_subject.py

Read \`docs/WRITING-BRIEFS.md\` first. The gate that matters most:

    Ask Veo for the verb. Ask Manim for the number.

If the topic's mark is a count, a ratio, an order, a direction, or any detailed
structure that must be accurate — the base pairing in a DNA helix, a pedigree
chart, a labelled apparatus — it is not a prompting problem and this tool is the
wrong tool. Draw it in Manim or as an SVG. Run \`./run.sh route\` for the full
gate and the evidence behind it.
MD
ok "wrote NEXT-STEPS.md"

step "Done"
if [ "$FAILED" = "1" ]; then
  printf "  ${red}Some checks failed.${off} Fix the ✗ lines above and run ./setup.sh again.\n\n"
  exit 1
fi
cat <<TXT
  Everything is in place.

  ${bold}1.${off} Load the extension:  chrome://extensions → Developer mode → Load unpacked
                          $EXT
  ${bold}2.${off} Start the bridge:    ./run.sh
  ${bold}3.${off} Open Flow, press Connect in the panel, then Start.

  The full version of that, with your paths filled in, is in ${bold}NEXT-STEPS.md${off}.
  Before writing your own topics, read ${bold}docs/WRITING-BRIEFS.md${off} and run ${bold}./run.sh route${off}.

TXT
