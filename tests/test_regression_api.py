import importlib
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from app import CURRENT_SESSION_ID, SessionEnvManager, app, session_env_manager
from inference import build_submission_runner, load_inference_config


class RegressionAPITests(unittest.TestCase):
    def setUp(self):
        session_env_manager.reset_for_tests()
        self.client = TestClient(app, base_url="https://testserver")

    def tearDown(self):
        session_env_manager.reset_for_tests()

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

    def test_state_returns_serialized_observation_after_reset(self):
        self._reset()
        state_response = self.client.get("/state")

        self.assertEqual(state_response.status_code, 200)
        body = state_response.json()
        self.assertIn("elements", body)
        self.assertIn("score", body)
        self.assertIn("step_count", body)
        self.assertIn("max_steps", body)
        self.assertEqual(body["step_count"], 0)
        self.assertEqual(body["score"], 0.0)

    def test_exactly_one_get_state_route_is_registered_and_returns_typed_fields(self):
        state_routes = [
            route
            for route in app.router.routes
            if getattr(route, "path", None) == "/state"
            and "GET" in getattr(route, "methods", set())
        ]

        self.assertEqual(len(state_routes), 1)

        self._reset()
        response = self.client.get("/state")
        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("step_count", body)
        self.assertIn("elements", body)
        self.assertIn("score", body)
        self.assertIn("max_steps", body)

    def test_state_reflects_live_step_progress_after_audit(self):
        self._reset()
        step_response = self.client.post("/step", json={"action": {"operation": "audit"}})

        self.assertEqual(step_response.status_code, 200)
        self.assertEqual(step_response.json()["observation"]["step_count"], 1)

        state_response = self.client.get("/state")

        self.assertEqual(state_response.status_code, 200)
        self.assertEqual(state_response.json()["step_count"], 1)

    def test_session_cookie_sets_secure_and_max_age(self):
        response = self.client.post("/reset")

        self.assertEqual(response.status_code, 200)
        set_cookie = response.headers.get("set-cookie", "")
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("SameSite=lax", set_cookie)
        self.assertIn("Secure", set_cookie)
        self.assertIn("Max-Age=1800", set_cookie)

    def test_state_reflects_mutation_after_set_attribute(self):
        self._reset()
        audit_response = self.client.post("/step", json={"action": {"operation": "audit"}})
        self.assertEqual(audit_response.status_code, 200)

        mutate_response = self.client.post(
            "/step",
            json={
                "action": {
                    "operation": "set_attribute",
                    "element_id": "img1",
                    "attribute": "alt",
                    "value": "fixed",
                }
            },
        )

        self.assertEqual(mutate_response.status_code, 200)

        state_response = self.client.get("/state")
        body = state_response.json()

        self.assertEqual(state_response.status_code, 200)
        self.assertEqual(body["step_count"], 2)
        self.assertGreater(body["score"], 0.0)
        img1 = next(element for element in body["elements"] if element["id"] == "img1")
        self.assertEqual(img1["attributes"]["alt"], "fixed")

    def test_multi_client_sessions_are_isolated(self):
        client_a = TestClient(app, base_url="https://testserver")
        client_b = TestClient(app, base_url="https://testserver")

        self.assertEqual(client_a.post("/reset").status_code, 200)
        self.assertEqual(client_b.post("/reset").status_code, 200)
        self.assertEqual(
            client_a.post("/step", json={"action": {"operation": "audit"}}).status_code,
            200,
        )

        state_a = client_a.get("/state").json()
        state_b = client_b.get("/state").json()

        self.assertEqual(state_a["step_count"], 1)
        self.assertEqual(state_b["step_count"], 0)

    def test_session_manager_eviction_bounds_sessions_and_drops_progress(self):
        clock = [100.0]
        manager = SessionEnvManager(ttl_seconds=30, max_sessions=2, clock=lambda: clock[0])

        token = CURRENT_SESSION_ID.set("session-a")
        env_a = manager.get_current_env()
        env_a.reset()
        env_a.step(("audit",))
        CURRENT_SESSION_ID.reset(token)

        clock[0] = 110.0
        token = CURRENT_SESSION_ID.set("session-b")
        env_b = manager.get_current_env()
        env_b.reset()
        CURRENT_SESSION_ID.reset(token)

        self.assertEqual(manager.session_count(), 2)

        clock[0] = 120.0
        token = CURRENT_SESSION_ID.set("session-c")
        env_c = manager.get_current_env()
        env_c.reset()
        CURRENT_SESSION_ID.reset(token)

        self.assertEqual(manager.session_count(), 2)

        clock[0] = 121.0
        token = CURRENT_SESSION_ID.set("session-a")
        state_a = manager.get_current_state()
        CURRENT_SESSION_ID.reset(token)

        self.assertEqual(state_a.step_count, 0)
        self.assertEqual(manager.session_count(), 2)

    def test_session_manager_ttl_expiry_evicts_stale_session_deterministically(self):
        clock = [100.0]
        manager = SessionEnvManager(ttl_seconds=30, max_sessions=5, clock=lambda: clock[0])

        token = CURRENT_SESSION_ID.set("session-a")
        env_a = manager.get_current_env()
        env_a.reset()
        env_a.step(("audit",))
        CURRENT_SESSION_ID.reset(token)

        self.assertEqual(manager.session_count(), 1)

        clock[0] = 131.0
        token = CURRENT_SESSION_ID.set("session-a")
        state_a = manager.get_current_state()
        CURRENT_SESSION_ID.reset(token)

        self.assertEqual(state_a.step_count, 0)
        self.assertEqual(manager.session_count(), 1)

    def test_inference_uses_hf_token_contract_without_openai_api_key(self):
        with mock.patch.dict(
            "os.environ",
            {
                "API_BASE_URL": "https://router.huggingface.co/v1",
                "MODEL_NAME": "meta/test-model",
                "HF_TOKEN": "hf_test_token",
            },
            clear=True,
        ):
            config = load_inference_config()
            runner = build_submission_runner(config)

        self.assertEqual(config.api_base_url, "https://router.huggingface.co/v1")
        self.assertEqual(config.model_name, "meta/test-model")
        self.assertEqual(config.hf_token, "hf_test_token")
        self.assertEqual(runner.model_name, "meta/test-model")
        self.assertEqual(runner.client.api_key, "hf_test_token")

    def test_openenv_global_max_steps_matches_default_reset_budget(self):
        yaml_text = Path("openenv.yaml").read_text(encoding="utf-8")

        yaml_max_steps = None
        for line in yaml_text.splitlines():
            if line.startswith("max_steps:"):
                yaml_max_steps = int(line.split(":", 1)[1].strip())
                break

        self.assertIsNotNone(yaml_max_steps)

        reset_body = self.client.post("/reset").json()
        self.assertEqual(reset_body["observation"]["max_steps"], yaml_max_steps)


if __name__ == "__main__":
    unittest.main()
