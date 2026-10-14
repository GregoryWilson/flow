"""Compare audio evidence with a score reference without mixing evidence lanes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


PITCH_CLASS_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def _reference_groups(reference: Mapping[str, Any]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for event in reference.get("events", []):
        if event.get("event_type", "note") != "note":
            continue
        midi_note = int(event["midi_note"])
        pitch_class = midi_note % 12
        if groups and groups[-1]["pitch_class"] == pitch_class:
            groups[-1]["attack_count"] += 1
            groups[-1]["end_beat"] = float(event["beat"]) + float(event["duration_beats"])
        else:
            groups.append(
                {
                    "pitch_class": pitch_class,
                    "pitch_class_name": PITCH_CLASS_NAMES[pitch_class],
                    "midi_note": midi_note,
                    "pitch": event.get("pitch", PITCH_CLASS_NAMES[pitch_class]),
                    "attack_count": 1,
                    "start_beat": float(event["beat"]),
                    "end_beat": float(event["beat"]) + float(event["duration_beats"]),
                }
            )
    return groups


def _observed_runs(
    windows: Sequence[Mapping[str, Any]],
    reference_groups: Sequence[Mapping[str, Any]],
    minimum_strength: float,
    onset_clusters: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    target_classes = {int(group["pitch_class"]) for group in reference_groups}
    runs: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for window in windows:
        strengths: dict[int, float] = {}
        exact_strengths: dict[int, float] = {}
        for candidate in window.get("candidates", []):
            midi_note = int(candidate["midi_note"])
            pitch_class = midi_note % 12
            if pitch_class not in target_classes:
                continue
            strength = float(candidate["relative_strength"])
            strengths[pitch_class] = max(strengths.get(pitch_class, 0.0), strength)
            exact_strengths[midi_note] = max(exact_strengths.get(midi_note, 0.0), strength)

        pitch_class = max(strengths, key=strengths.get) if strengths else None
        strength = strengths.get(pitch_class, 0.0) if pitch_class is not None else 0.0
        if strength < minimum_strength:
            pitch_class = None

        if pitch_class is None:
            current = None
            continue

        start = float(window["start_seconds"])
        end = float(window["end_seconds"])
        if current is None or current["pitch_class"] != pitch_class:
            current = {
                "pitch_class": pitch_class,
                "pitch_class_name": PITCH_CLASS_NAMES[pitch_class],
                "start_seconds": start,
                "end_seconds": end,
                "peak_pitch_class_strength": strength,
                "peak_exact_pitch_strength": 0.0,
            }
            runs.append(current)
        else:
            current["end_seconds"] = end
            current["peak_pitch_class_strength"] = max(
                current["peak_pitch_class_strength"], strength
            )

        expected_midi = next(
            int(group["midi_note"])
            for group in reference_groups
            if int(group["pitch_class"]) == pitch_class
        )
        current["peak_exact_pitch_strength"] = max(
            current["peak_exact_pitch_strength"], exact_strengths.get(expected_midi, 0.0)
        )

    for run in runs:
        run["onset_cluster_count"] = sum(
            1
            for cluster in onset_clusters
            if run["start_seconds"] <= float(cluster["center_seconds"]) < run["end_seconds"]
        )
    return runs


def _pitch_label(midi_note: int) -> str:
    pitch_class = midi_note % 12
    octave = midi_note // 12 - 1
    return f"{PITCH_CLASS_NAMES[pitch_class]}{octave}"


def _register_evidence_for_run(
    windows: Sequence[Mapping[str, Any]], run: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Summarize exact MIDI candidates supporting a pitch-class run by octave."""
    pitch_class = int(run["pitch_class"])
    overlapping = [
        window
        for window in windows
        if float(window["start_seconds"]) < float(run["end_seconds"])
        and float(window["end_seconds"]) > float(run["start_seconds"])
    ]
    strengths_by_midi: dict[int, list[float]] = {}
    for window in overlapping:
        candidates = {
            int(candidate["midi_note"]): float(candidate["relative_strength"])
            for candidate in window.get("candidates", [])
            if int(candidate["midi_note"]) % 12 == pitch_class
        }
        for midi_note in set(strengths_by_midi) | set(candidates):
            strengths_by_midi.setdefault(midi_note, []).append(candidates.get(midi_note, 0.0))

    return [
        {
            "midi_note": midi_note,
            "pitch": _pitch_label(midi_note),
            "candidate_window_count": sum(value > 0 for value in strengths),
            "overlapping_window_count": len(overlapping),
            "peak_relative_strength": max(strengths, default=0.0),
            "mean_relative_strength": (
                sum(strengths) / len(overlapping) if overlapping else 0.0
            ),
        }
        for midi_note, strengths in sorted(strengths_by_midi.items())
    ]


