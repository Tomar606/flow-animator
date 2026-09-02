"""A brief is what you write; a prompt is what Flow gets.

The wording below is not style. Every block in it was paid for in credits: the
clip set in `reference/biology/clip-set/` is what came back once these blocks
were in the prompt, and `reference/biology/ovule/` is the record of what came
back before each of them existed. Read `docs/WRITING-BRIEFS.md` before changing
any of it.

THE ORDER IS LOAD-BEARING
-------------------------
    field  ->  what is drawn, in textbook style  ->  what MOVES  ->
    framing and completeness  ->  silent  ->  NEGATIVE

That is the order of the one clip that came back correct on the first attempt
(DNA replication, `reference/biology/dna-replication/`), and it is the only
order with evidence behind it. The field comes first because it is the thing
most often lost; the negatives come last because a model weighs the end of a
prompt heavily and that is where the bans belong.

WHY THE FIELD IS A PER-TOPIC CHOICE
-----------------------------------
The clip is generated on a flat chroma field, keyed, and composited over your
own background. So the drawing must not contain the field colour, or the keyer
punches a hole through the diagram — see `rejected_green_field_sac_keyed_out.png`,
where the embryo sac was drawn green and keying removed the middle of the ovule.

Botany is green. Anything with a leaf, a stalk or a chloroplast in it should be
generated on `"field": "blue"`. Everything else keys more cleanly on green,
which is what Veo defaults toward and therefore renders flattest.

DO NOT ARGUE WITH THE MODEL ABOUT THE BACKGROUND
------------------------------------------------
Naming a thing in a prompt is a signal to draw it, so "do not change the
background" makes changes MORE likely. The field clause is three sentences on
purpose. An earlier version of this pipeline uploaded a finished background
plate and asked for the animation to be drawn onto it; Veo does not preserve a
plate, it regenerates a plausible imitation and adds to it — a measured run came
back with a benzene ring, a DNA helix and `H₂ = CH₂` that were never on the
plate. Keying is a compositing parameter. A plate is a request.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path

# --- the field clauses -------------------------------------------------------
# Three sentences, and the third one ("nothing else in it") is the one that
# actually removes the floor the model wants to stand the drawing on.

_FIELD = """The entire background is one flat, even, saturated chroma {name}, edge to edge,
the same {name} in every frame, with nothing else in it — no floor, no wall, no surface,
no horizon, no shadow cast onto it, and no gradient or texture in the {name}."""

FIELDS = {
    # name          prompt word   hex for the keyer's first guess
    "green": ("green", "0x1FB714"),
    "blue": ("blue", "0x1155A5"),
}

STYLE = """Drawn as a clean educational textbook illustration: bold dark outlines, flat
saturated colours, smooth cel shading, simple clear shapes. It is a drawing from a school
textbook — not a photograph, not a microscope image, and not a realistic
three-dimensional render."""

FRAMING = """The drawing is complete with {name} visible all around it and clear of every
edge IN EVERY FRAME, including at the end after everything it becomes has appeared. Size
it for its largest moment, so the opening frame looks emptier than feels natural. Nothing
runs off any edge at any time. The camera is locked and static. Nothing in the drawing is
{name} and no part of it is transparent."""

SILENT = "The clip is silent, with no voiceover and no narration."

# Bans that apply to every topic. Typography is banned outright because every
# word that ends up on screen is typeset afterwards in the video project, where
# it can be spell-checked — a generated letterform is a defect however neat it
# looks. Counts are labels too: where a topic turns on a number, say it as a
# shape the animation must have, never as a number to write.
_NEG_BASE = (
    "text, letters, words in any script, Devanagari, numerals, digits, captions, "
    "subtitles, labels, callouts, leader lines, arrows carrying letters, typography; "
    "border, frame, vignette, title card, sparkle, glint, lens flare, floating particles, "
    "glow, interface elements; a floor, a wall, a table, a surface, a horizon, a room, "
    "scenery, a shadow cast onto the background, a gradient or vignette in the {name}, "
    "uneven lighting on the background; photorealistic rendering, a microscope photograph, "
    "a realistic 3D render; the drawing growing past the top or bottom edge, the drawing "
    "being cut off by any edge, the drawing filling the whole frame edge to edge; "
    "camera pan, zoom, push-in, rotation, handheld drift; voiceover, narration, speech, music"
)

# Where a topic is drawn. "flow" means generate it here; the others mean it has
# been judged unreachable by generation and belongs in deterministic drawing
# code. See docs/ROUTING.md for the evidence behind that judgement.
ROUTES = ("flow", "manim", "svg")

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class BriefError(ValueError):
    """A topics file is malformed. The message names the topic and the field."""


@dataclass
class Brief:
    id: str
    title: str
    draws: str
    moves: str
    field: str = "green"
    bans: str = ""
    checks: list[str] = dc_field(default_factory=list)
    aspect: str = "9:16"
    notes: str = ""
    route: str = "flow"
    route_why: str = ""

    @property
    def generable(self) -> bool:
        return self.route == "flow"

    @property
    def field_word(self) -> str:
        return FIELDS[self.field][0]

    @property
    def field_hex(self) -> str:
        return FIELDS[self.field][1]

    def prompt(self) -> str:
        """The positive prompt, in the proven order."""
        name = self.field_word
        return "\n\n".join([
            _FIELD.format(name=name),
            f"On it is drawn {self.draws}.",
            STYLE,
            f"Over the clip, {self.moves}. The movement is steady and finishes "
            f"within the clip.",
            FRAMING.format(name=name),
            SILENT,
        ])

    def negative(self) -> str:
        base = _NEG_BASE.format(name=self.field_word)
        extra = self.bans.strip().rstrip(",")
        return f"{base}; {extra}" if extra else base

    def full(self) -> str:
        """Prompt and negatives as one block.

        Flow's UI has no separate negative-prompt field, so the bans travel in
        the prompt itself, last, introduced by a clause the model reads as an
        instruction rather than as more things to draw.
        """
        return f"{self.prompt()}\n\nDo NOT include any of the following: {self.negative()}."

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "field": self.field,
            "field_hex": self.field_hex,
            "aspect": self.aspect,
            "prompt": self.prompt(),
            "negative": self.negative(),
            "text": self.full(),
            "checks": list(self.checks),
            "notes": self.notes,
            "route": self.route,
            "route_why": self.route_why,
        }


def _one(topic_id: str, raw: dict, source: Path) -> Brief:
    where = f"{source.name}: topic {topic_id!r}"
    if not ID_RE.match(topic_id):
        raise BriefError(
            f"{where} — the id becomes a filename, so it may only contain "
            f"letters, digits, dot, dash and underscore.")
    if not isinstance(raw, dict):
        raise BriefError(f"{where} — expected a dict, got {type(raw).__name__}.")

    for key in ("draws", "moves"):
        if not str(raw.get(key, "")).strip():
            raise BriefError(
                f"{where} — {key!r} is required and must not be empty. "
                f"See topics/_template.py.")

    fld = str(raw.get("field", "green")).lower()
    if fld not in FIELDS:
        raise BriefError(
            f"{where} — field {fld!r} is not one of {sorted(FIELDS)}. "
            f"Use 'blue' for anything botanical, 'green' otherwise.")

    route = str(raw.get("route", "flow")).lower()
    if route not in ROUTES:
        raise BriefError(
            f"{where} — route {route!r} is not one of {sorted(ROUTES)}. "
            f"Use 'flow' to generate it here; 'manim' or 'svg' to say it must be "
            f"drawn deterministically instead. See docs/ROUTING.md.")
    if route != "flow" and not str(raw.get("route_why", "")).strip():
        raise BriefError(
            f"{where} — a topic routed to {route!r} must also give 'route_why'. "
            f"The reason is the useful part; without it the next person retries it.")

    checks = raw.get("checks") or []
    if isinstance(checks, str):
        checks = [checks]

    def clean(s: str) -> str:
        # briefs are written as triple-quoted prose; collapse the newlines so
        # the prompt reaches Flow as flowing sentences rather than a poem.
        return " ".join(str(s).split())

    return Brief(
        id=topic_id,
        title=clean(raw.get("title", topic_id)),
        draws=clean(raw["draws"]).rstrip("."),
        moves=clean(raw["moves"]).rstrip("."),
        field=fld,
        bans=clean(raw.get("bans", "")),
        checks=[clean(c) for c in checks],
        aspect=str(raw.get("aspect", "9:16")),
        notes=clean(raw.get("notes", "")),
        route=route,
        route_why=clean(raw.get("route_why", "")),
    )


def load(path: str | Path) -> list[Brief]:
    """Import a topics file and return its briefs, in file order."""
    path = Path(path).expanduser().resolve()
    if not path.exists():
        raise BriefError(f"No topics file at {path}")
    if path.suffix != ".py":
        raise BriefError(f"{path.name} is not a .py topics file")

    spec = importlib.util.spec_from_file_location(f"_topics_{path.stem}", path)
    if spec is None or spec.loader is None:          # pragma: no cover
        raise BriefError(f"Could not import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)
    except SyntaxError as e:
        raise BriefError(
            f"{path.name} has a Python syntax error on line {e.lineno}: {e.msg}\n"
            f"  Most often an unclosed triple-quote or a missing comma between topics."
        ) from e

    topics = getattr(mod, "TOPICS", None)
    if not isinstance(topics, dict) or not topics:
        raise BriefError(
            f"{path.name} must define a non-empty dict named TOPICS. "
            f"Copy topics/_template.py to start one.")

    return [_one(tid, raw, path) for tid, raw in topics.items()]
