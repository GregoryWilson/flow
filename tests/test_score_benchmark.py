import unittest

from flow.listening.benchmark import (
    _score_beat_at_time,
    _score_context_at_beat,
    _score_context_summary,
    _score_time_interval_diagnostic,
    _pitch_relationships_to_score,
    compare_analysis_to_score,
)


class ScoreBenchmarkTests(unittest.TestCase):
    def test_matches_pitch_class_groups_and_keeps_attack_counts_cautious(self):
        reference = {
            "id": "test.motif",
            "part_activity": {
                "active_parts": ["Violin I", "Clarinet I"],
                "resting_parts": ["Trumpet I"],
            },
            "events": [
                {"event_type": "rest", "beat": 0, "duration_beats": 0.5},
                *[
                    {
                        "event_type": "note",
                        "beat": beat,
                        "duration_beats": 0.5,
                        "midi_note": midi,
                        "pitch": pitch,
                    }
                    for beat, midi, pitch in [
                        (0.5, 67, "G4"),
                        (1.0, 67, "G4"),
                        (1.5, 67, "G4"),
                        (2.0, 63, "D#4"),
                        (4.5, 65, "F4"),
                        (5.0, 65, "F4"),
                        (5.5, 65, "F4"),
                        (6.0, 62, "D4"),
                    ]
                ],
            ],
        }
        analysis = {
            "analyzer": "test",
            "pitch_evidence_windows": [
                {"start_seconds": start, "end_seconds": end, "candidates": [
                    {"midi_note": midi, "relative_strength": 0.9}
                ]}
                for start, end, midi in [
                    (0.0, 0.2, 67),
                    (0.2, 0.4, 67),
                    (0.4, 0.6, 63),
                    (0.6, 0.8, 65),
                    (0.8, 1.0, 62),
                ]
            ],
            "onset_clusters": [
                {"center_seconds": time} for time in (0.05, 0.15, 0.25, 0.35, 0.45)
            ],
        }

        result = compare_analysis_to_score(analysis, reference)

        self.assertTrue(result["ordered_pitch_class_sequence_found"])
        self.assertEqual(result["expected_pitch_class_sequence"], ["G", "D#", "F", "D"])
        self.assertEqual(
            [group["expected_attack_count"] for group in result["comparison"]],
            [3, 1, 3, 1],
        )
        self.assertEqual(
            result["comparison"][0]["register_evidence"],
            [
                {
                    "midi_note": 67,
                    "pitch": "G4",
                    "candidate_window_count": 2,
                    "overlapping_window_count": 2,
                    "peak_relative_strength": 0.9,
                    "mean_relative_strength": 0.9,
                }
            ],
        )
        alignment = result["score_beat_alignment"]
        self.assertEqual(len(alignment["anchors"]), 4)
        self.assertEqual(alignment["anchors"][0], {
            "pitch": "G4", "score_beat": 0.5, "audio_seconds": 0.0
        })
        self.assertEqual(len(alignment["intervals"]), 3)
        self.assertAlmostEqual(alignment["intervals"][0]["implied_bpm"], 225.0)
        self.assertEqual(result["score_part_activity"], reference["part_activity"])
        self.assertIn("not detected note attacks", alignment["limitations"][0])
        self.assertIn("Whole-mix onset counts cannot confirm repeated attacks in the melody part.",
                      result["interpretation_limits"])

    def test_reports_octave_candidates_without_claiming_separate_parts(self):
        reference = {
            "id": "test.registers",
            "events": [
                {"event_type": "note", "beat": 0, "duration_beats": 1, "midi_note": 67},
                {"event_type": "note", "beat": 1, "duration_beats": 1, "midi_note": 63},
            ],
        }
        analysis = {
            "pitch_evidence_windows": [
                {
                    "start_seconds": 0.0,
                    "end_seconds": 0.2,
                    "candidates": [
                        {"midi_note": 43, "relative_strength": 0.8},
                        {"midi_note": 55, "relative_strength": 0.7},
                        {"midi_note": 67, "relative_strength": 0.9},
                    ],
                },
                {
                    "start_seconds": 0.2,
                    "end_seconds": 0.4,
                    "candidates": [
                        {"midi_note": 43, "relative_strength": 0.4},
                        {"midi_note": 67, "relative_strength": 0.6},
                    ],
                },
                {
                    "start_seconds": 0.4,
                    "end_seconds": 0.6,
                    "candidates": [{"midi_note": 63, "relative_strength": 0.8}],
                },
            ],
            "onset_clusters": [],
        }

        result = compare_analysis_to_score(analysis, reference)

        evidence = result["comparison"][0]["register_evidence"]
        self.assertEqual([item["pitch"] for item in evidence], ["G2", "G3", "G4"])
        self.assertEqual(evidence[0]["candidate_window_count"], 2)
        self.assertEqual(evidence[0]["overlapping_window_count"], 2)
        self.assertAlmostEqual(evidence[0]["mean_relative_strength"], 0.6)
        self.assertTrue(any("harmonics" in limit for limit in result["interpretation_limits"]))

    def test_compares_score_labeled_parts_without_consuming_shared_onsets(self):
        reference = {
            "id": "test.part-lanes",
            "events": [
                {"event_type": "note", "beat": 0, "duration_beats": 1, "midi_note": 67},
                {"event_type": "note", "beat": 1, "duration_beats": 1, "midi_note": 63},
            ],
            "part_events": {
                "Violas": [
                    {"event_type": "note", "beat": 0, "duration_beats": 1, "midi_note": 55},
                    {"event_type": "note", "beat": 1, "duration_beats": 1, "midi_note": 51},
                ],
                "Cellos": [
                    {"event_type": "note", "beat": 0, "duration_beats": 1, "midi_note": 43},
                    {"event_type": "note", "beat": 1, "duration_beats": 1, "midi_note": 39},
                ],
            },
        }
        analysis = {
            "pitch_evidence_windows": [
                {
                    "start_seconds": 0.0,
                    "end_seconds": 0.2,
                    "candidates": [
                        {"midi_note": 67, "relative_strength": 0.8},
                        {"midi_note": 55, "relative_strength": 0.7},
                        {"midi_note": 43, "relative_strength": 0.6},
                    ],
                },
                {
                    "start_seconds": 0.9,
                    "end_seconds": 1.1,
                    "candidates": [
                        {"midi_note": 63, "relative_strength": 0.8},
                        {"midi_note": 51, "relative_strength": 0.7},
                        {"midi_note": 39, "relative_strength": 0.6},
                    ],
                },
            ],
            "onset_clusters": [
                {"center_seconds": 0.02, "event_count": 1},
                {"center_seconds": 1.02, "event_count": 1},
            ],
        }

        result = compare_analysis_to_score(analysis, reference)
        part_alignment = result["score_part_attack_alignment"]

        self.assertEqual(part_alignment["parts"]["Violas"]["note_event_count"], 2)
        self.assertEqual(part_alignment["parts"]["Violas"]["exact_pitch_supported_count"], 2)
        self.assertEqual(len(part_alignment["simultaneous_part_events"]), 2)
        first_stack = part_alignment["simultaneous_part_events"][0]
        self.assertEqual(first_stack["score_part_count"], 3)
        self.assertEqual(first_stack["distinct_score_pitch_count"], 3)
        self.assertTrue(
            all(note["exact_pitch_supported"] for note in first_stack["expected_pitches"])
        )
        self.assertIn("double the same note", " ".join(part_alignment["interpretation_limits"]))

    def test_aligns_individual_attacks_to_nearby_onset_and_pitch_evidence(self):
        reference = {
            "id": "test.attacks",
            "events": [
                {"event_type": "note", "beat": 0, "duration_beats": 1, "midi_note": 60},
                {"event_type": "note", "beat": 1, "duration_beats": 1, "midi_note": 62},
            ],
        }
        analysis = {
            "pitch_evidence_windows": [
                {
                    "start_seconds": 0.9,
                    "end_seconds": 1.0,
                    "candidates": [{"midi_note": 60, "relative_strength": 0.8}],
                },
                {
                    "start_seconds": 1.9,
                    "end_seconds": 2.0,
                    "candidates": [{"midi_note": 62, "relative_strength": 0.65}],
                },
                {
                    "start_seconds": 1.35,
                    "end_seconds": 1.45,
                    "candidates": [{"midi_note": 64, "relative_strength": 0.7}],
                },
            ],
            "onset_clusters": [
                {"center_seconds": 0.95, "event_count": 2},
                {"center_seconds": 1.4, "event_count": 1},
                {"center_seconds": 1.95, "event_count": 1},
            ],
        }

        result = compare_analysis_to_score(analysis, reference)
        attacks = result["score_attack_alignment"]["attacks"]

        self.assertEqual(len(attacks), 2)
        self.assertEqual([attack["expected_pitch"] for attack in attacks], ["C4", "D4"])
        self.assertAlmostEqual(attacks[0]["predicted_audio_seconds"], 0.9)
        self.assertAlmostEqual(attacks[0]["nearest_onset_seconds"], 0.95)
        self.assertAlmostEqual(attacks[0]["nearest_onset_delta_seconds"], 0.05)
        self.assertTrue(attacks[0]["onset_within_tolerance"])
        self.assertTrue(attacks[0]["pitch_class_supported"])
        self.assertEqual(attacks[0]["whole_mix_event_count"], 2)
        self.assertAlmostEqual(attacks[0]["expected_midi_peak_strength"], 0.8)
        self.assertTrue(attacks[1]["pitch_class_supported"])
        unassigned = result["score_attack_alignment"]["unassigned_onsets"]
        self.assertEqual(len(unassigned), 1)
        self.assertAlmostEqual(unassigned[0]["onset_seconds"], 1.4)
        self.assertEqual(unassigned[0]["nearby_pitch_candidates"][0]["pitch"], "E4")
        self.assertAlmostEqual(unassigned[0]["estimated_score_beat"], 0.5)
        self.assertEqual(unassigned[0]["score_contexts"][0]["type"], "note_duration")

    def test_maps_unassigned_onsets_to_score_rest_or_sustain(self):
        anchors = [
            {"score_beat": 0, "audio_seconds": 1},
            {"score_beat": 4, "audio_seconds": 5},
        ]
        events = [
            {"event_type": "note", "beat": 0, "duration_beats": 1,
             "midi_note": 60, "pitch": "C4", "role": "melody"},
            {"event_type": "rest", "beat": 1, "duration_beats": 1,
             "role": "melody"},
            {"event_type": "note", "beat": 2, "duration_beats": 2,
             "midi_note": 62, "pitch": "D4", "role": "melody"},
            {"event_type": "note", "beat": 2, "duration_beats": 2,
             "midi_note": 50, "pitch": "D3", "role": "bass"},
        ]

        self.assertEqual(_score_beat_at_time(2.5, anchors), 1.5)
        self.assertEqual(_score_context_at_beat(1.5, events)[0]["type"], "rest")
        sustain = _score_context_at_beat(3.0, events)
        self.assertEqual(sustain[0]["type"], "note_duration")
        self.assertEqual([item["pitch"] for item in sustain], ["D4", "D3"])
        relationships = _pitch_relationships_to_score(38, sustain)
        self.assertEqual([item["same_pitch_class"] for item in relationships], [True, True])
        self.assertEqual([item["octave_displacement"] for item in relationships], [-2, -1])
        self.assertEqual(
            _pitch_relationships_to_score(39, sustain)[0]["octave_displacement"], None
        )
        self.assertEqual(
            _score_context_at_beat(-0.1, events)[0]["type"], "outside_reference"
        )

    def test_includes_lower_scored_parts_in_unassigned_onset_context(self):
        melody = [
            {"event_type": "note", "beat": 0.5, "duration_beats": 1.5,
             "midi_note": 67, "pitch": "G4", "role": "upper-motif"}
        ]
        parts = {
            "Violas": [
                {"event_type": "note", "beat": 0.5, "duration_beats": 1.5,
                 "midi_note": 55, "pitch": "G3", "role": "motif-doubling"}
            ],
            "Cellos": [
                {"event_type": "note", "beat": 0.5, "duration_beats": 1.5,
                 "midi_note": 43, "pitch": "G2", "role": "motif-doubling"}
            ],
        }

        contexts = _score_context_at_beat(1.0, melody, parts)
        self.assertEqual(
            [(context.get("score_part"), context["pitch"]) for context in contexts],
            [(None, "G4"), ("Violas", "G3"), ("Cellos", "G2")],
        )
        cello_relationship = next(
            relationship
            for relationship in _pitch_relationships_to_score(43, contexts)
            if relationship.get("score_part") == "Cellos"
        )
        self.assertTrue(cello_relationship["same_pitch_class"])
        self.assertEqual(cello_relationship["octave_displacement"], 0)

    def test_summarizes_rest_across_all_modeled_score_lanes(self):
        contexts = [
            {"type": "rest", "role": "upper-motif"},
            {"type": "rest", "score_part": "Violas"},
            {"type": "rest", "score_part": "Cellos"},
        ]

        summary = _score_context_summary(contexts)

        self.assertEqual(summary["status"], "all_modeled_lanes_rest")
        self.assertEqual(summary["note_lanes"], [])
        self.assertEqual(summary["rest_lanes"], ["Cellos", "Violas", "upper-motif"])
        self.assertEqual(summary["modeled_lane_count"], 3)

    def test_marks_score_positions_inside_stretched_timing_intervals(self):
        anchors = [
            {"score_beat": 0, "audio_seconds": 0, "pitch": "C4"},
            {"score_beat": 1, "audio_seconds": 1, "pitch": "D4"},
            {"score_beat": 2, "audio_seconds": 2.5, "pitch": "E4"},
            {"score_beat": 3, "audio_seconds": 3.5, "pitch": "F4"},
        ]

        result = _score_time_interval_diagnostic(2.0, anchors)

        self.assertEqual(result["status"], "stretched")
        self.assertEqual(result["interval_start_beat"], 1.0)
        self.assertEqual(result["interval_end_beat"], 2.0)
        self.assertAlmostEqual(result["stretch_ratio"], 1.5)
        self.assertEqual(result["from_pitch"], "D4")
        self.assertEqual(result["to_pitch"], "E4")


if __name__ == "__main__":
    unittest.main()
