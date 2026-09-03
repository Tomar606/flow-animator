# flow-animator

Topic briefs in, keyed animation clips out — into a folder the video project
reads directly.

You write a short brief per topic. The tool drives Google Flow in your own
logged-in browser, generates each clip on a flat chroma field, keys it, measures
the result, and files it with everything needed to check it:

```
delivery/
  manifest.json                 every topic, its status and its files
  BIO-C2-LA-01/
    BIO-C2-LA-01_alpha.webm     ← composite this. VP9, real alpha channel.
    BIO-C2-LA-01_raw.mp4        what Flow returned, chroma field and all
    BIO-C2-LA-01_last.png       final frame, for anchoring a follow-on clip
    BIO-C2-LA-01_preview.mp4    the keyed clip over slate, for eyeballing
    BIO-C2-LA-01.json           brief, prompt, key report, checks to confirm
```

Nothing here calls a paid API. Google Flow is covered by a Google AI
subscription but is **UI-only** — those credits do not apply to the API, which
bills separately. So a Chrome extension drives the browser session you are
already signed into, and hands the results to a local bridge.

---

## Read this before you generate anything

> ### Ask the generator for the verb. Ask Manim for the number.

If the topic's mark can be stated as a **count**, a **ratio**, an **order** or a
**direction** — or if it contains **detailed structure that has to be accurate**,
like base pairing in a DNA helix, a pedigree grid, a labelled apparatus or a
circuit — **this is the wrong tool**. Draw it in **Manim or as an SVG**, where it
comes out identical every time and can be checked once.

This is not caution, it is a measured boundary. Fourteen topics were briefed by
hand and graded; seven failed, and every one failed on the same thing: a discrete
quantity that *is* the answer. Three were then regenerated with the number named
explicitly, stated three ways, and every alternative banned — all three came back
wrong again. Wording does not move counting.

Mark those topics `"route": "manim"` in the topics file and **this tool refuses to
generate them**. Run `./run.sh route` for the gate and the evidence, or read
[docs/ROUTING.md](docs/ROUTING.md).

Generation is for the *verb*: how a thing happens, what moves, what it looks like
while it changes. The hybrid usually beats both — generate the organic body here,
and composite the counts, arrows and labels over it in the video project.

---

## Install

**You need:** Python 3.10+ (3.13 recommended), `ffmpeg` with `libvpx-vp9`, and
Chrome or Brave.

```bash
brew install python@3.13 ffmpeg          # macOS
# sudo apt install python3 python3-venv ffmpeg     # Ubuntu/Debian
```

Then:

```bash
git clone <this repo> flow-animator
cd flow-animator
./setup.sh
```

`setup.sh` checks everything, builds the venv, creates the folders, writes
`config.json` and `run.sh`, and finishes by writing **`NEXT-STEPS.md`** with your
real paths filled in. It is safe to run again at any time.

```bash
./run.sh doctor        # re-check this machine whenever something is off
```

### Browser setup

Full detail, including the one that will otherwise waste your afternoon, is in
[docs/BROWSER-SETUP.md](docs/BROWSER-SETUP.md). The short form:

1. `chrome://extensions` → **Developer mode** → **Load unpacked** → this repo's
   `extension/` folder. Note the extension **ID**.
2. Settings → Downloads → **turn off "Ask where to save each file"**, and make
   sure the download folder matches `"inbox"` in `config.json`.
3. **Brave only:** Chromium's Local Network Access check blocks the bridge
   *silently* — the TCP connection is established and the request is never
   delivered, with no error anywhere. Add a policy allowlist at
   `/Library/Managed Preferences/com.brave.Browser.plist` naming your extension
   ID and `http://127.0.0.1:8765`, restart, and confirm at `brave://policy`. The
   exact plist is in [docs/BROWSER-SETUP.md](docs/BROWSER-SETUP.md).
4. Expect Chrome's **"is debugging this browser"** banner while a run is going.
   Do not dismiss it. Flow's prompt box is a Slate editor that rejects synthetic
   input, so text has to arrive as a trusted keystroke over the debugger protocol.

> The extension's ID is derived from its folder path. Move or rename this repo
> and the ID changes, which silently breaks the Brave policy above.

---

## Use

Open your Flow project in a tab. That is everything the browser asks of you.

```bash
./run.sh                 # drives Flow and delivers every clip
```

The run is driven from here, not from the page. For each topic in turn it types
the prompt, presses Create, waits for the clip, downloads it through your
session, keys it and files it — then moves to the next one.

**The tab can sit behind whatever you are actually doing.** The extension drives
it over the Chrome debugger protocol, which dispatches into the renderer and
does not care whether the tab is visible, foreground, or on the desktop you are
looking at. The panel it injects is a status readout with **no controls**; close
it, or never open it, and the run is unaffected.

