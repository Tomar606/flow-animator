# What belongs here, and what belongs in Manim or an SVG

> **Ask the generator for the verb. Ask Manim for the number.**

This is the first decision, before any brief is written and before any credit is
spent. Getting it wrong is the most expensive mistake available in this pipeline,
because a wrong clip does not look wrong — it looks confident.

---

## The gate

Ask this about the topic:

> **Can the mark be stated as a count, a ratio, an order, or a direction?
> Does it contain detailed structure that has to be accurate?**

If yes, it does not belong here.

Generation renders **manner** reliably and **quantity** unreliably. It knows what
a polar body looks like, what a bacteriophage does, what a pond contains. It does
not reliably draw *three* of something when three is the answer, does not point
an arrow the right way when direction is the answer, and does not keep a
structural rule — A pairs with T, G pairs with C — that a student would be marked
wrong for breaking.

Anything in that second category is drawn **deterministically**: in Manim, or as
an SVG, or by hand. There it comes out identical every time, it can be checked
once, and it stays checked.

| Draw it deterministically | Generate it here |
|---|---|
| a count that is the answer (three polar bodies, four microspores) | how a cell divides unequally |
| a ratio (9 : 3 : 3 : 1) | what a blend looks like next to a patchwork |
| an order (trophic levels, a sequence of stages) | what a habitat contains |
| a direction (arrows from eaten to eater) | how a phage empties into a bacterium |
| exact structure (DNA base pairing, a pedigree grid, a circuit, a labelled apparatus) | the organic form of a thing changing |
| anything with text or numbers on it | texture, growth, flow, corrosion |

Mark those topics `"route": "manim"` (or `"svg"`) in the topics file, with a
`"route_why"`. This tool then refuses to generate them, which is the point —
`./run.sh route` prints the gate and the split for your file.

---

## The evidence

Fourteen Class 12 Biology animations were briefed by hand, generated, and graded
against their own biology checks. The clips are in `reference/biology/clip-set/`.

**Seven shipped. Seven were routed away.** The failures were not spread evenly.
Every one failed on the same thing: *a discrete quantity that IS the answer.*

| topic | the marked quantity | what came back |
|---|---|---|
| dihybrid cross | 9 : 3 : 3 : 1 | 9 : 4 : 4 : 4 |
| ovule | 3 egg-apparatus cells + 3 antipodals | 1 + 2 |
| ovule | micropyle beside the funicle (anatropous) | at the far end (orthotropous) |
| food chains | arrows: eaten → eater | reversed, and the chains crossed |
| ecological pyramid | tiers ordered by trophic level | inverted and scrambled |
| DNA helix | A–T and G–C, consistently | any base with any base |
| electrophoresis | a child's bands traceable to a parent | random bands |

And every topic that passed asks for no such quantity: a blend versus a patch, the
*manner* of an unequal division, a sperm's morphology, an action, a habitat.

### The confirmation that settles it

Three of the failures were regenerated with briefs corrected precisely against
the finding — the number named explicitly, stated three ways, every alternative
banned. This was the test of whether the failures were prompt-craft or capability.

| topic | the fix | result |
|---|---|---|
| ovule | anatropous stated three ways; 3 + 3 cells named explicitly | **still wrong** — 4 and 6 cells, funicle attached to nothing |
| DNA helix | only two legal rung pairings, named by colour, every other pairing banned | **still wrong** — yellow met blue, and a fifth colour appeared |
| uterus | framing only, stated as "spans the middle third of the picture width" | **passed** |

The third row is the control, and it is why the conclusion is narrow rather than
general: a *framing* correction landed on the first retry. A *quantity*
correction did not land at all, three times. Wording moves framing. Wording does
not move counting.

---

## The hybrid, which is usually the real answer

Generate the organic body here on chroma, and composite the counts, arrows and
labels over it in the video project, where they are drawn deterministically and
can be checked.

The ovule is the clearest case: its *form* is organic and generation draws it
beautifully; the seven cells and the anatropous orientation are geometry. Nothing
requires those to come from the same place.

This is also why every brief bans typography outright. Every word that ends up on
screen is typeset afterwards, where it can be spell-checked. A generated
letterform is a defect however neat it looks — and a generated *number* is a
defect even when it is right, because it was not checked.

---

## Two mistakes worth not repeating

**Check every colour you name against the chroma field.** One brief asked for
yellow-with-**green** rungs on a **green** field. Had the model complied, half of
every such rung would have keyed out into a hole — the same failure as
`reference/biology/ovule/rejected_green_field_sac_keyed_out.png`, where an embryo
sac drawn in green was removed from the middle of the ovule by the keyer. This is
now a mechanical check, not a habit.

**One new demand per revision.** Emphasis is zero-sum. A brief revised to add
both anatomy and framing came back with the anatomy fixed and the framing worse.
Re-run with framing alone, stated as a concrete fraction of the frame rather than
as "a wide band", and it passed.

**A correction must live in the file the generator reads.** One topic's
orientation was corrected in a planning note and never propagated into the brief.
The generator rendered the brief faithfully, and the clip was confidently wrong —
and the review could not catch it, because a review grades the clip against the
brief. If the fix is not in the topics file, it does not exist.
