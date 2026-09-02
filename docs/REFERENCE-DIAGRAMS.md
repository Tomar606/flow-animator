# The reference material, and what each file is

Everything in `reference/` is committed on purpose. It is the evidence behind
every rule in [WRITING-BRIEFS.md](WRITING-BRIEFS.md) and [ROUTING.md](ROUTING.md),
and it is far more use than the rules alone: a rejected frame shows you a failure
in a second that takes a paragraph to describe.

Three groups: **source diagrams** (what the animation must be true to),
**one topic's full accept/reject history**, and **the delivered clip set**.

---

## `reference/biology/ovule/` — one topic, six attempts, and why each failed

Class 12 Biology, Chapter 1, Long Answer 1: *draw a labelled diagram of a typical
angiosperm ovule.* This topic is now routed to Manim — see
[ROUTING.md](ROUTING.md) — and the record of getting there is the most useful
thing in this repo.

### The source diagrams

| file | what it is |
|---|---|
| `source_answer_page.png` | The scanned question-bank page the topic comes from, in Hindi: *एक प्रारूपी आवृतबीजी बीजाण्ड …* with its model answer. Carries **figure 1.5**, a typical **anatropous** ovule labelled hilum, funicle, micropyle, micropylar end, outer and inner integument, nucellus, embryo sac, chalazal end; and **figure 1.6**, the embryo sac enlarged. This page is the authority for what the clip must show. |
| `reference_book_figure.png` | Figure 1.5 cropped and enlarged — a stippled line drawing. Note the shape that matters: the body lies back **alongside** its own stalk, and the micropyle is at the **same** end as the stalk, not opposite it. That is what *anatropous* means, and it is the single fact every rejected attempt got wrong. |
| `reference_book_embryo_sac.png` | Figure 1.6 cropped: the embryo sac with the **egg apparatus** (one egg cell between two synergids) at the micropylar end, the **secondary nucleus** in the centre, and **three antipodal cells** at the chalazal end. Seven cells, eight nuclei. |
| `ncert_ovule_reference.png` | The NCERT ovule figure, in colour. Included because NCERT wins wherever it and the question bank disagree. Labels are cropped off deliberately — the clip must carry no text, so the shape is the only thing to take from it. |
| `ncert_embryo_sac_reference.png` | The NCERT embryo sac, in colour, drawn with the micropylar end **downward** — the opposite orientation from the question bank's figure 1.6. A good reminder that orientation is a convention, and therefore has to be stated in the brief rather than assumed. |

### The attempts

Read these in order. Each is a still from a generated clip.

| file | verdict |
|---|---|
| `rejected_v2.png` | **Unkeyable, and the wrong anatomy.** Every part is a shade of green on a green field, so keying would remove the whole drawing. The sac also sits at the stalk end instead of offset toward the micropyle, and the nucellus is drawn as brain-like folds. |
| `rejected_v3.png` | **Still all green, and now orthotropous.** The ovule stands upright on a straight stalk with the opening at the top, away from the stalk — the anatropous inversion is gone. Sepal-like leaves have appeared, which nothing asked for. |
| `master_v4_from_book_reference.png` | **Accepted at the time**, generated with `reference_book_figure.png` attached. The inversion is right: the stalk runs up alongside the body. Still drawn largely in green, which is what the next attempt is about. Its clip is `master_v4.mp4`. |
| `rejected_v5_colour_broke_shape.png` | **The colour was fixed and the shape broke.** Blue sac, cream nucellus, orange coats — all keyable. But it is now a whole flower: sepals, leaves, a style, standing upright on a straight stalk. This is the *emphasis is zero-sum* lesson in one picture. |
| `rejected_v6_colour_ok_shape_broke.png` | **Same failure, tidier.** Keyable colours, clean drawing, and still orthotropous — upright, micropyle at the top, the stalk beneath instead of alongside. |
| `rejected_green_field_sac_keyed_out.png` | **The keying failure, made visible.** The drawing is good, but the embryo sac was painted the same green as the field, so keying punched a hole through the middle of the ovule. This is the exact case the delivery check now measures — the tool reports about 5% enclosed transparency on this frame and 0.00% on the accepted one below. |
| `blue_field_key_verified.png` | **The fix.** The same topic regenerated on a **blue** field, so the plant greens survive keying. Nothing in the drawing is blue; the key comes out clean. |
| `master_v4.mp4` | The v4 clip in full, for watching the motion rather than a frame. |

