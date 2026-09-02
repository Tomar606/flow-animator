# Writing a brief

A brief is five fields. The tool assembles them into a prompt in a fixed order,
adds the field clause, the style clause, the framing clause and the standing ban
list, and sends that. You write only what is specific to your topic.

```python
"MY-TOPIC-01": {
    "title":  "...",     # how a colleague recognises the clip
    "route":  "flow",    # or "manim" / "svg" — read step 0 first
    "field":  "green",   # or "blue" — read step 1
    "draws":  "...",     # the still picture, before anything moves
    "moves":  "...",     # the one change, start to finish
    "bans":   "...",     # the wrong picture this topic invites
    "checks": [...],     # what must be true, checkable from a still frame
},
```

---

## Step 0 — decide it belongs here at all

> **Can the mark be stated as a count, a ratio, an order or a direction? Does it
> contain detailed structure that has to be accurate?**

If yes, **stop**. Draw it in Manim or as an SVG. Set `"route": "manim"` with a
`"route_why"` and this tool will refuse to generate it.

This is not caution. Three topics were regenerated with the number named
explicitly, stated three ways, and every alternative banned — all three came back
wrong again. Generation renders *manner* reliably and *quantity* unreliably. See
[ROUTING.md](ROUTING.md) for the full evidence and the hybrid that usually beats
both.

Detailed structure that must be accurate — base pairing in a DNA helix, a
pedigree grid, a labelled apparatus, a circuit, anything a student could be
marked wrong for misreading — is drawn deterministically, every time.

---

## Step 1 — pick the field, and check every colour against it

The clip is generated on a flat chroma field and keyed. **The drawing must not
contain the field colour**, or the keyer removes that part of the drawing.

- **Botanical → blue.** Leaves, stalks, chloroplasts, anything green by nature.
- **Everything else → green.** It is what the model drifts toward anyway, and it
  therefore renders flattest.

Then read back every colour you *name* in the brief and check it against the
field. One brief asked for yellow-with-**green** rungs on a **green** field; had
the model complied, half of every such rung would have keyed into a hole. This is
mechanical, not a matter of judgement — do it every time.

`reference/biology/ovule/rejected_green_field_sac_keyed_out.png` is what the
failure looks like: an embryo sac drawn green, and the keyer took the middle out
of the ovule. `blue_field_key_verified.png` is the same topic, fixed.

---

## Step 2 — `draws`: the still picture

Describe the **object**, not a scene. No floor, no table, no room, no horizon —
they are already banned, and naming one to forbid it makes it *more* likely.

Say where things sit **relative to each other**, because relative position is
what gets lost first: *"the small opening sits at the SAME end as the stalk,
close beside where it joins"*, not *"a micropyle"*.

Capitalise the one word that must not be missed. `INVERTED`, `UNEQUAL`,
`THREE` — used sparingly it survives; used everywhere it stops meaning anything.

Where the framing matters, state it as a **measurable fraction of the frame**.
"A wide band of empty space on both sides" failed; *"the whole drawing spans only
the middle THIRD of the picture width"* passed on the next attempt.

---

## Step 3 — `moves`: one change, finished inside the clip

One continuous change with a beginning and an end, and say what it **ends as**.
"Each part settles and stays. Nothing that has appeared moves again" is worth its
length — without it, things keep drifting and the last frame is unusable as an
anchor for a follow-on clip.

Never ask for a camera move. Never mention music or narration — they are banned
already, and a musical phrase cannot resolve inside ten seconds anyway: it gets
cut mid-bar at the boundary and the next clip restarts from silence.

---

## Step 4 — `bans`: the wrong picture, named

The general bans are already applied to every brief: text and typography in any
script, borders, sparkles, floors and rooms, photorealism, camera moves,
narration. Do not repeat them.

Your `bans` are the **specific** wrong picture this topic invites. For an ovule:
a seed, a fruit, a whole flower, a pollen tube, a second ovule. Name what the
model reaches for when it does not know — that is what a ban is for.

---

## Step 5 — `checks`: what a reviewer confirms from one frame

Each check is a statement that can be confirmed or denied from a **single still
frame**, about the *subject*, not the picture quality:

```
"exactly three small cells remain at the end, clustered at the large cell's edge"
"the lining thickens first and sheds afterwards, never the reverse"
```

The checks travel into `delivery/<ID>/<ID>.json` and into the manifest, so
whoever uses the clip sees what it was supposed to show. This is the only part of
the process no tool can do for you, and it is what catches the expensive failure:
a clip that is confidently, plausibly wrong and passes an unaided glance.

---

## Revising a brief that came back wrong

**One new demand per revision.** Emphasis is zero-sum. A brief revised to fix
both the anatomy and the framing came back with the anatomy fixed and the framing
*worse*. Re-run with one change, stated in units the model can measure.

**Never argue with the background.** Naming a thing is a signal to draw it, so
"do not change the background" makes changes more likely. The field clause is
three sentences on purpose; an earlier design uploaded a finished background
plate and asked for the animation to be drawn onto it, and a measured run came
back with a benzene ring, a DNA helix and `H₂ = CH₂` that were never on the
plate. Keying is a compositing parameter. A plate is a request.

**Put the correction in the topics file.** A fix that lives in a note and never
reaches the brief does not exist. The generator renders the brief faithfully, and
a review grades the clip against the brief — so a wrong brief produces a
confidently wrong clip that passes review.

**After two failed revisions on the same point, stop and re-read step 0.** Two
misses on the same demand usually means the demand is a quantity.
