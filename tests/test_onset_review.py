import unittest

from flow.listening.onset_review import inspect_onset_pitch_evidence


class OnsetPitchReviewTests(unittest.TestCase):
    def test_pairs_each_cluster_with_overlapping_pitch_windows(self):
        analysis = {
            "analyzer": "test",
            "onset_clusters": [
                {
                    "start_seconds": 0.98,
                    "end_seconds": 1.02,
                    "center_seconds": 1.0,
                    "event_count": 2,
                }
            ],
            "pitch_evidence_windows": [
                {
                    "start_seconds": 0.75,
                    "end_seconds": 1.0,
                    "candidates": [
                        {"midi_note": 67, "note_name": "G4", "relative_strength": 0.8}
                    ],
                },
                {
                    "start_seconds": 1.0,
                    "end_seconds": 1.25,
                    "candidates": [
                        {"midi_note": 63, "note_name": "D#4", "relative_strength": 1.0}
                    ],
                },
                {
                    "start_seconds": 1.25,
                    "end_seconds": 1.5,
                    "candidates": [],
                },
                {
                    "start_seconds": 1.5,
                    "end_seconds": 1.75,
                    "candidates": [],
                },
            ],
        }

        result = inspect_onset_pitch_evidence(analysis)

        self.assertEqual(result["onset_count"], 1)
        onset = result["onsets"][0]
        self.assertEqual(onset["whole_mix_event_count"], 2)
        self.assertEqual(
            [window["start_seconds"] for window in onset["pitch_evidence_windows"]],
            [0.75, 1.0, 1.25],
        )
        self.assertEqual(
            onset["pitch_evidence_windows"][1]["candidates"][0]["note_name"], "D#4"
        )

    def test_falls_back_to_raw_onsets_and_rejects_negative_windows(self):
        result = inspect_onset_pitch_evidence({"onset_seconds": [0.5]})
        self.assertEqual(result["onsets"][0]["center_seconds"], 0.5)
        self.assertEqual(result["onsets"][0]["whole_mix_event_count"], 1)

        with self.assertRaises(ValueError):
            inspect_onset_pitch_evidence({}, before_seconds=-0.1)


if __name__ == "__main__":
    unittest.main()