Two things a background tab breaks, both handled in `extension/background.js`:
Slate drops input when `document.hasFocus()` is false, so the worker turns on
`Emulation.setFocusEmulationEnabled`; and an MV3 worker is killed after 30s idle,
so a 20s timer touches a trivial extension API — which is what actually resets
the idle timer, a pending `fetch` does not — with a 30s alarm to restart the
poll loop if it was killed anyway.

There is nothing to teach. Every control the run touches in Flow's UI is named
in [`selectors.json`](selectors.json), which is also the one file to edit when
Flow moves something. It avoids hashed class names on purpose and prefers a
`data-` attribute, an `aria-label`, or visible button text, in that order.

The terminal tells you, per clip, whether it came out clean:

```
  ✓ BIO-C2-LA-01  Oogenesis: three unequal divisions, three polar bodies
    coverage 22.5%  holes 0.03%  edge 0%
  ? BIO-C5-LA-03  DNA double helix turning, base pairs intact
    coverage 10.9%  holes 2.41%  edge 0%
    open the preview — 2.4% of the frame is background enclosed by the drawing…
```

Then hand `delivery/` to the video project, which should read `manifest.json`
rather than guessing at filenames.

### Your own topics

```bash
cp topics/_template.py topics/my_subject.py
./run.sh run --topics topics/my_subject.py
```

A brief is five fields — what is drawn, what moves, what to ban, what must be
true, and which chroma field. Read
[docs/WRITING-BRIEFS.md](docs/WRITING-BRIEFS.md) first; most of what makes a
brief work is not obvious.

`topics/biology_class12.py` is the worked example: fourteen Class 12 Biology
animations, seven generated here and seven routed away, each with the reason
recorded.

### Commands

```bash
./run.sh run        # drive Flow and deliver the clips          (the default)
./run.sh serve      # just the bridge, so the extension stays connected
./run.sh route      # the gate: what belongs here, what does not
./run.sh list       # the topics, their fields and their checks
./run.sh prompts    # the assembled prompts, for pasting by hand
./run.sh key FILE   # key a clip you already have, no browser involved
./run.sh doctor     # check this machine
```

`run --only BIO-C2-LA-01,BIO-C4-LA-01` re-runs just those, which is what the
summary prints for you when a topic does not come back.

---

## Two things about the chroma field

**Choose it per topic.** The clip is keyed, so the drawing must not contain the
field colour, or the keyer removes that part of the drawing. Anything botanical
goes on **blue**; everything else on **green**. Then read back every colour you
*name* in a brief and check it against the field — one brief asked for
yellow-with-green rungs on a green field, and had the model complied, half of
every rung would have keyed into a hole.

**Never argue with the model about the background.** Naming a thing is a signal
to draw it, so "do not change the background" makes changes more likely. An
earlier design uploaded a finished background plate and asked for the animation
to be drawn onto it; the model does not preserve a plate, it regenerates a
plausible imitation and adds to it — a measured run came back with a benzene
ring, a DNA helix and `H₂ = CH₂` that were never on the plate. Keying is a
compositing parameter. A plate is a request.

---

## What is in here

```
setup.sh                  sets this up and tells you what to do next
topics/                   the briefs you write  (biology_class12.py is the example)
extension/                the Chrome MV3 extension — load this unpacked
                          background.js drives the tab; content.js only reports
selectors.json            every control this touches in Flow's UI, in one file
src/flowanim/
  briefs.py               a brief → the prompt Flow gets
  bridge.py               the verb server the extension long-polls
  drive.py                the run loop: submit, wait, download, key, file
  key.py                  chroma key, plus the measurement that catches a bad one
  deliver.py              what lands in delivery/, and the manifest
  cli.py                  the commands above
reference/biology/        source scans, six attempts at one topic, fourteen clips,
                          and all 110 captioned NCERT Class 12 figures
tools/                    one-off: extract the NCERT figures from the chapter PDFs
docs/
  ROUTING.md              what belongs here and what belongs in Manim  ← read this
  WRITING-BRIEFS.md       how to write a brief that works
  BROWSER-SETUP.md        Chrome and Brave, and the silent Brave failure
  REFERENCE-DIAGRAMS.md   every file in reference/, and what it is
```

## Keep this repository private

`reference/biology/` contains figures rendered from the NCERT Class 12 Biology
PDFs, and every page of those carries a diagonal **"© not to be republished"**
notice which renders into each figure. Share this by adding collaborators, not by
making the repo public or re-hosting the figures. Everything else in here —
the code, the briefs, the generated clips — is ours.

