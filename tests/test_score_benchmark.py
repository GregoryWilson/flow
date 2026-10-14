import unittest

from flow.listening.benchmark import compare_analysis_to_score


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


if __name__ == "__main__":
    unittest.main()
