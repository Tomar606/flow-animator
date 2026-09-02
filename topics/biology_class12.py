"""Class 12 Biology — the fourteen Long Answer animations, and where each belongs.

This file is the worked example. Every brief in it was written by hand, sent to
Flow, and graded against its own biology checks; the clips are in
`reference/biology/clip-set/` and the grading is in `docs/ROUTING.md`.

SEVEN OF THE FOURTEEN ARE MARKED `"route": "manim"` AND WILL NOT BE GENERATED.
They are kept here, with their briefs intact, because the reason each one is
routed away is the most useful thing in this file. Read `route_why` before you
write a brief of your own — the seven failures are all the same failure, and it
is the one you are most likely to repeat:

    Ask Veo for the verb. Ask Manim for the number.

A clip whose mark is a count, a ratio, an order or a direction is not a prompting
problem. Three of these were regenerated with the number named explicitly and
every alternative banned, and they still came back wrong. That is a capability
boundary, and no further wording will move it.

FIELD COLOUR IS PER TOPIC, AND IT IS A MECHANICAL CHECK
-------------------------------------------------------
The clip is keyed, so the drawing must not contain the field colour. Anything
botanical is generated on blue. Check every colour you NAME in a brief against
the field before you send it: an earlier version of BIO-C5-LA-03 asked for
yellow-with-GREEN rungs on a GREEN field, and had the model complied, half of
every such rung would have keyed out into a hole.
"""

