import json
import unittest

from flow.composer import beethoven_opening_recipe
from flow.knowledge.models import MusicalEvent, Recipe


class KnowledgeModelTests(unittest.TestCase):
    def test_beethoven_seed_is_serializable_and_structurally_relative(self):
        entry = beethoven_opening_recipe()
        data = json.loads(json.dumps(entry.to_dict()))

        self.assertEqual(data["schema_version"], "1.0")
        self.assertEqual(data["status"], "proposed")
        self.assertEqual(len(data["recipe"]["events"]), 8)
        self.assertEqual(data["recipe"]["events"][0]["scale_degree"], 3)
        self.assertGreater(
            data["recipe"]["events"][3]["duration_beats"],
            data["recipe"]["events"][0]["duration_beats"],
        )

    def test_recipe_rejects_unknown_role(self):
        with self.assertRaisesRegex(ValueError, "unknown roles"):
            Recipe(
                roles=("lead",),
                events=(MusicalEvent("bass", 0, 1),),
                invariants=(),
                transformations=(),
            )

    def test_event_rejects_non_positive_duration(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            MusicalEvent("lead", 0, 0)


if __name__ == "__main__":
    unittest.main()

