import json
import unittest
from dataclasses import replace

from flow.composer import beethoven_opening_recipe
from flow.knowledge.models import FocusSpan, MelodyPresence, MusicalEvent, Recipe
from flow.listening import beat_interval_windows, candidate_onset_gaps, cluster_onsets


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

    def test_recipe_can_foreground_rhythm_section_with_no_melody(self):
        recipe = Recipe(
            roles=("bass", "percussion"),
            events=(),
            invariants=(),
            transformations=(),
            focus_plan=(
                FocusSpan(
                    start_beat=16,
                    duration_beats=8,
                    foreground_roles=("bass", "percussion"),
                    melody_presence=MelodyPresence.ABSENT,
                ),
            ),
        )

        serialized = json.loads(
            json.dumps(replace(beethoven_opening_recipe(), recipe=recipe).to_dict())
        )

        self.assertEqual(serialized["recipe"]["focus_plan"][0]["foreground_roles"],
                         ["bass", "percussion"])
        self.assertEqual(serialized["recipe"]["focus_plan"][0]["melody_presence"],
                         "absent")

    def test_focus_plan_rejects_unknown_roles_and_overlapping_spans(self):
        with self.assertRaisesRegex(ValueError, "unknown roles"):
            Recipe(
                roles=("bass",),
                events=(),
                invariants=(),
                transformations=(),
                focus_plan=(FocusSpan(0, 4, ("percussion",)),),
            )

        with self.assertRaisesRegex(ValueError, "cannot overlap"):
            Recipe(
                roles=("bass",),
                events=(),
                invariants=(),
                transformations=(),
                focus_plan=(FocusSpan(0, 4, ("bass",)), FocusSpan(3, 2, ("bass",))),
            )

    def test_event_rejects_non_positive_duration(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            MusicalEvent("lead", 0, 0)

    def test_onsets_are_clustered_without_losing_attack_count(self):
        clusters = cluster_onsets([1.00, 1.03, 1.20, 2.00], merge_within_seconds=0.05)
        self.assertEqual([cluster.event_count for cluster in clusters], [2, 1, 1])
        self.assertAlmostEqual(clusters[0].center_seconds, 1.015)

    def test_long_inter_onset_gaps_are_candidates(self):
        clusters = cluster_onsets([0.0, 0.2, 0.4, 2.0, 2.2])
        gaps = candidate_onset_gaps(clusters)
        self.assertEqual(len(gaps), 1)
        self.assertAlmostEqual(gaps[0]["duration_seconds"], 1.6)

    def test_beat_windows_retain_large_intervals_as_evidence(self):
        beats = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 5.5, 6, 6.5]
        windows = beat_interval_windows(beats, beats_per_window=8)
        self.assertEqual(len(windows), 2)
        self.assertGreater(windows[0]["interval_spread_seconds"], 1.0)


if __name__ == "__main__":
    unittest.main()

