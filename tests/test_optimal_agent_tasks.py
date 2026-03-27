import unittest

from tasks.easy import MAX_STEPS as EASY_MAX_STEPS
from tasks.easy import run_task as run_easy
from tasks.hard import MAX_STEPS as HARD_MAX_STEPS
from tasks.hard import run_task as run_hard
from tasks.medium import MAX_STEPS as MEDIUM_MAX_STEPS
from tasks.medium import run_task as run_medium


class OptimalAgentTaskTests(unittest.TestCase):
    def test_easy_task_is_perfect_and_within_budget(self):
        result = run_easy()
        self.assertEqual(result["score"], 1.0)
        self.assertLessEqual(result["steps"], EASY_MAX_STEPS)

    def test_medium_task_is_perfect_and_within_budget(self):
        result = run_medium()
        self.assertEqual(result["score"], 1.0)
        self.assertLessEqual(result["steps"], MEDIUM_MAX_STEPS)

    def test_hard_task_is_perfect_and_within_budget(self):
        result = run_hard()
        self.assertEqual(result["score"], 1.0)
        self.assertLessEqual(result["steps"], HARD_MAX_STEPS)


if __name__ == "__main__":
    unittest.main()
