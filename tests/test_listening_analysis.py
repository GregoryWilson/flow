import unittest

from flow.listening.analyze import (
    strongest_pitch_candidates,
)


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

if __name__ == "__main__":
    unittest.main()
