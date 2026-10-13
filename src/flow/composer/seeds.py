"""Score-informed benchmark recipes.

These references are isolated from audio-only analysis to prevent benchmark
knowledge from leaking into listening measurements.
"""

from flow.knowledge.models import KnowledgeEntry, MusicalEvent, Recipe, Status


def beethoven_opening_recipe() -> KnowledgeEntry:
    """Return an intentionally relative representation of the opening gesture.

    The invariant is the short-short-short-long rhythmic identity followed by
    continuation at a different pitch level. Exact score encoding will be
    added as a separately reviewed reference fixture.
    """

    events = (
        MusicalEvent("ensemble", 0.0, 0.5, scale_degree=3, tags=("short", "accent")),
        MusicalEvent("ensemble", 0.5, 0.5, scale_degree=3, tags=("short", "accent")),
        MusicalEvent("ensemble", 1.0, 0.5, scale_degree=3, tags=("short", "accent")),
        MusicalEvent("ensemble", 1.5, 2.0, scale_degree=1, tags=("long", "fermata-like")),
        MusicalEvent("ensemble", 4.0, 0.5, scale_degree=2, tags=("short", "accent")),
        MusicalEvent("ensemble", 4.5, 0.5, scale_degree=2, tags=("short", "accent")),
        MusicalEvent("ensemble", 5.0, 0.5, scale_degree=2, tags=("short", "accent")),
        MusicalEvent("ensemble", 5.5, 2.0, scale_degree=7, tags=("long", "fermata-like")),
    )
    return KnowledgeEntry(
        id="motif.beethoven5.opening.v1",
        title="Short-short-short-long developmental cell",
        intent_description=(
            "Establish a compact, forceful identity that can remain recognizable "
            "through transposition, redistribution, fragmentation, and rhythmic development."
        ),
        recipe=Recipe(
            roles=("ensemble",),
            events=events,
            invariants=(
                "three short attacks lead to one substantially longer event",
                "the long event changes pitch relative to the repeated short attacks",
            ),
            transformations=(
                "transpose while preserving relative contour",
                "redistribute attacks among performer roles",
                "augment or diminish durations proportionally",
                "fragment the first three attacks and answer them later",
                "place a new harmony or rhythm beneath the unchanged motif",
            ),
        ),
        status=Status.PROPOSED,
        effects=("identity", "urgency", "forward momentum"),
        requires=("clear contrast between short attacks and a long arrival",),
        alternatives=(
            "the perceptual identity may depend on articulation and dynamics as much as pitch",
        ),
        confidence=0.5,
    )

