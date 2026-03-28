import json
import os
from dataclasses import dataclass

from openai import OpenAI

from baseline_inference import LLMRunnerConfig, run_all_tasks


@dataclass(frozen=True)
class InferenceConfig:
    api_base_url: str
    model_name: str
    hf_token: str


def load_inference_config() -> InferenceConfig:
    api_base_url = os.environ.get("API_BASE_URL")
    model_name = os.environ.get("MODEL_NAME")
    hf_token = os.environ.get("HF_TOKEN")

    missing = [
        name
        for name, value in (
            ("API_BASE_URL", api_base_url),
            ("MODEL_NAME", model_name),
            ("HF_TOKEN", hf_token),
        )
        if not value
    ]
    if missing:
        missing_str = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variable(s): {missing_str}")

    return InferenceConfig(
        api_base_url=api_base_url,
        model_name=model_name,
        hf_token=hf_token,
    )


def build_submission_runner(config: InferenceConfig) -> LLMRunnerConfig:
    client = OpenAI(base_url=config.api_base_url, api_key=config.hf_token)
    return LLMRunnerConfig(client=client, model_name=config.model_name)


def main() -> None:
    config = load_inference_config()
    runner = build_submission_runner(config)
    result = run_all_tasks(runner=runner, model_name=config.model_name)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
