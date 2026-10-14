import json
import tempfile
import unittest
import wave
from pathlib import Path

from flow.cli import main
from flow.composer import rhythm_section_feature_recipe
from flow.knowledge.models import KnowledgeEntry


class RecipeIOTests(unittest.TestCase):
    def test_knowledge_entry_round_trips_through_versioned_json(self):
        original = rhythm_section_feature_recipe()
        restored = KnowledgeEntry.from_dict(json.loads(json.dumps(original.to_dict())))
        self.assertEqual(restored, original)

    def test_render_recipe_cli_reads_json_and_writes_wav(self):
        with tempfile.TemporaryDirectory() as directory:
            recipe_path = Path(directory) / "rhythm.recipe.json"
            output_path = Path(directory) / "custom-preview.wav"
            rhythm_section_feature_recipe().write_json(recipe_path)

            result = main(
                [
                    "render-recipe",
                    str(recipe_path),
                    "--out",
                    str(output_path),
                    "--tempo",
                    "110",
                    "--sample-rate",
                    "8000",
                ]
            )

            self.assertEqual(result, 0)
            with wave.open(str(output_path), "rb") as rendered:
                self.assertEqual(rendered.getframerate(), 8000)
                self.assertEqual(rendered.getnchannels(), 1)
                self.assertGreater(rendered.getnframes(), 0)


if __name__ == "__main__":
    unittest.main()
