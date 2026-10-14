import tempfile
import unittest
import wave
from array import array
from pathlib import Path

from flow.composer import render_wav, rhythm_section_feature_recipe


class AudioRenderTests(unittest.TestCase):
    def test_renders_deterministic_wav_and_keeps_rhythm_active_during_melody_rest(self):
        with tempfile.TemporaryDirectory() as directory:
            first_path = Path(directory) / "preview.wav"
            second_path = Path(directory) / "preview-again.wav"
            notes = render_wav(
                rhythm_section_feature_recipe(), first_path, tempo_bpm=120, sample_rate=8000
            )
            render_wav(
                rhythm_section_feature_recipe(), second_path, tempo_bpm=120, sample_rate=8000
            )

            self.assertEqual(first_path.read_bytes(), second_path.read_bytes())
            with wave.open(str(first_path), "rb") as rendered:
                self.assertEqual(rendered.getnchannels(), 1)
                self.assertEqual(rendered.getsampwidth(), 2)
                self.assertEqual(rendered.getframerate(), 8000)
                frames = array("h", rendered.readframes(rendered.getnframes()))

        self.assertEqual(len(notes), 28)
        # At 120 BPM, the melody ends at four seconds; bass and drums continue to eight.
        during_melody = frames[3 * 8000 : 4 * 8000]
        during_rhythm_handoff = frames[5 * 8000 : 6 * 8000]
        self.assertTrue(any(during_melody))
        self.assertTrue(any(during_rhythm_handoff))
        self.assertEqual(len(frames), 8 * 8000 + 2000)


if __name__ == "__main__":
    unittest.main()