**What the six attempts add up to:** the colour problem was solved and the shape
problem was solved, and never at the same time. That is what sent the topic to
Manim — see [ROUTING.md](ROUTING.md).

---

## `reference/biology/dna-replication/` — the clip that worked first time

The one that came back correct on the first attempt, and whose structure every
brief in `topics/biology_class12.py` follows.

| file | what it is |
|---|---|
| `dna_f0.png` | First frame: one double helix, blue and purple backbones. |
| `dna_fmid.png` | Mid clip: the strands separating progressively from one end. |
| `dna_flast.png` | Last frame, and the proof it is right — **two** complete helices, each carrying **one blue and one purple** backbone. One parental strand and one new strand each: semi-conservative replication, which is the whole point of the question. |
| `01_raw_green.mp4` | The raw clip as generated, on the chroma field. |
| `02_keyed_alpha.webm` | The same clip keyed — VP9 with a real alpha channel. This is the format the tool now delivers. To inspect its alpha with ffmpeg you must name the decoder: `ffmpeg -c:v libvpx-vp9 -i … -vf alphaextract`, or the alpha plane is not exposed. |
| `03_preview_over_plate.mp4` | The keyed clip composited over a rendered background at 1080×1920 — what it looks like in a finished video. |

---

## `reference/biology/clip-set/` — the fourteen delivered clips

For each topic: the generated clip, and its final frame as a PNG. The filename
suffix says which chroma field it was generated on.

| clip | topic |
|---|---|
| `BIO-C1-LA-01_blue` | angiosperm ovule in section |
| `BIO-C1-LA-02_blue` | microsporogenesis beside megasporogenesis |
| `BIO-C2-LA-01_green` | oogenesis — unequal divisions and polar bodies |
| `BIO-C2-LA-02_green` | the uterine lining through one menstrual cycle |
| `BIO-C2-LA-03_green` | spermatogenesis — four equal cells, then four tails |
| `BIO-C4-LA-01_blue` | incomplete dominance beside codominance |
| `BIO-C4-LA-02_blue` | dihybrid cross — the four phenotype groups |
| `BIO-C4-LA-03_green` | X-linked inheritance pedigree |
| `BIO-C5-LA-01_green` | gel electrophoresis |
| `BIO-C5-LA-02_green` | Hershey–Chase — the phage stays outside |
| `BIO-C5-LA-03_green` | DNA double helix turning |
| `BIO-C12-LA-01_green` | grazing food chain above a detritus food chain |
| `BIO-C12-LA-02_green` | an ecological pyramid, then inverted |
| `BIO-C12-LA-03_blue` | a pond ecosystem filling in layers |

Seven of these ship and seven are routed to Manim. **The routed ones are kept
because the failure is the information** — the arrows in `BIO-C12-LA-01` point
the wrong way, the four groups in `BIO-C4-LA-02` come out 9:4:4:4, and the rungs
in `BIO-C5-LA-03` pair any colour with any colour. Look at those three before
writing a brief that depends on a count.

The whole set is also the keyer's regression test. Every clip in it keys cleanly
at the shipped settings:

```bash
./run.sh key reference/biology/clip-set/BIO-C2-LA-01_green.mp4 --id BIO-C2-LA-01
```

---

## `reference/biology/style-reference-plant-cell.png`

A plant cell illustrated on a green field: bold dark outlines, flat saturated
colours, smooth cel shading, no text anywhere. This is the look the `STYLE`
clause in `src/flowanim/briefs.py` is trying to name in words. When a brief comes
back photorealistic or three-dimensional, compare against this rather than
rewriting the clause from scratch.
