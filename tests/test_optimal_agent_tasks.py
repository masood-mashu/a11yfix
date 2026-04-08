import unittest

from reproducibility_report import build_reproducibility_report
from tasks.easy import MAX_STEPS as EASY_MAX_STEPS
from tasks.easy import get_easy_elements
from tasks.easy import run_task as run_easy
from tasks.hard import MAX_STEPS as HARD_MAX_STEPS
from tasks.hard import get_hard_elements
from tasks.hard import run_task as run_hard
from tasks.medium import MAX_STEPS as MEDIUM_MAX_STEPS
from tasks.medium import get_medium_elements
from tasks.medium import run_task as run_medium


class OptimalAgentTaskTests(unittest.TestCase):
    def test_easy_task_is_perfect_and_within_budget(self):
        result = run_easy()
        self.assertGreater(result["score"], 0.0)
        self.assertLess(result["score"], 1.0)
        self.assertAlmostEqual(result["score"], 0.999, places=3)
        self.assertLessEqual(result["steps"], EASY_MAX_STEPS)

    def test_medium_task_is_perfect_and_within_budget(self):
        result = run_medium()
        self.assertGreater(result["score"], 0.0)
        self.assertLess(result["score"], 1.0)
        self.assertAlmostEqual(result["score"], 0.999, places=3)
        self.assertLessEqual(result["steps"], MEDIUM_MAX_STEPS)

    def test_hard_task_is_perfect_and_within_budget(self):
        result = run_hard()
        self.assertGreater(result["score"], 0.0)
        self.assertLess(result["score"], 1.0)
        self.assertAlmostEqual(result["score"], 0.999, places=3)
        self.assertLessEqual(result["steps"], HARD_MAX_STEPS)

    def test_seeded_task_variants_are_deterministic_per_seed(self):
        self.assertEqual(get_easy_elements(seed=7), get_easy_elements(seed=7))
        self.assertEqual(get_medium_elements(seed=7), get_medium_elements(seed=7))
        self.assertEqual(get_hard_elements(seed=7), get_hard_elements(seed=7))

    def test_seeded_task_variants_can_change_across_seeds(self):
        self.assertNotEqual(get_easy_elements(seed=1), get_easy_elements(seed=2))
        self.assertNotEqual(get_medium_elements(seed=1), get_medium_elements(seed=2))
        self.assertNotEqual(get_hard_elements(seed=1), get_hard_elements(seed=2))

    def test_reproducibility_report_confirms_deterministic_baseline(self):
        report = build_reproducibility_report(num_runs=3, seed_samples=(0, 1))

        self.assertTrue(report["baseline_deterministic"])
        self.assertAlmostEqual(report["baseline_summary"]["easy"], 0.999, places=3)
        self.assertAlmostEqual(report["baseline_summary"]["medium"], 0.999, places=3)
        self.assertAlmostEqual(report["baseline_summary"]["hard"], 0.999, places=3)
        self.assertTrue(report["seeded_variants_distinct"]["easy"])
        self.assertTrue(report["seeded_variants_distinct"]["medium"])
        self.assertTrue(report["seeded_variants_distinct"]["hard"])


if __name__ == "__main__":
    unittest.main()
