"""Score-informed benchmark recipes.

These references are isolated from audio-only analysis to prevent benchmark
knowledge from leaking into listening measurements.
"""

from flow.knowledge.models import (
    EventType,
    FocusSpan,
    KnowledgeEntry,
    MelodyPresence,
    MusicalEvent,
    Recipe,
    Status,
)


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


def rhythm_section_feature_recipe() -> KnowledgeEntry:
    """Demonstrate focus moving from a melody to bass and percussion.

    The bass and percussion continue throughout. The melody has an explicit
    eight-beat rest while the focus plan makes the rhythm section foreground.
    This is a structural exercise, not an audio rendering or style template.
    """
    events = (
        MusicalEvent("melody", 0.0, 1.0, scale_degree=1, tags=("foreground",)),
        MusicalEvent("melody", 2.0, 1.0, scale_degree=3, tags=("foreground",)),
        MusicalEvent("melody", 4.0, 1.0, scale_degree=5, tags=("foreground",)),
        MusicalEvent("melody", 6.0, 1.0, scale_degree=3, tags=("foreground",)),
        MusicalEvent(
            "melody",
            8.0,
            8.0,
            event_type=EventType.REST,
            tags=("melody-dropout",),
        ),
        MusicalEvent("bass", 0.0, 2.0, scale_degree=1, tags=("pulse",)),
        MusicalEvent("bass", 2.0, 2.0, scale_degree=5, tags=("pulse",)),
        MusicalEvent("bass", 4.0, 2.0, scale_degree=6, tags=("pulse",)),
        MusicalEvent("bass", 6.0, 2.0, scale_degree=4, tags=("pulse",)),
        MusicalEvent("bass", 8.0, 2.0, scale_degree=1, tags=("featured", "pulse")),
        MusicalEvent("bass", 10.0, 2.0, scale_degree=3, tags=("featured", "pulse")),
        MusicalEvent("bass", 12.0, 2.0, scale_degree=5, tags=("featured", "pulse")),
        MusicalEvent("bass", 14.0, 2.0, scale_degree=6, tags=("featured", "pulse")),
        *(
            MusicalEvent(
                "percussion",
                float(beat),
                0.5,
                tags=(
                    ("kick",)
                    if beat % 4 == 0
                    else ("backbeat",)
                    if beat % 2 == 0
                    else ("subdivision",)
                ),
            )
            for beat in range(16)
        ),
    )
    return KnowledgeEntry(
        id="exercise.rhythm-section-feature.v1",
        title="Let the rhythm section carry the passage",
        intent_description=(
            "Move foreground attention from a short melody to the continuing bass "
            "and percussion, leaving a clear melodic gap without stopping the music."
        ),
        recipe=Recipe(
            roles=("melody", "bass", "percussion"),
            events=events,
            invariants=(
                "bass and percussion continue through the melody rest",
                "foreground focus shifts to bass and percussion as melody becomes absent",
            ),
            transformations=(
                "vary the bass contour while keeping the groove stable",
                "thin or intensify percussion during the melody rest",
                "let the melody return with a transformed phrase",
            ),
            focus_plan=(
                FocusSpan(
                    start_beat=0,
                    duration_beats=8,
                    foreground_roles=("melody",),
                    melody_presence=MelodyPresence.FOREGROUND,
                ),
                FocusSpan(
                    start_beat=8,
                    duration_beats=8,
                    foreground_roles=("bass", "percussion"),
                    melody_presence=MelodyPresence.ABSENT,
                ),
            ),
        ),
        status=Status.PROPOSED,
        effects=("contrast", "space", "groove-forward focus"),
        requires=(
            "a bass and percussion pattern that can sustain interest without lead melody",
        ),
        alternatives=(
            "the melody may be softly sustained in the background instead of fully absent",
        ),
        confidence=0.5,
    )