TOPICS = {
    "BIO-C1-LA-01": {
        "title": "Anatropous ovule in section, built part by part",
        "route": "manim",
        "route_why": """
        Seven cells, eight nuclei and an anatropous orientation are all marked
        facts. Regenerated with the count named explicitly and every alternative
        banned; it still came back with 4 and 6 cells.""",
        "field": "blue",
        "draws": """
        a single angiosperm ovule seen in section, its body INVERTED so that it lies
        back alongside its own stalk: the stalk runs up beside the body and the
        small opening in the coats sits at the SAME end as the stalk, close beside
        where the stalk joins. The far end, away from the stalk, is closed. An outer
        coat and an inner coat wrap the body, and inside it a large oval sac holds
        THREE cells grouped at the opening end (one larger with two smaller beside
        it), THREE cells grouped at the far closed end, and two nuclei together in
        the middle""",
        "moves": """
        the ovule is drawn onto the empty field from the stalk inward — first the stalk
        and the outline, then the two coats sliding into place around it, then the
        inner sac fading up, and last the egg cell and the two central nuclei
        appearing inside it. Each part settles and stays. Nothing that has appeared
        moves again""",
        "bans": """
        a seed, a fruit, a whole flower, pollen grains, a pollen tube, roots,
        leaves, a second ovule""",
        "checks": [
            "the ovule has TWO coats wrapping it, not one",
            "the small opening lies at the SAME end as the stalk, beside where it joins",
            "the egg cell sits near the opening end, not at the far end",
            "there is exactly one large sac inside, containing the egg and two central nuclei",
        ],
        "notes": """
        Six attempts. The record of the other five is in reference/biology/ovule/ —
        read it before rewriting this brief""",
    },
    "BIO-C1-LA-02": {
        "title": "Microsporogenesis beside megasporogenesis — four survive, one survives",
        "route": "flow",
        "field": "blue",
        "draws": """
        two columns of cells side by side, each column a vertical chain of rounded
        cells: the left column starting from one cell, the right column also
        starting from one cell but larger""",
        "moves": """
        both parent cells divide twice. On the LEFT, the divisions produce four
        equal small cells that stay together as a tight group of four. On the RIGHT,
        the divisions produce four cells in a row of which three shrink and fade
        away and one remains, growing larger. Both sequences run at the same pace so
        they can be compared""",
        "bans": """
        more than four cells on either side, the left group losing any of its four,
        the right side keeping more than one survivor, chromosomes drawn as threads,
        a spindle""",
        "checks": [
            "the left column ends with FOUR cells, all surviving and of equal size",
            "the right column ends with exactly ONE surviving cell, the other three gone",
            "the surviving cell on the right is larger than any of the four on the left",
            "both sides start from a single cell",
        ],
    },
    "BIO-C2-LA-01": {
        "title": "Oogenesis: three unequal divisions, three polar bodies",
        "route": "flow",
        "field": "green",
        "draws": """
        a single large round cell with a clear nucleus, drawn as a simple bold
        textbook cell""",
        "moves": """
        the cell divides UNEQUALLY: it pinches on one side and buds off a very small
        cell that stays attached at the edge while the main cell stays large. That
        small cell then divides once into two even smaller cells. The large cell
        divides unequally once more, budding a third small cell. At the end one
        large cell remains with three tiny cells clustered against its edge""",
        "bans": """
        an equal division, four cells of the same size, the large cell shrinking,
        sperm, a follicle, an ovary, more than three small cells""",
        "checks": [
            "every division is UNEQUAL — one large cell and one much smaller one",
            "the large cell stays large throughout and never shrinks to match the small ones",
            "exactly three small cells remain at the end, clustered at the large cell's edge",
            "there is exactly one large cell at the end",
        ],
    },
    "BIO-C2-LA-02": {
        "title": "The uterine lining through one menstrual cycle",
        "route": "flow",
        "field": "green",
        "draws": """
        a simple cross-section of a uterus drawn as a hollow pear-shaped organ with
        a distinct inner lining layer along its inside wall,. A short tube leaves
        each upper corner and ENDS in a small rounded ovary, so the whole shape
        closes on both sides well inside the picture. The whole drawing, ovary tip
        to ovary tip, spans only the middle THIRD of the picture width, so that a
        wide margin of empty field runs down the entire left side and the entire
        right side of the frame""",
        "moves": """
        the inner lining thickens steadily and evenly, becoming rich and folded;
        then it breaks down and sheds away, thinning back to where it started, and
        begins to thicken again. The whole cycle completes once inside the clip""",
        "bans": """
        a graph, a curve, a chart, an axis, a calendar, a clock, hormone molecules,
        an embryo, a foetus, blood drops leaving the frame, a tube running off the
        side of the picture, a tube ending in nothing, any part of the drawing
        touching or crossing an edge""",
        "checks": [
            "the lining thickens first and sheds afterwards, never the reverse",
            "the lining returns to a thin state before beginning to thicken again",
            "the uterus outline itself does not change size or shape",
            "no embryo, foetus or fertilisation appears",
        ],
    },
    "BIO-C2-LA-03": {
        "title": "Spermatogenesis: four equal cells, then four tails",
        "route": "flow",
        "field": "green",
        "draws": """
        a vertical chain: one round cell at the top, and below it space for what it
        becomes""",
        "moves": """
        the top cell divides into two, those two each divide into two, giving four
        equal round cells in a row. Each of those four then RESHAPES: it elongates,
        its front condenses into a compact head, and a long thin tail grows behind
        it, until four tadpole-shaped cells sit where the round ones were, all
        pointing the same way""",
        "bans": """
        an egg, an unequal division, a polar body, fewer or more than four tails,
        cells swimming away, a testis""",
        "checks": [
            "the divisions are EQUAL — all four cells are the same size",
            "exactly four cells result, and all four go on to reshape",
            "each finished cell has a compact head and a single long tail",
            "no small cell is discarded at any point",
        ],
    },
    "BIO-C4-LA-01": {
        "title": "Incomplete dominance beside codominance",
        "route": "flow",
        "field": "blue",
        "draws": """
        two rows of simple flower heads, drawn flat and bold: a red flower and a
        white flower at the top, with empty space below them for what they produce""",
        "moves": """
        on the left the two top flowers produce a single offspring flower that is an
        even blend of the two colours, a clear pink. On the right the same two top
        flowers produce an offspring that carries BOTH colours at once as distinct
        red and white patches on the same flower, not blended. Both results appear
        at the same time so they can be compared""",
        "bans": """
        a grid, a square, a table, a Punnett square, a pedigree, more than three
        flowers per side, the pink flower having patches, the patched flower being
        pink""",
        "checks": [
            "the blended offspring is a single uniform intermediate colour with no patches",
            "the other offspring shows BOTH parent colours as distinct areas, not blended",
            "the two parent flowers are the same on both sides",
        ],
    },
    "BIO-C4-LA-02": {
        "title": "Dihybrid cross — the four groups and their sizes",
        "route": "manim",
        "route_why": """
        9:3:3:1 is the mark. Veo drew 9:4:4:4, and a corrected brief did not change
        that.""",
        "field": "blue",
        "draws": """
        two pea seeds at the top of the frame: one round and yellow, one wrinkled
        and green, drawn flat and bold, with empty space below them""",
        "moves": """
        the two seeds produce a single offspring seed that is round and yellow. That
        offspring then produces a scattered field of seeds below it in four visibly
        different groups: a large group of round yellow seeds, a much smaller group
        of round green, an equally small group of wrinkled yellow, and a very small
        group of wrinkled green. The four groups settle into four clusters whose
        relative sizes are obvious at a glance""",
        "bans": """
        a grid, a square, a Punnett square, a table, numbers, ratios written out,
        the four groups being equal in size, a group larger than the round-yellow
        one""",
        "checks": [
            "the single first-generation seed is round AND yellow",
            "the round-yellow group is clearly the largest of the four",
            "the wrinkled-green group is clearly the smallest of the four",
            "the two middle groups are roughly equal to each other and both much smaller than the round-yellow group",
            "all four combinations are present",
        ],
    },
    "BIO-C4-LA-03": {
        "title": "X-linked inheritance: affected father, carrier daughters",
        "route": "manim",
        "route_why": """
        A pedigree is a symbol grid: filled and half-filled shapes on generation
        lines. It came out right once, which is not the same as being reproducible.""",
        "field": "green",
        "draws": """
        a simple family diagram using only shapes: a square for the father and a
        circle for the mother at the top, with empty space below for children""",
        "moves": """
        the father's square fills with a solid colour marking him affected while the
        mother's circle stays plain. Lines then grow downward and four children
        appear in a row: two squares and two circles. The circles take a half-filled
        appearance and the squares stay plain, each settling in turn""",
        "bans": """
        a Punnett square, a grid, chromosomes, blood, a hospital, more than four
        children, any child's shape being fully filled""",
        "checks": [
            "the father's square is fully marked and the mother's circle is plain",
            "no son is fully marked",
            "the daughters are half-marked, not fully marked and not plain",
            "there are exactly four children",
        ],
    },
    "BIO-C5-LA-01": {
        "title": "Gel electrophoresis — bands separating by size",
        "route": "manim",
        "route_why": """
        The answer is which bands a lane shares with another lane — a relationship
        between marks, not a picture of a gel.""",
        "field": "green",
        "draws": """
        a simple upright rectangular slab with several wells along its top edge,
        drawn flat and bold like a textbook gel""",
        "moves": """
        from each well a group of short horizontal bars moves downward and spreads
        out, the smaller bars travelling further than the larger ones, until each
        lane has settled into its own distinct pattern of bars at different heights.
        Two of the lanes end with matching patterns and the others differ""",
        "bans": """
        a photograph of a real gel, a machine, a computer screen, a person, a
        pipette, numbers beside the bands, a ruler""",
        "checks": [
            "the bands travel away from the wells, never back toward them",
            "smaller bands end further from the wells than larger ones",
            "at least two lanes end with clearly different band patterns",
        ],
    },
    "BIO-C5-LA-02": {
        "title": "Hershey and Chase: the phage stays outside",
        "route": "flow",
        "field": "green",
        "draws": """
        a large rounded bacterial cell with several small angular viruses sitting on
        its outer surface, each virus drawn as a head on a short tail with fine legs
        gripping the cell""",
        "moves": """
        each virus injects its contents into the bacterium: a thread travels down
        the tail and into the cell, the virus heads emptying and going pale while
        the inside of the bacterium fills with the threads. The emptied heads then
        detach and drift slightly away, leaving the bacterium holding the threads""",
        "bans": """
        a blender, a centrifuge, a test tube, a laboratory, radioactivity symbols,
        the bacterium bursting, the viruses entering the cell whole""",
        "checks": [
            "the virus stays OUTSIDE the bacterium throughout — only its contents enter",
            "the emptied virus heads remain outside and go pale",
            "the injected material ends up inside the bacterium",
            "the bacterium does not burst",
        ],
    },
    "BIO-C5-LA-03": {
        "title": "DNA double helix turning, base pairs intact",
        "route": "manim",
        "route_why": """
        Base pairing must be A-T and G-C every time. Named as two legal colour
        pairings with every other pairing banned, it still produced yellow-with-blue
        and a fifth colour.""",
        "field": "green",
        "draws": """
        a DNA double helix standing upright: two twisting backbones in two clearly
        different colours, joined by short flat rungs between them. There are only
        TWO kinds of rung in the whole helix and no others: a RED half always
        meeting a BLUE half, and a YELLOW half always meeting a GREEN half. Red
        never meets yellow or green; blue never meets yellow or green. The two kinds
        alternate irregularly up the ladder""",
        "moves": """
        the helix turns slowly and steadily about its upright axis, one full turn
        over the clip, so the twist of the two backbones and the paired rungs
        between them are seen from every side. Nothing separates and nothing is
        added""",
        "bans": """
        the strands separating, the helix unwinding, a replication fork, a second
        helix, a single strand, the helix tilting or falling over, a rung whose two
        halves are any pairing other than red-with-blue or yellow-with-green, a rung
        of one solid colour, more than four rung colours anywhere in the helix""",
        "checks": [
            "the two backbones remain joined by rungs for the whole clip",
            "each rung is made of two halves meeting in the middle",
            "the helix turns as one piece and never separates",
            "there is exactly one helix at the end",
        ],
        "notes": """
        The rung colours are spelled out because a helix with four freely mixed rung
        colours is what came back when they were not""",
    },
    "BIO-C12-LA-01": {
        "title": "Grazing food chain above a detritus food chain",
        "route": "manim",
        "route_why": """
        Arrows must point from eaten to eater. Direction is topology, and generators
        do not respect it — the arrows reversed and the two chains crossed.""",
        "field": "green",
        "draws": """
        two horizontal chains of simple organism shapes, one above the other: the
        upper chain beginning with a plant, the lower chain beginning with a heap of
        dead leaves and fragments""",
        "moves": """
        in the upper chain, arrows grow from the plant to a small animal, then to a
        larger animal, then to a bird, each link appearing in turn. In the lower
        chain, arrows grow from the dead matter to a small soil creature, then to a
        slightly larger one, then to a bird. Both chains complete and remain on
        screen together""",
        "bans": """
        a pyramid, a grid, a table, numbers beside the organisms, a sun, a food web
        with crossing arrows, more than four links in either chain""",
        "checks": [
            "the upper chain starts with a living plant",
            "the lower chain starts with dead matter, not a living plant",
            "every arrow points from the eaten toward the eater, consistently",
            "the two chains stay separate and do not cross",
        ],
    },
    "BIO-C12-LA-02": {
        "title": "An ecological pyramid, then inverted",
        "route": "manim",
        "route_why": """
        The tiers are ordered by trophic level, and the ordering IS the concept. It
        came back inverted and scrambled.""",
        "field": "green",
        "draws": """
        a stack of horizontal bars forming a pyramid shape, widest at the bottom and
        narrowing upward, drawn flat and bold with a small organism shape resting on
        each bar""",
        "moves": """
        the pyramid builds from the bottom bar upward, each bar sliding into place
        with its organism. Once complete it INVERTS: the bars smoothly change width
        so the widest is now at the top and the narrowest at the bottom, holding the
        new shape at the end""",
        "bans": """
        numbers on the bars, a chart axis, a graph, a triangle outline with nothing
        in it, more than four levels, the bars separating from each other""",
        "checks": [
            "the first pyramid is widest at the bottom and narrows upward",
            "after inverting it is widest at the top and narrowest at the bottom",
            "the number of levels does not change when it inverts",
        ],
    },
    "BIO-C12-LA-03": {
        "title": "A pond ecosystem filling in layers",
        "route": "flow",
        "field": "blue",
        "draws": """
        a pond seen from the side: a rounded body of water with a sloped floor of
        mud, drawn flat and bold, with open water above the floor""",
        "moves": """
        the pond fills with life in layers, each appearing in turn and staying:
        rooted plants rising from the mud at the shallow edge, small floating plants
        settling on the surface, tiny drifting specks appearing through the open
        water, fish appearing mid-water and holding station, and small creatures
        settling onto the muddy floor""",
        "bans": """
        a person, a boat, a house, a sun with a face, a fishing rod, the water
        draining, a cross-section cut line, a bank of soil outside the pond""",
        "checks": [
            "rooted plants are attached to the mud, not floating free",
            "floating plants sit ON the water surface, not below it",
            "the bottom-dwelling creatures are on the mud floor",
            "fish are in the open water, not on the floor and not above the surface",
        ],
    },
}
