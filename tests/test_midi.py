import struct
import tempfile
import unittest
from pathlib import Path

from flow.composer import realize_midi_notes, rhythm_section_feature_recipe, write_midi


class MidiExportTests(unittest.TestCase):
    def test_focus_handoff_realizes_as_melody_rest_with_rhythm_section_active(self):
        notes = realize_midi_notes(rhythm_section_feature_recipe())
        by_role = {}
        for note in notes:
            by_role.setdefault(note.role, []).append(note)

        self.assertEqual(len(by_role["melody"]), 4)
        self.assertEqual([note.midi_note for note in by_role["melody"]], [60, 63, 67, 63])
        self.assertEqual(len(by_role["bass"]), 8)
        self.assertEqual(len(by_role["percussion"]), 16)
        self.assertEqual(
            {note.midi_note for note in by_role["percussion"]},
            {36, 38, 42},
        )
        self.assertTrue(all(note.end_tick <= 8 * 480 for note in by_role["melody"]))
        self.assertTrue(
            all(note.velocity == 114 for note in by_role["bass"] if note.start_tick >= 8 * 480)
        )
        self.assertTrue(
            all(note.velocity == 82 for note in by_role["bass"] if note.start_tick < 8 * 480)
        )

    def test_writes_standard_midi_file_with_one_track_per_active_role(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "rhythm-demo.mid"
            notes = write_midi(rhythm_section_feature_recipe(), path, tempo_bpm=110)
            data = path.read_bytes()

        self.assertEqual(len(notes), 28)
        self.assertEqual(data[:4], b"MThd")
        self.assertEqual(struct.unpack(">IHHH", data[4:14]), (6, 1, 4, 480))
        offset = 14
        for _ in range(4):
            self.assertEqual(data[offset : offset + 4], b"MTrk")
            chunk_length = struct.unpack(">I", data[offset + 4 : offset + 8])[0]
            offset += 8 + chunk_length
        self.assertEqual(offset, len(data))


if __name__ == "__main__":
    unittest.main()
