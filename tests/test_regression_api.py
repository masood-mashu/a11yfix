import importlib
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import app


class RegressionAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def _reset(self):
        response = self.client.post("/reset")
        self.assertEqual(response.status_code, 200)

    def test_openenv_entry_point_factory_is_constructible(self):
        yaml_text = Path("openenv.yaml").read_text(encoding="utf-8")

        entry_point = None
        for line in yaml_text.splitlines():
            if line.strip().startswith("entry_point:"):
                entry_point = line.split(":", 1)[1].strip()
                break

        self.assertIsNotNone(entry_point, "entry_point not found in openenv.yaml")

        module_name, symbol_name = entry_point.split(":", 1)
        module = importlib.import_module(module_name)
        factory = getattr(module, symbol_name)
        env = factory()

        self.assertTrue(callable(factory))
        self.assertTrue(hasattr(env, "reset"))
        self.assertTrue(hasattr(env, "step"))

    def test_step_timeout_validation_parity_flat_vs_nested(self):
        self._reset()
        nested = self.client.post(
            "/step",
            json={"action": {"operation": "audit"}, "timeout_s": -1},
        )

        self._reset()
        flat = self.client.post(
            "/step",
            json={"operation": "audit", "timeout_s": -1},
        )

        self.assertEqual(nested.status_code, 422)
        self.assertEqual(flat.status_code, 422)
        self.assertIn("timeout_s", nested.text)
        self.assertIn("timeout_s", flat.text)

    def test_step_success_parity_with_request_fields_flat_vs_nested(self):
        self._reset()
        nested = self.client.post(
            "/step",
            json={
                "action": {"operation": "audit"},
                "timeout_s": 1,
                "request_id": "abc",
            },
        )

        self._reset()
        flat = self.client.post(
            "/step",
            json={"operation": "audit", "timeout_s": 1, "request_id": "abc"},
        )

        self.assertEqual(nested.status_code, 200)
        self.assertEqual(flat.status_code, 200)

        nested_body = nested.json()
        flat_body = flat.json()

        self.assertEqual(nested_body["done"], flat_body["done"])
        self.assertEqual(nested_body["reward"], flat_body["reward"])
        self.assertEqual(
            nested_body["observation"]["step_count"],
            flat_body["observation"]["step_count"],
        )


if __name__ == "__main__":
    unittest.main()