def _score_beat_alignment(
    reference_groups: Sequence[Mapping[str, Any]], comparison: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Build a piecewise beat-to-time map from matched pitch-run boundaries."""
    anchors = [
        {
            "pitch": row["expected_pitch"],
            "score_beat": float(group["start_beat"]),
            "audio_seconds": float(row["observed_start_seconds"]),
        }
        for group, row in zip(reference_groups, comparison, strict=True)
        if row["observed_start_seconds"] is not None
    ]
    intervals = []
    for left, right in zip(anchors, anchors[1:]):
        beat_delta = right["score_beat"] - left["score_beat"]
        second_delta = right["audio_seconds"] - left["audio_seconds"]
        if beat_delta <= 0 or second_delta <= 0:
            continue
        seconds_per_beat = second_delta / beat_delta
        intervals.append(
            {
                "from_pitch": left["pitch"],
                "to_pitch": right["pitch"],
                "score_beats": beat_delta,
                "audio_seconds": second_delta,
                "observed_seconds_per_score_beat": seconds_per_beat,
                "implied_bpm": 60.0 / seconds_per_beat,
            }
        )
    return {
        "method": "piecewise interpolation between matched pitch-run boundaries",
        "anchors": anchors,
        "intervals": intervals,
        "limitations": [
            "Pitch-run boundaries are coarse anchors, not detected note attacks.",
            "Fermatas and expressive timing can stretch intervals; implied BPM is local only.",
        ],
    }


def _time_at_score_beat(
    beat: float, anchors: Sequence[Mapping[str, Any]]
) -> float | None:
    """Interpolate only within measured anchor coverage; do not extrapolate."""
    for left, right in zip(anchors, anchors[1:]):
        left_beat = float(left["score_beat"])
        right_beat = float(right["score_beat"])
        if left_beat <= beat <= right_beat and right_beat > left_beat:
            left_time = float(left["audio_seconds"])
            right_time = float(right["audio_seconds"])
            return left_time + (beat - left_beat) * (right_time - left_time) / (
                right_beat - left_beat
            )
    if anchors and beat == float(anchors[-1]["score_beat"]):
        return float(anchors[-1]["audio_seconds"])
    return None


def _score_attack_alignment(
    reference: Mapping[str, Any],
    analysis: Mapping[str, Any],
    anchors: Sequence[Mapping[str, Any]],
    minimum_strength: float,
    onset_tolerance_seconds: float,
) -> dict[str, Any]:
    """Compare each score note attack with nearby whole-mix onset and pitch evidence."""
    clusters = list(analysis.get("onset_clusters", []))
    windows = list(analysis.get("pitch_evidence_windows", []))
    used_cluster_indexes: set[int] = set()
    attacks: list[dict[str, Any]] = []

    for event in reference.get("events", []):
        if event.get("event_type", "note") != "note":
            continue
        midi_note = int(event["midi_note"])
        pitch_class = midi_note % 12
        beat = float(event["beat"])
        predicted = _time_at_score_beat(beat, anchors)

        nearest_index: int | None = None
        nearest_delta: float | None = None
        if predicted is not None:
            for index, cluster in enumerate(clusters):
                if index in used_cluster_indexes:
                    continue
                delta = float(cluster["center_seconds"]) - predicted
                if nearest_delta is None or abs(delta) < abs(nearest_delta):
                    nearest_index = index
                    nearest_delta = delta

        within_tolerance = (
            nearest_delta is not None
            and abs(nearest_delta) <= onset_tolerance_seconds
        )
        matched_cluster = (
            clusters[nearest_index]
            if within_tolerance and nearest_index is not None
            else None
        )
        if matched_cluster is not None and nearest_index is not None:
            used_cluster_indexes.add(nearest_index)

        evidence_center = (
            float(matched_cluster["center_seconds"])
            if matched_cluster is not None
            else predicted
        )
        nearby_windows = (
            [
                window
                for window in windows
                if float(window["end_seconds"]) >= evidence_center - 0.1
                and float(window["start_seconds"]) <= evidence_center + 0.15
            ]
            if evidence_center is not None
            else []
        )
        candidate_strengths: dict[int, list[float]] = {}
        for window in nearby_windows:
            for candidate in window.get("candidates", []):
                candidate_midi = int(candidate["midi_note"])
                if candidate_midi % 12 == pitch_class:
                    candidate_strengths.setdefault(candidate_midi, []).append(
                        float(candidate["relative_strength"])
                    )
        pitch_class_peak = max(
            (max(strengths) for strengths in candidate_strengths.values()), default=0.0
        )
        expected_pitch_peak = max(candidate_strengths.get(midi_note, []), default=0.0)
        pitch_supported = pitch_class_peak >= minimum_strength

        attacks.append(
            {
                "score_beat": beat,
                "expected_pitch": event.get("pitch", _pitch_label(midi_note)),
                "expected_midi_note": midi_note,
                "predicted_audio_seconds": predicted,
                "nearest_onset_seconds": (
                    float(clusters[nearest_index]["center_seconds"])
                    if nearest_index is not None
                    else None
                ),
                "nearest_onset_delta_seconds": (
                    nearest_delta if nearest_delta is not None else None
                ),
                "onset_within_tolerance": within_tolerance,
                "whole_mix_event_count": (
                    int(matched_cluster.get("event_count", 1))
                    if matched_cluster is not None
                    else None
                ),
                "nearby_pitch_window_count": len(nearby_windows),
                "expected_midi_peak_strength": expected_pitch_peak,
                "pitch_class_peak_strength": pitch_class_peak,
                "pitch_class_supported": pitch_supported,
                "register_evidence": [
                    {
                        "midi_note": candidate_midi,
                        "pitch": _pitch_label(candidate_midi),
                        "peak_relative_strength": max(strengths),
                        "candidate_window_count": len(strengths),
                    }
                    for candidate_midi, strengths in sorted(candidate_strengths.items())
                ],
            }
        )

    return {
        "method": "piecewise score-beat interpolation with nearest unused onset and local pitch windows",
        "onset_tolerance_seconds": onset_tolerance_seconds,
        "minimum_pitch_strength": minimum_strength,
        "attacks": attacks,
        "limitations": [
            "Onset clusters summarize the whole mix and may represent several instruments.",
            "Pitch salience near an onset is supporting evidence, not proof of its source.",
            "Pitch windows overlap in time and can smear attacks across neighboring notes.",
            "Attacks outside measured score-beat anchors have no predicted time.",
        ],
    }


def compare_analysis_to_score(
    analysis: Mapping[str, Any],
    reference: Mapping[str, Any],
    *,
    minimum_strength: float = 0.3,
    onset_tolerance_seconds: float = 0.2,
) -> dict[str, Any]:
    """Find an ordered pitch-class passage in score-informed pitch evidence.

    This is a review aid, not a note-recognition accuracy score. CQT salience is
    relative to each window, and onset clusters cover the whole mix.
    """
    if not 0 <= minimum_strength <= 1:
        raise ValueError("minimum_strength must be between 0 and 1")
    if onset_tolerance_seconds < 0:
        raise ValueError("onset_tolerance_seconds cannot be negative")
    reference_groups = _reference_groups(reference)
    if not reference_groups:
        raise ValueError("score reference contains no note events")

    runs = _observed_runs(
        analysis.get("pitch_evidence_windows", []),
        reference_groups,
        minimum_strength,
        analysis.get("onset_clusters", []),
    )
    expected = [int(group["pitch_class"]) for group in reference_groups]
    matching_paths = [
        runs[index : index + len(expected)]
        for index in range(max(0, len(runs) - len(expected) + 1))
        if [int(run["pitch_class"]) for run in runs[index : index + len(expected)]] == expected
    ]
    matched = max(
        matching_paths,
        key=lambda path: sum(float(run["peak_pitch_class_strength"]) for run in path),
        default=[],
    )

    comparison: list[dict[str, Any]] = []
    for index, group in enumerate(reference_groups):
        matched_run = matched[index] if matched else None
        comparison.append(
            {
                "expected_pitch": group["pitch"],
                "expected_pitch_class": group["pitch_class_name"],
                "expected_attack_count": group["attack_count"],
                "score_start_beat": group["start_beat"],
                "score_end_beat": group["end_beat"],
                "observed_start_seconds": matched_run["start_seconds"] if matched_run else None,
                "observed_end_seconds": matched_run["end_seconds"] if matched_run else None,
                "pitch_class_peak_strength": (
                    matched_run["peak_pitch_class_strength"] if matched_run else None
                ),
                "exact_pitch_peak_strength": (
                    matched_run["peak_exact_pitch_strength"] if matched_run else None
                ),
                "whole_mix_onset_cluster_count": (
                    matched_run["onset_cluster_count"] if matched_run else None
                ),
                "register_evidence": (
                    _register_evidence_for_run(
                        analysis.get("pitch_evidence_windows", []), matched_run
                    )
                    if matched_run
                    else []
                ),
            }
        )

    beat_alignment = _score_beat_alignment(reference_groups, comparison)
    attack_alignment = _score_attack_alignment(
        reference,
        analysis,
        beat_alignment["anchors"],
        minimum_strength,
        onset_tolerance_seconds,
    )
    return {
        "reference_id": reference.get("id"),
        "analyzer": analysis.get("analyzer"),
        "minimum_relative_strength": minimum_strength,
        "ordered_pitch_class_sequence_found": bool(matched),
        "expected_pitch_class_sequence": [group["pitch_class_name"] for group in reference_groups],
        "comparison": comparison,
        "score_beat_alignment": beat_alignment,
        "score_attack_alignment": attack_alignment,
        "score_part_activity": reference.get("part_activity"),
        "observed_runs": runs,
        "interpretation_limits": [
            "Relative strength is normalized per window; it is not probability.",
            "Pitch-class matches may come from accompaniment or harmonics, not melody.",
            "Register candidates are whole-mix salience; octave matches may be harmonics.",
            "Whole-mix onset counts cannot confirm repeated attacks in the melody part.",
            "Attack alignment is a local audio-evidence comparison, not melody transcription.",
        ],
    }
