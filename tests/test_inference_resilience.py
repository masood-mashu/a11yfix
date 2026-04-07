from unittest import mock
from types import SimpleNamespace

from baseline_inference import LLMRunnerConfig, run_task_with_runner
from tasks.easy import get_easy_elements


def test_llm_runner_falls_back_to_offline_behavior_when_completion_call_raises():
    fake_client = mock.Mock()
    fake_client.chat.completions.create.side_effect = RuntimeError("upstream unavailable")
    runner = LLMRunnerConfig(client=fake_client, model_name="fake-model")

    result = run_task_with_runner("easy", get_easy_elements(), 8, runner=runner)

    assert result["done"] is True
    assert result["final_score"] == 1.0
    assert result["history"][0]["action"]["operation"] == "audit"
    assert result["history"][-1]["action"]["operation"] == "done"


def test_llm_runner_falls_back_when_completion_returns_empty_choices():
    fake_client = mock.Mock()
    fake_client.chat.completions.create.return_value = SimpleNamespace(choices=[])
    runner = LLMRunnerConfig(client=fake_client, model_name="fake-model")

    result = run_task_with_runner("easy", get_easy_elements(), 8, runner=runner)

    assert result["done"] is True
    assert result["final_score"] == 1.0
    assert result["history"][-1]["action"]["operation"] == "done"


def test_llm_runner_falls_back_when_choice_message_is_missing():
    fake_client = mock.Mock()
    fake_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace()]
    )
    runner = LLMRunnerConfig(client=fake_client, model_name="fake-model")

    result = run_task_with_runner("easy", get_easy_elements(), 8, runner=runner)

    assert result["done"] is True
    assert result["final_score"] == 1.0
    assert result["history"][-1]["action"]["operation"] == "done"


def test_llm_runner_falls_back_when_choice_content_is_missing():
    fake_client = mock.Mock()
    fake_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace())]
    )
    runner = LLMRunnerConfig(client=fake_client, model_name="fake-model")

    result = run_task_with_runner("easy", get_easy_elements(), 8, runner=runner)

    assert result["done"] is True
    assert result["final_score"] == 1.0
    assert result["history"][-1]["action"]["operation"] == "done"


def test_llm_runner_falls_back_when_completion_response_shape_is_unexpected():
    fake_client = mock.Mock()
    fake_client.chat.completions.create.return_value = object()
    runner = LLMRunnerConfig(client=fake_client, model_name="fake-model")

    result = run_task_with_runner("easy", get_easy_elements(), 8, runner=runner)

    assert result["done"] is True
    assert result["final_score"] == 1.0
    assert result["history"][-1]["action"]["operation"] == "done"
