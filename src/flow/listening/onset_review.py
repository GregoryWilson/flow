"""Pair whole-mix onset clusters with nearby, timestamped pitch evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def inspect_onset_pitch_evidence(
    analysis: Mapping[str, Any],
    *,
    before_seconds: float = 0.1,
    after_seconds: float = 0.3,
) -> dict[str, Any]:
    """Attach nearby pitch-evidence windows to each detected onset cluster.

    This is a review aid. It does not claim that a pitch candidate caused an
    onset, or that either one belongs to a particular instrument or voice.
    """
    if before_seconds < 0:
        raise ValueError("before_seconds cannot be negative")
    if after_seconds < 0:
        raise ValueError("after_seconds cannot be negative")

    clusters = list(analysis.get("onset_clusters", []))
    if not clusters:
        clusters = [
            {
                "start_seconds": float(onset),
                "end_seconds": float(onset),
                "center_seconds": float(onset),
                "event_count": 1,
            }
            for onset in analysis.get("onset_seconds", [])
        ]

    pitch_windows = analysis.get("pitch_evidence_windows", [])
    reviewed_onsets: list[dict[str, Any]] = []
    for index, cluster in enumerate(clusters):
        center = float(cluster["center_seconds"])
        window_start = float(cluster.get("start_seconds", center)) - before_seconds
        window_end = float(cluster.get("end_seconds", center)) + after_seconds
        nearby_windows = [
            {
                "start_seconds": float(window["start_seconds"]),
                "end_seconds": float(window["end_seconds"]),
                "offset_from_onset_center_seconds": (
                    (float(window["start_seconds"]) + float(window["end_seconds"])) / 2
                    - center
                ),
                "candidates": [
                    {
                        "midi_note": int(candidate["midi_note"]),
                        "note_name": candidate.get("note_name"),
                        "relative_strength": float(candidate["relative_strength"]),
                    }
                    for candidate in window.get("candidates", [])
                ],
            }
            for window in pitch_windows
            if float(window["end_seconds"]) >= window_start
            and float(window["start_seconds"]) <= window_end
        ]
        reviewed_onsets.append(
            {
                "onset_index": index,
                "start_seconds": float(cluster.get("start_seconds", center)),
                "end_seconds": float(cluster.get("end_seconds", center)),
                "center_seconds": center,
                "whole_mix_event_count": int(cluster.get("event_count", 1)),
                "pitch_evidence_windows": nearby_windows,
            }
        )

    return {
        "analyzer": analysis.get("analyzer"),
        "before_seconds": before_seconds,
        "after_seconds": after_seconds,
        "onset_count": len(reviewed_onsets),
        "onsets": reviewed_onsets,
        "interpretation_limits": [
            "Onset clusters summarize the whole mix and are not melody note attacks.",
            "Nearby pitch candidates are not assigned to the onset source or an instrument.",
            "Relative strength is normalized within each pitch-evidence window; it is not probability.",
            "Pitch windows may straddle an onset and can include sound before or after it.",
        ],
    }
