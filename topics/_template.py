"""Copy this file, rename it, and fill it in. Then:

    ./run.sh run --topics topics/<your file>.py

Read docs/WRITING-BRIEFS.md before you write the first one — most of what makes
a brief work is not obvious, and every rule in that file was paid for.

THE GATE, FIRST
---------------
Before writing anything, ask: can the mark be stated as a COUNT, a RATIO, an
ORDER or a DIRECTION? Is there detailed structure that has to be ACCURATE — base
pairing in a DNA helix, a pedigree grid, a labelled apparatus, a circuit?

If yes, this is the wrong tool. Draw it in Manim or as an SVG, where it comes
out identical every time and can be checked once. Mark it "route": "manim" here
with a "route_why", and this tool will refuse to generate it — which is the
point. `./run.sh route` prints the gate and the evidence behind it.

Generation is for the VERB: how a thing happens, what moves, what it looks like
while it changes. Not for how many.
"""

TOPICS = {

    # The id becomes the folder name in delivery/ and the download filename, so
    # keep it short and use it as the topic's name everywhere else too.
    "MY-TOPIC-01": {

        "title": "One line a colleague can recognise the clip by",

        # "flow"  — generate it here.
        # "manim" / "svg" — do not; it needs a count, an order, or exact
        #                   structure. A "route_why" is then required.
        "route": "flow",

        # "green" or "blue". The clip is keyed, so the drawing must not contain
        # the field colour or the keyer punches a hole through it. Anything
        # botanical goes on blue. Check every colour you NAME below against this.
        "field": "green",

        # WHAT IS DRAWN — the still picture, before anything moves. Describe the
        # object, not the scene: no floor, no table, no room. Say where things
        # sit relative to each other, because that is what gets lost first.
        "draws": """
        a single large round cell with a clear nucleus, drawn as a simple bold
        textbook cell""",

        # WHAT MOVES — one continuous change that starts and finishes inside the
        # clip. Say what it ends as. Avoid asking for a specific number of
        # anything; if a count matters, this topic belongs in Manim.
        "moves": """
        the cell divides unequally: it pinches on one side and buds off a much
        smaller cell that stays attached at the edge while the main cell stays
        large""",

        # BANS specific to this topic — the wrong picture a generator reaches
        # for. General bans (text, labels, borders, cameras, floors, narration)
        # are already applied to every brief; do not repeat them here.
        "bans": """
        an equal division, four cells of the same size, the large cell shrinking,
        a follicle, an ovary""",

        # CHECKS — what must be TRUE of the finished clip, each phrased so it can
        # be confirmed or denied from a single still frame. This is the part no
        # tool can do for you, and the part that catches a confidently wrong clip.
        "checks": [
            "every division is UNEQUAL — one large cell and one much smaller one",
            "the large cell stays large throughout",
        ],

        # Optional. Anything the next person needs to know: attempts made,
        # wording that failed, a reference the drawing must match.
        "notes": """""",
    },

}
