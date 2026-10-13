import unittest

from flow.listening.benchmark import compare_analysis_to_score


class ScoreBenchmarkTests(unittest.TestCase):
    def test_matches_pitch_class_groups_and_keeps_attack_counts_cautious(self):
        reference = {
            "id": "test.motif",
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
        self.assertIn("Whole-mix onset counts cannot confirm repeated attacks in the melody part.",
                      result["interpretation_limits"])


if __name__ == "__main__":
    unittest.main()
