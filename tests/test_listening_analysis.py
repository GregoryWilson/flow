import unittest

from flow.listening.analyze import (
    _low_energy_intervals,
    _window_frame_ranges,
    strongest_pitch_candidates,
    spectral_timbre_features,
)

try:
    import numpy as np
except ImportError:  # audio dependencies are optional for the base install
    np = None


class ListeningAnalysisTests(unittest.TestCase):
    def test_pitch_candidates_report_note_names_and_relative_strength(self):
        # MIDI 60 is C4; MIDI 67 is G4. The quiet values between peaks should
        # not be promoted over either local maximum.
        candidates = strongest_pitch_candidates(
            [0.2, 1.0, 0.3, 0.1, 0.7, 0.2], midi_start=60, count=2
        )
        self.assertEqual([item.note_name for item in candidates], ["C#4", "E4"])
        self.assertEqual([item.relative_strength for item in candidates], [1.0, 0.7])

    def test_pitch_candidates_handle_empty_or_silent_window(self):
        self.assertEqual(strongest_pitch_candidates([]), ())
        self.assertEqual(strongest_pitch_candidates([0.0, 0.0, 0.0]), ())

    def test_low_energy_intervals_return_candidates_without_silence_claim(self):
        intervals = _low_energy_intervals(
            [0.0, 0.05, 0.5, 0.0],
            [0.0, 1.0, 2.0, 3.0, 4.0],
            threshold=0.1,
            minimum_seconds=1.0,
        )
        self.assertEqual(len(intervals), 2)
        self.assertEqual(intervals[0]["start_seconds"], 0.0)
        self.assertEqual(intervals[0]["end_seconds"], 2.0)
        self.assertEqual(intervals[1]["start_seconds"], 3.0)
        self.assertEqual(intervals[1]["end_seconds"], 4.0)

    def test_pitch_frame_windows_overlap_at_configured_hop(self):
        self.assertEqual(
            _window_frame_ranges(frame_count=11, window_frames=5, hop_frames=2),
            ((0, 5), (2, 7), (4, 9), (6, 11), (8, 11), (10, 11)),
        )

    def test_pitch_frame_windows_reject_invalid_sizes(self):
        with self.assertRaises(ValueError):
            _window_frame_ranges(frame_count=10, window_frames=0, hop_frames=2)
        with self.assertRaises(ValueError):
            _window_frame_ranges(frame_count=10, window_frames=4, hop_frames=0)

    @unittest.skipIf(np is None, "timbre feature test requires the optional NumPy dependency")
    def test_spectral_timbre_features_report_shape_and_candidate_harmonics(self):
        sample_rate = 8000
        spectrum = np.zeros(1025)
        frequencies = np.linspace(0, sample_rate / 2, spectrum.size)
        for frequency, amplitude in ((440, 1.0), (880, 0.5), (1320, 0.25)):
            spectrum[np.argmin(np.abs(frequencies - frequency))] = amplitude

        features = spectral_timbre_features(
            spectrum,
            sample_rate,
            midi_notes=[69],
            onset_strength=[0.1, 0.7, 0.2],
        )

        self.assertGreater(features["spectral_centroid_hz"], 0)
        self.assertGreater(features["rolloff_85_hz"], 0)
        self.assertAlmostEqual(sum(features["relative_band_energy"].values()), 1.0)
        self.assertAlmostEqual(features["onset_strength_peak"], 0.7)
        profile = features["candidate_harmonic_profiles"][0]
        self.assertEqual(profile["midi_note"], 69)
        self.assertGreater(profile["odd_to_even_harmonic_energy_ratio"], 1.0)
        self.assertIn(
            "acoustic descriptors, not instrument labels", spectral_timbre_features.__doc__
        )

if __name__ == "__main__":
    unittest.main()
